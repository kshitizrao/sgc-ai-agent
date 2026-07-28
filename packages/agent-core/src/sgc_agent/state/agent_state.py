from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages
from sgc_shared.constants import IntentType
from sgc_shared.types import ContextEnvelope, SourceRef, ToolResult


class AgentState(TypedDict):
    session_id: str
    messages: Annotated[list, add_messages]
    context: dict
    intent: str | None
    tool_results: list[dict]
    source_refs: list[dict]
    tool_amounts: list[float]
    draft_response: str
    final_response: str
    requires_human_review: bool
    model_used: str
