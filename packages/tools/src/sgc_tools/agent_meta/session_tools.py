from sgc_shared.types import ToolResult
from sgc_tools.registry import BaseTool


class CreateSessionNoteTool(BaseTool):
    name = "create_session_note"
    description = "Create an escalation note for human advisor review"

    async def execute(self, session, session_id, note, priority="normal", **kwargs):
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"session_id": session_id, "note": note, "priority": priority, "escalated": True},
        )
