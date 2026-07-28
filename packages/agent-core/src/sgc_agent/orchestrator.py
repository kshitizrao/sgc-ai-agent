import json

from sgc_agent.nodes.tool_executor import execute_intent_tools, format_tool_results_for_prompt
from sgc_agent.router.intent_classifier import classify_intent
from sgc_agent.state.agent_state import AgentState
from sgc_governance.engine import GovernanceEngine
from sgc_llm.router import ModelRouter
from sgc_shared.config import get_settings
from sgc_shared.constants import IntentType, TaskType
from sgc_shared.types import ContextEnvelope
from sgc_tools.registry import ToolRegistry, create_registry
from sqlalchemy.ext.asyncio import AsyncSession


class AgentOrchestrator:
    """Main agent orchestrator — classify, tool-first, generate, govern."""

    def __init__(
        self,
        db_session: AsyncSession,
        registry: ToolRegistry | None = None,
        llm_router: ModelRouter | None = None,
        governance: GovernanceEngine | None = None,
    ):
        self.db_session = db_session
        self.registry = registry or create_registry()
        self.llm_router = llm_router or ModelRouter(use_mock=get_settings().environment == "test")
        self.governance = governance or GovernanceEngine(db_session)

    async def process_message(
        self,
        session_id: str,
        message: str,
        context: ContextEnvelope,
        history: list[dict] | None = None,
    ) -> dict:
        input_check = await self.governance.validate_input(message, session_id)
        if not input_check.approved:
            return {
                "response": input_check.content,
                "intent": IntentType.GENERAL_FAQ.value,
                "source_refs": [],
                "requires_human_review": False,
                "model_used": "",
            }

        intent = classify_intent(message)
        tool_results, source_refs, tool_amounts = await execute_intent_tools(
            intent, message, context, self.registry, self.db_session
        )

        if not tool_results or not tool_results[0].get("success"):
            fallback = (
                "I don't have that information yet; let me connect you with our team. "
                "Could you share a few more details about your vehicle?"
            )
            return {
                "response": fallback,
                "intent": intent.value,
                "source_refs": source_refs,
                "requires_human_review": False,
                "model_used": "",
            }

        tool_context = format_tool_results_for_prompt(tool_results)
        system_prompt = self.governance.get_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                f"Customer context: {context.customer.model_dump_json()}\n"
                f"Intent: {intent.value}\n"
                f"Tool results (use ONLY this data for facts):\n{tool_context}\n\n"
                f"Customer message: {message}\n\n"
                "Respond in a respectful, friendly tone. Include specific facts from tool results only."
            )},
        ]

        task = TaskType.COMPLEX_REASONING if intent in (IntentType.CLAIMS, IntentType.DIAGNOSTICS) else TaskType.TOOL_NLG
        llm_response = await self.llm_router.complete(messages, task=task)

        requires_review = intent in (IntentType.RSA, IntentType.CLAIMS) and any(
            tr.get("data", {}).get("requires_human_review") or tr.get("data", {}).get("severity_level") == "High"
            for tr in tool_results
            if isinstance(tr.get("data"), dict)
        )

        output_check = await self.governance.validate_output(
            llm_response.content,
            session_id,
            tool_amounts=tool_amounts,
            model_used=llm_response.model,
            tools_called=[tr["tool_name"] for tr in tool_results],
            requires_human_review=requires_review,
        )

        return {
            "response": output_check.content,
            "intent": intent.value,
            "source_refs": source_refs,
            "requires_human_review": output_check.requires_human_review,
            "model_used": llm_response.model,
            "tool_results": tool_results,
        }
