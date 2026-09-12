"""Session repository — CRUD for conversations, messages, tool invocations,
chat interactions, and agent action logs.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sgc_db.models.agent_meta import (
    AgentActionLog,
    ChatInteraction,
    Conversation,
    Message,
    ToolInvocation,
)


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Conversations ──────────────────────────────────────────────────

    async def create_conversation(
        self, session_id: str, customer_id: str | None, context: dict
    ) -> Conversation:
        conv = Conversation(
            session_id=session_id,
            customer_id=customer_id,
            context_snapshot=context,
        )
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def get_conversation(self, session_id: str) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        return result.scalar_one_or_none()

    # ── Messages ───────────────────────────────────────────────────────

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        source_refs: list | None = None,
        language: str = "en",
    ) -> Message:
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            source_refs=source_refs or [],
            language=language,
        )
        self.session.add(msg)
        await self.session.commit()
        return msg

    async def get_messages(self, session_id: str, limit: int = 50) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Tool Invocations ───────────────────────────────────────────────

    async def log_tool_invocation(
        self,
        session_id: str,
        tool_name: str,
        input_payload: dict,
        output_payload: dict,
        success: bool,
    ) -> ToolInvocation:
        inv = ToolInvocation(
            session_id=session_id,
            tool_name=tool_name,
            input_payload=input_payload,
            output_payload=output_payload,
            success=success,
        )
        self.session.add(inv)
        await self.session.commit()
        return inv

    # ── Chat Interactions (for fine-tuning export) ─────────────────────

    async def log_chat_interaction(
        self,
        session_id: str,
        user_message: str,
        agent_response: str,
        detected_intent: str | None = None,
        detected_language: str = "en",
        tools_called: list[str] | None = None,
        tool_results_summary: dict | None = None,
        model_used: str | None = None,
        response_latency_ms: float | None = None,
        requires_human_review: bool = False,
        customer_id: str | None = None,
        customer_context: dict | None = None,
    ) -> ChatInteraction:
        """Save a complete user ↔ agent exchange for future fine-tuning."""
        interaction = ChatInteraction(
            session_id=session_id,
            customer_id=customer_id,
            user_message=user_message,
            agent_response=agent_response,
            detected_intent=detected_intent,
            detected_language=detected_language,
            tools_called=tools_called or [],
            tool_results_summary=tool_results_summary or {},
            model_used=model_used,
            response_latency_ms=response_latency_ms,
            requires_human_review=requires_human_review,
            customer_context=customer_context or {},
        )
        self.session.add(interaction)
        await self.session.commit()
        return interaction

    async def get_chat_history_for_export(
        self, session_id: str | None = None, limit: int = 1000
    ) -> list[dict]:
        """Export chat interactions in JSONL-compatible format for fine-tuning.

        Each returned dict has the structure::

            {
                "messages": [
                    {"role": "user", "content": "..."},
                    {"role": "assistant", "content": "..."}
                ],
                "metadata": {
                    "intent": "...",
                    "language": "...",
                    "tools_used": [...],
                    "model": "..."
                }
            }
        """
        query = select(ChatInteraction).order_by(ChatInteraction.created_at.desc()).limit(limit)
        if session_id:
            query = query.where(ChatInteraction.session_id == session_id)
        # Exclude interactions that require human review (potentially bad quality)
        query = query.where(ChatInteraction.requires_human_review == False)  # noqa: E712

        result = await self.session.execute(query)
        interactions = result.scalars().all()

        export = []
        for i in interactions:
            export.append({
                "messages": [
                    {"role": "user", "content": i.user_message},
                    {"role": "assistant", "content": i.agent_response},
                ],
                "metadata": {
                    "intent": i.detected_intent,
                    "language": i.detected_language,
                    "tools_used": i.tools_called,
                    "model": i.model_used,
                    "latency_ms": i.response_latency_ms,
                    "session_id": i.session_id,
                },
            })
        return export

    # ── Agent Action Logs (for debugging) ──────────────────────────────

    async def log_agent_action(
        self,
        session_id: str,
        action_type: str,
        action_input: dict | None = None,
        action_output: dict | None = None,
        duration_ms: float | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AgentActionLog:
        """Log an agent decision step for debugging."""
        log = AgentActionLog(
            session_id=session_id,
            action_type=action_type,
            action_input=action_input,
            action_output=action_output,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
        )
        self.session.add(log)
        await self.session.commit()
        return log

    async def get_agent_actions(self, session_id: str) -> list[AgentActionLog]:
        """Get the full decision chain for a session."""
        result = await self.session.execute(
            select(AgentActionLog)
            .where(AgentActionLog.session_id == session_id)
            .order_by(AgentActionLog.created_at)
        )
        return list(result.scalars().all())

    async def get_interaction_analytics(self, session_id: str) -> dict[str, Any]:
        """Summary analytics for a session."""
        messages = await self.get_messages(session_id)
        actions = await self.get_agent_actions(session_id)

        user_msgs = [m for m in messages if m.role == "user"]
        assistant_msgs = [m for m in messages if m.role == "assistant"]

        return {
            "session_id": session_id,
            "total_messages": len(messages),
            "user_messages": len(user_msgs),
            "assistant_messages": len(assistant_msgs),
            "total_actions": len(actions),
            "action_types": list({a.action_type for a in actions}),
            "errors": [
                {"type": a.action_type, "error": a.error_message}
                for a in actions
                if not a.success
            ],
        }
