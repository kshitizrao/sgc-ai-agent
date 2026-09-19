from dataclasses import dataclass, field
import time

from sqlalchemy.ext.asyncio import AsyncSession

from sgc_governance.guardrails.fact_check import fact_check_response
from sgc_governance.guardrails.input_guard import check_input, check_output_tone
from sgc_governance.pii.redactor import redact_pii
from sgc_governance.prompt_registry.defaults import ESCALATION_TEMPLATES, SYSTEM_PROMPT_V1, TONE_BLOCKLIST
from sgc_db.models.governance import GovernanceEvent


@dataclass
class GovernanceResult:
    approved: bool
    content: str
    decision: str
    details: dict = field(default_factory=dict)
    prompt_version: str = "v1"
    requires_human_review: bool = False


class GovernanceEngine:
    """Wraps every LLM input/output with guardrails and audit logging."""

    def __init__(self, db_session: AsyncSession | None = None):
        self.db_session = db_session
        self.system_prompt = SYSTEM_PROMPT_V1
        self.tone_blocklist = TONE_BLOCKLIST

    async def validate_input(self, text: str, session_id: str) -> GovernanceResult:
        start = time.perf_counter()
        safe_text = redact_pii(text)
        ok, reason = check_input(safe_text)
        latency = int((time.perf_counter() - start) * 1000)

        result = GovernanceResult(
            approved=ok,
            content=safe_text if ok else "I'm sorry, I couldn't process that message. How can I help with your vehicle today?",
            decision="input_allowed" if ok else "input_blocked",
            details={"reason": reason} if reason else {},
        )
        await self._log_event(session_id, "input_guard", result, latency)
        return result

    async def validate_output(
        self,
        response: str,
        session_id: str,
        tool_amounts: list | None = None,
        model_used: str = "",
        tools_called: list[str] | None = None,
        requires_human_review: bool = False,
    ) -> GovernanceResult:
        start = time.perf_counter()
        ok_tone, tone_reason = check_output_tone(response, self.tone_blocklist)
        ok_facts, fact_reason = fact_check_response(response, tool_amounts or [])

        approved = ok_tone and ok_facts
        decision = "output_allowed"
        details: dict = {}

        if not ok_tone:
            decision = "output_tone_blocked"
            details["reason"] = tone_reason
        elif not ok_facts:
            decision = "output_fact_blocked"
            details["reason"] = fact_reason
            response = ESCALATION_TEMPLATES["no_data"]

        latency = int((time.perf_counter() - start) * 1000)
        result = GovernanceResult(
            approved=approved,
            content=response if approved else ESCALATION_TEMPLATES["no_data"],
            decision=decision,
            details=details,
            requires_human_review=requires_human_review,
        )
        await self._log_event(
            session_id,
            "output_guard",
            result,
            latency,
            model_used=model_used,
            tools_called=tools_called or [],
        )
        return result

    async def _log_event(
        self,
        session_id: str,
        event_type: str,
        result: GovernanceResult,
        latency_ms: int,
        model_used: str = "",
        tools_called: list | None = None,
    ) -> None:
        if not self.db_session:
            return
        event = GovernanceEvent(
            session_id=session_id,
            event_type=event_type,
            model_used=model_used,
            prompt_version=result.prompt_version,
            tools_called=tools_called or [],
            decision=result.decision,
            details=result.details,
            latency_ms=latency_ms,
        )
        self.db_session.add(event)
        
        import sqlalchemy.exc
        import logging
        logger = logging.getLogger("agent.governance")
        try:
            await self.db_session.commit()
        except sqlalchemy.exc.SQLAlchemyError as e:
            logger.warning(f"Failed to commit governance event, rolling back and retrying: {e}")
            await self.db_session.rollback()
            self.db_session.add(event)
            try:
                await self.db_session.commit()
            except Exception as retry_e:
                logger.error(f"Failed to log governance event after retry: {retry_e}")

    def get_system_prompt(self) -> str:
        return self.system_prompt
