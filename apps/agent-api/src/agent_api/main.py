"""SGC AI Agent API — FastAPI application with MCP server lifecycle,
dual-database support, structured logging, and chat history endpoints.
"""

import asyncio
import logging
import subprocess
import sys
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text

from agent_api.deps import get_db_session, get_pikpart_db_session
from sgc_agent.mcp_client import get_mcp_client, shutdown_mcp_client
from sgc_agent.orchestrator import AgentOrchestrator
from sgc_db.repositories.sessions import SessionRepository
from sgc_db.session_dual import dispose_all_engines
from sgc_llm.router import ModelRouter
from sgc_shared.config import get_settings
from sgc_shared.logging import setup_logging
from sgc_shared.types import ContextEnvelope, CustomerContext, LocationContext, ToolResult
from sgc_tools.registry import create_registry

logger = logging.getLogger("agent.api")


# ═══════════════════════════════════════════════════════════════════════════
# MCP Server subprocess management
# ═══════════════════════════════════════════════════════════════════════════

_mcp_process: subprocess.Popen | None = None


def _start_mcp_server() -> subprocess.Popen | None:
    """Start the MCP server as a background subprocess."""
    settings = get_settings()
    try:
        env_vars = {
            "SGC_MCP_PORT": str(settings.mcp_port),
            "SGC_MCP_HOST": settings.mcp_host,
            "SG_AI_DATABASE_URL": settings.database_url,
        }
        import os
        env = {**os.environ, **env_vars}

        proc = subprocess.Popen(
            [sys.executable, "-m", "sgc_mcp.server"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info(
            "MCP server started",
            extra={"pid": proc.pid, "port": settings.mcp_port},
        )
        return proc
    except Exception as e:
        logger.error("Failed to start MCP server: %s", e, exc_info=True)
        return None


def _stop_mcp_server(proc: subprocess.Popen | None) -> None:
    """Stop the MCP server subprocess."""
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
            logger.info("MCP server stopped gracefully", extra={"pid": proc.pid})
        except subprocess.TimeoutExpired:
            proc.kill()
            logger.warning("MCP server killed after timeout", extra={"pid": proc.pid})


# ═══════════════════════════════════════════════════════════════════════════
# Application lifecycle
# ═══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mcp_process

    # ── 1. Configure logging ───────────────────────────────────────────
    setup_logging()
    logger.info("SGC AI Agent API starting up")

    # ── 2. Verify database connections ─────────────────────────────────
    settings = get_settings()

    # Check prod_pikpart (read-only)
    try:
        from sgc_db.session_dual import get_pikpart_session_factory
        factory = get_pikpart_session_factory()
        async with factory() as session:
            result = await session.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            logger.info(
                "Connected to prod_pikpart database",
                extra={"database": db_name},
            )
    except Exception as e:
        logger.error("Failed to connect to prod_pikpart: %s", e)

    # Check sgc_agent (read-write)
    try:
        from sgc_db.session_dual import get_agent_session_factory
        factory = get_agent_session_factory()
        async with factory() as session:
            result = await session.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            logger.info(
                "Connected to sgc_agent database",
                extra={"database": db_name},
            )
    except Exception as e:
        logger.error("Failed to connect to sgc_agent: %s", e)

    # ── 3. Start MCP server ────────────────────────────────────────────
    if settings.start_local_mcp_server:
        _mcp_process = _start_mcp_server()
        if _mcp_process:
            await asyncio.sleep(2)  # Give MCP server time to start

    # ── 4. Connect MCP client ──────────────────────────────────────────
    try:
        mcp_client = await get_mcp_client()
        tools = await mcp_client.list_tools()
        logger.info(
            "MCP client connected",
            extra={"tools_count": len(tools)},
        )
    except Exception as e:
        logger.warning("MCP client connection failed (will retry on first request): %s", e)

    logger.info("SGC AI Agent API ready")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────
    logger.info("SGC AI Agent API shutting down")
    await shutdown_mcp_client()
    _stop_mcp_server(_mcp_process)
    await dispose_all_engines()
    logger.info("SGC AI Agent API shutdown complete")


# ═══════════════════════════════════════════════════════════════════════════
# FastAPI app
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="SGC AI Agent API",
    version="0.2.0",
    description="Smart Garage Customer AI Agent — with MCP-powered prod_pikpart data access",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ─────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "Request processed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": elapsed,
        },
    )
    return response


