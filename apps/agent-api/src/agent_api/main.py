import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uuid

from agent_api.deps import get_db_session
from sgc_agent.orchestrator import AgentOrchestrator
from sgc_db.repositories.sessions import SessionRepository
from sgc_llm.router import ModelRouter
from sgc_shared.config import get_settings
from sgc_shared.types import ContextEnvelope, CustomerContext, LocationContext
from sgc_tools.registry import create_registry

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    from sgc_db.session import get_session_factory
    from sqlalchemy import text
    
    factory = get_session_factory()
    try:
        async with factory() as session:
            result = await session.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            logger.info(f"Successfully connected to the database. Database name: {db_name}")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        
    yield

app = FastAPI(
    title="SGC AI Agent API",
    version="0.1.0",
    description="Smart Garage Customer AI Agent — plug-and-play API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateSessionRequest(BaseModel):
    customer_id: str | None = None
    vehicle_id: str | None = None
    context: ContextEnvelope | None = None


class CreateSessionResponse(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: ContextEnvelope | None = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    intent: str | None = None
    source_refs: list[dict] = Field(default_factory=list)
    requires_human_review: bool = False
    model_used: str = ""


class ToolInvokeRequest(BaseModel):
    tool_name: str
    parameters: dict = Field(default_factory=dict)
    session_id: str | None = None


class ToolInvokeResponse(BaseModel):
    tool_name: str
    success: bool
    data: dict | list | None = None
    error: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sgc-agent-api"}


@app.get("/v1/models")
async def list_models():
    router = ModelRouter()
    return {"models": router.list_models()}


@app.post("/v1/sessions", response_model=CreateSessionResponse)
async def create_session(
    body: CreateSessionRequest,
    session=Depends(get_db_session),
):
    session_id = str(uuid.uuid4())
    ctx = body.context or ContextEnvelope(
        customer=CustomerContext(customer_id=body.customer_id, vehicle_id=body.vehicle_id)
    )
    repo = SessionRepository(session)
    await repo.create_conversation(
        session_id=session_id,
        customer_id=body.customer_id,
        context=ctx.model_dump(),
    )
    return CreateSessionResponse(session_id=session_id)


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    session=Depends(get_db_session),
):
    repo = SessionRepository(session)
    conv = await repo.get_conversation(body.session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")

    context = body.context or ContextEnvelope.model_validate(conv.context_snapshot or {})
    await repo.add_message(body.session_id, "user", body.message)

    registry = create_registry()
    orchestrator = AgentOrchestrator(db_session=session, registry=registry)
    result = await orchestrator.process_message(
        session_id=body.session_id,
        message=body.message,
        context=context,
    )

    await repo.add_message(
        body.session_id,
        "assistant",
        result["response"],
        source_refs=result.get("source_refs"),
    )

    for tr in result.get("tool_results", []):
        await repo.log_tool_invocation(
            body.session_id,
            tr["tool_name"],
            {"message": body.message},
            tr,
            tr.get("success", True),
        )

    return ChatResponse(
        session_id=body.session_id,
        response=result["response"],
        intent=result.get("intent"),
        source_refs=result.get("source_refs", []),
        requires_human_review=result.get("requires_human_review", False),
        model_used=result.get("model_used", ""),
    )


@app.websocket("/v1/chat/stream")
async def chat_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        session_id = data.get("session_id")
        message = data.get("message", "")

        from sgc_db.session import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            registry = create_registry()
            orchestrator = AgentOrchestrator(db_session=session, registry=registry)
            context = ContextEnvelope.model_validate(data.get("context", {}))
            result = await orchestrator.process_message(session_id, message, context)

            words = result["response"].split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                await websocket.send_json({"type": "token", "content": chunk})

            await websocket.send_json({
                "type": "done",
                "intent": result.get("intent"),
                "source_refs": result.get("source_refs", []),
            })
    except WebSocketDisconnect:
        pass
    except Exception as error:
        await websocket.send_json({"type": "error", "message": str(error)})


@app.post("/v1/tools/invoke", response_model=ToolInvokeResponse)
async def invoke_tool(
    body: ToolInvokeRequest,
    session=Depends(get_db_session),
):
    registry = create_registry()
    result = await registry.invoke(body.tool_name, session, **body.parameters)

    if body.session_id:
        repo = SessionRepository(session)
        await repo.log_tool_invocation(
            body.session_id,
            body.tool_name,
            body.parameters,
            result.model_dump(),
            result.success,
        )

    return ToolInvokeResponse(
        tool_name=result.tool_name,
        success=result.success,
        data=result.data,
        error=result.error,
    )


def run():
    import uvicorn
    uvicorn.run("agent_api.main:app", host="0.0.0.0", port=8000, reload=True)
