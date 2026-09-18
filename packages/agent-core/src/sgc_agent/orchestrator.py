"""Main agent orchestrator — classify, route, tool-execute, generate, govern.

This orchestrator supports two execution paths:
1. **MCP path** (PIKPART_QUERY): LLM classifies → MCP query planner → MCP tool
   execution → LLM response generation.
2. **Legacy path** (all other intents): keyword/LLM classify → local tool registry
   → LLM response generation.

Every step is logged with structured logging for debugging and audit.
"""

from __future__ import annotations

import json
import logging
import time

from sgc_agent.nodes.tool_executor import (
    execute_intent_tools,
    execute_pikpart_query,
    format_tool_results_for_prompt,
)
from sgc_agent.persona.system_prompts import AGENT_SYSTEM_PROMPT
from sgc_agent.router.intent_classifier import classify_intent_llm, classify_intent_keywords
from sgc_agent.state.agent_state import AgentState
from sgc_governance.engine import GovernanceEngine
from sgc_llm.router import ModelRouter
from sgc_shared.config import get_settings
from sgc_shared.constants import IntentType, TaskType
from sgc_shared.types import ContextEnvelope
from sgc_tools.registry import ToolRegistry, create_registry
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("agent.orchestrator")


class AgentOrchestrator:
    """Main agent orchestrator — classify, tool-first, generate, govern."""

    def __init__(
        self,
        db_session: AsyncSession,
        pikpart_session: AsyncSession | None = None,
        registry: ToolRegistry | None = None,
        llm_router: ModelRouter | None = None,
        governance: GovernanceEngine | None = None,
    ):
        self.db_session = db_session
        self.pikpart_session = pikpart_session
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
        total_start = time.perf_counter()

        logger.info(
            "Processing message",
            extra={
                "session_id": session_id,
                "message_preview": message[:100],
                "has_customer_context": bool(context.customer.customer_id),
            },
        )

        # ── Step 1: Governance input validation ────────────────────────
        input_check = await self.governance.validate_input(message, session_id)
        if not input_check.approved:
            logger.info(
                "Message blocked by governance",
                extra={"session_id": session_id, "reason": "input_validation"},
            )
            return {
                "response": input_check.content,
                "intent": IntentType.GENERAL_FAQ.value,
                "source_refs": [],
                "requires_human_review": False,
                "model_used": "",
            }

        # ── Step 2: Intent classification (LLM-based with fallback) ────
        intent_start = time.perf_counter()
        try:
            intent = await classify_intent_llm(message, self.llm_router)
        except Exception:
            intent = classify_intent_keywords(message)

        logger.info(
            "Intent classified",
            extra={
                "session_id": session_id,
                "intent": intent.value,
                "duration_ms": round((time.perf_counter() - intent_start) * 1000, 2),
            },
        )

        # ── Step 3: Execute tools based on intent ──────────────────────
        tool_start = time.perf_counter()

        if intent in (IntentType.PIKPART_QUERY, IntentType.SERVICE_BOOKING):
            # MCP path — query prod_pikpart via MCP server
            # SERVICE_BOOKING also uses MCP so the query planner can call booking tools
            tool_results, source_refs, tool_amounts = await execute_pikpart_query(
                message=message,
                context=context,
                llm_router=self.llm_router,
                session_id=session_id,
                registry=self.registry,
                db_session=self.pikpart_session or self.db_session,
            )
        elif intent == IntentType.GENERAL_FAQ:
            # No tool execution needed for greetings/FAQ
            tool_results, source_refs, tool_amounts = [], [], []
        else:
            # Legacy path — local tool registry
            tool_results, source_refs, tool_amounts = await execute_intent_tools(
                intent, message, context, self.registry, self.db_session
            )

        logger.info(
            "Tool execution completed",
            extra={
                "session_id": session_id,
                "intent": intent.value,
                "tools_called": len(tool_results),
                "duration_ms": round((time.perf_counter() - tool_start) * 1000, 2),
            },
        )

        # ── Step 4: Check for missing info from query planner ──────────
        if tool_results and tool_results[0].get("data", {}) and isinstance(tool_results[0]["data"], dict):
            missing_info = tool_results[0]["data"].get("missing_info")
            if missing_info:
                logger.info(
                    "Query planner needs more info from customer",
                    extra={"session_id": session_id, "missing_info": missing_info},
                )
                return {
                    "response": missing_info,
                    "intent": intent.value,
                    "source_refs": [],
                    "requires_human_review": False,
                    "model_used": "",
                    "tool_results": tool_results,
                }

        # ── Step 5: Handle empty/failed tool results ───────────────────
        if intent != IntentType.GENERAL_FAQ and (not tool_results or not any(
            tr.get("success") for tr in tool_results
        )):
            logger.warning(
                "No successful tool results",
                extra={"session_id": session_id, "intent": intent.value},
            )
            # Removed the hardcoded fallback return here. We want the LLM to
            # see the tool failure (e.g. missing API token) and generate a
            # context-aware, polite response instead of skipping the LLM entirely.

        # ── Step 6: Generate LLM response ──────────────────────────────
        llm_start = time.perf_counter()
        tool_context = format_tool_results_for_prompt(tool_results)

        messages = [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        ]

        # Add conversation history if available
        if history:
            for h in history[-6:]:  # Last 6 messages for context
                messages.append({"role": h["role"], "content": h["content"]})

        # Build user message with tool context
        user_content_parts = []
        if context.customer.customer_id:
            user_content_parts.append(f"Customer ID: {context.customer.customer_id}")
        if context.customer.first_name:
            user_content_parts.append(f"Customer First Name: {context.customer.first_name}")
        if context.customer.phone_number:
            user_content_parts.append(f"Phone Number: {context.customer.phone_number}")
        if context.customer.vehicle_make:
            user_content_parts.append(f"Vehicle: {context.customer.vehicle_make} {context.customer.vehicle_model or ''}")

        user_content_parts.append(f"Intent: {intent.value}")

        if tool_results:
            user_content_parts.append(f"Tool results (use ONLY this data for facts):\n{tool_context}")

        user_content_parts.append(f"Customer message: {message}")
        user_content_parts.append(
            "Respond in the same language the customer used. "
            "Be polite, helpful, and use simple language. "
            "Format prices in ₹ INR. Never dump raw JSON."
        )

        messages.append({"role": "user", "content": "\n\n".join(user_content_parts)})

        task = (
            TaskType.COMPLEX_REASONING
            if intent in (IntentType.CLAIMS, IntentType.DIAGNOSTICS)
            else TaskType.TOOL_NLG
        )
        llm_response = await self.llm_router.complete(messages, task=task)

        logger.info(
            "LLM response generated",
            extra={
                "session_id": session_id,
                "model": llm_response.model,
                "response_length": len(llm_response.content),
                "duration_ms": round((time.perf_counter() - llm_start) * 1000, 2),
            },
        )

        # ── Step 7: Determine if human review needed ───────────────────
        requires_review = intent in (IntentType.RSA, IntentType.CLAIMS) and any(
            tr.get("data", {}).get("requires_human_review")
            or tr.get("data", {}).get("severity_level") == "High"
            for tr in tool_results
            if isinstance(tr.get("data"), dict)
        )

        # ── Step 8: Governance output validation ───────────────────────
        output_check = await self.governance.validate_output(
            llm_response.content,
            session_id,
            tool_amounts=tool_amounts,
            model_used=llm_response.model,
            tools_called=[tr["tool_name"] for tr in tool_results],
            requires_human_review=requires_review,
        )

        total_ms = round((time.perf_counter() - total_start) * 1000, 2)
        logger.info(
            "Message processing completed",
            extra={
                "session_id": session_id,
                "intent": intent.value,
                "model": llm_response.model,
                "total_duration_ms": total_ms,
                "requires_review": output_check.requires_human_review,
            },
        )

        return {
            "response": output_check.content,
            "intent": intent.value,
            "source_refs": source_refs,
            "requires_human_review": output_check.requires_human_review,
            "model_used": llm_response.model,
            "tool_results": tool_results,
        }