# ═══════════════════════════════════════════════════════════════════════════
# Request / Response models
# ═══════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {"status": "ok", "service": "sgc-agent-api", "version": "0.2.0"}


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
    logger.info(
        "Session created",
        extra={"session_id": session_id, "customer_id": body.customer_id},
    )
    return CreateSessionResponse(session_id=session_id)


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    session=Depends(get_db_session),
):
    total_start = time.perf_counter()

    repo = SessionRepository(session)
    conv = await repo.get_conversation(body.session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")

    context = body.context or ContextEnvelope.model_validate(conv.context_snapshot or {})

    # Save user message
    await repo.add_message(body.session_id, "user", body.message)

    # Get conversation history for context
    messages = await repo.get_messages(body.session_id, limit=10)
    history = [{"role": m.role, "content": m.content} for m in messages[:-1]]  # exclude current

    # Process through orchestrator
    registry = create_registry()
    orchestrator = AgentOrchestrator(db_session=session, registry=registry)
    result = await orchestrator.process_message(
        session_id=body.session_id,
        message=body.message,
        context=context,
        history=history,
    )

    # Save assistant response
    await repo.add_message(
        body.session_id,
        "assistant",
        result["response"],
        source_refs=result.get("source_refs"),
    )

    # Log tool invocations
    for tr in result.get("tool_results", []):
        await repo.log_tool_invocation(
            body.session_id,
            tr["tool_name"],
            {"message": body.message},
            tr,
            tr.get("success", True),
        )

    # Log chat interaction for fine-tuning
    total_ms = round((time.perf_counter() - total_start) * 1000, 2)
    await repo.log_chat_interaction(
        session_id=body.session_id,
        user_message=body.message,
        agent_response=result["response"],
        detected_intent=result.get("intent"),
        tools_called=[tr["tool_name"] for tr in result.get("tool_results", [])],
        model_used=result.get("model_used"),
        response_latency_ms=total_ms,
        requires_human_review=result.get("requires_human_review", False),
        customer_id=context.customer.customer_id,
        customer_context=context.customer.model_dump(),
    )

    logger.info(
        "Chat response sent",
        extra={
            "session_id": body.session_id,
            "intent": result.get("intent"),
            "duration_ms": total_ms,
        },
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

        from sgc_db.session_dual import get_agent_session_factory
        factory = get_agent_session_factory()
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
    
    if registry.get(body.tool_name):
        result = await registry.invoke(body.tool_name, session, **body.parameters)
    else:
        try:
            mcp_client = await get_mcp_client()
            mcp_tools = await mcp_client.list_tools()
            if any(t["name"] == body.tool_name for t in mcp_tools):
                mcp_res = await mcp_client.call_tool(body.tool_name, body.parameters)
                result = ToolResult(
                    tool_name=mcp_res["tool_name"],
                    success=mcp_res["success"],
                    data=mcp_res["data"],
                    error=mcp_res["error"]
                )
            else:
                result = ToolResult(tool_name=body.tool_name, success=False, error=f"Unknown tool: {body.tool_name}")
        except Exception as e:
            logger.error("Failed to invoke MCP tool %s: %s", body.tool_name, e)
            result = ToolResult(tool_name=body.tool_name, success=False, error=f"MCP Error: {str(e)}")

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


# ═══════════════════════════════════════════════════════════════════════════
# NEW: Chat history & analytics endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/v1/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    session=Depends(get_db_session),
):
    """Get the full chat history for a session."""
    repo = SessionRepository(session)
    conv = await repo.get_conversation(session_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await repo.get_messages(session_id, limit=limit)
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "language": m.language,
                "created_at": str(m.created_at),
            }
            for m in messages
        ],
    }


@app.get("/v1/analytics/sessions/{session_id}")
async def get_session_analytics(
    session_id: str,
    session=Depends(get_db_session),
):
    """Get analytics summary for a session (actions, errors, message counts)."""
    repo = SessionRepository(session)
    analytics = await repo.get_interaction_analytics(session_id)
    return analytics


@app.get("/v1/export/finetune")
async def export_finetune_data(
    session_id: str | None = None,
    limit: int = 1000,
    session=Depends(get_db_session),
):
    """Export chat interactions in JSONL format for fine-tuning."""
    repo = SessionRepository(session)
    data = await repo.get_chat_history_for_export(session_id=session_id, limit=limit)
    return {"count": len(data), "interactions": data}


@app.get("/v1/mcp/tools")
async def list_mcp_tools():
    """List all available MCP tools from the MCP server."""
    try:
        client = await get_mcp_client()
        tools = await client.list_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error("Failed to list MCP tools: %s", e)
        raise HTTPException(status_code=503, detail=f"MCP server unavailable: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

def run():
    import uvicorn
    uvicorn.run("agent_api.main:app", host="0.0.0.0", port=8000, reload=True)
