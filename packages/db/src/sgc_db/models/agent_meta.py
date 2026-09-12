"""SQLAlchemy models for agent metadata (sgc_agent database).

Tables live in the ``agent_meta`` schema and store conversations, messages,
tool invocations, chat interactions (for fine-tuning), and agent action logs
(for debugging).
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB

from sgc_db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = {"schema": "agent_meta"}

    session_id = Column(String(64), primary_key=True)
    customer_id = Column(String(64), index=True)
    vehicle_id = Column(String(64))
    context_snapshot = Column(JSONB, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema": "agent_meta"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    source_refs = Column(JSONB, default=list)
    language = Column(String(16), default="en")
    created_at = Column(DateTime, server_default=func.now())


class ToolInvocation(Base):
    __tablename__ = "tool_invocations"
    __table_args__ = {"schema": "agent_meta"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    tool_name = Column(String(64), nullable=False)
    input_payload = Column(JSONB)
    output_payload = Column(JSONB)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class CustomerContextCache(Base):
    __tablename__ = "customer_context_cache"
    __table_args__ = {"schema": "agent_meta"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(64), index=True)
    vehicle_id = Column(String(64))
    context_data = Column(JSONB, default=dict)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ═══════════════════════════════════════════════════════════════════════════
# NEW: Chat interaction for fine-tuning data export
# ═══════════════════════════════════════════════════════════════════════════

class ChatInteraction(Base):
    """Stores every complete user ↔ agent exchange for future fine-tuning.

    Each row captures the full round-trip: user message → intent → tools used
    → agent response, along with metadata for quality filtering.
    """
    __tablename__ = "chat_interactions"
    __table_args__ = {"schema": "agent_meta"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    customer_id = Column(String(64), index=True)

    # The exchange
    user_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)

    # Classification & routing metadata
    detected_intent = Column(String(32))
    detected_language = Column(String(16), default="en")

    # Tool execution metadata
    tools_called = Column(JSONB, default=list)  # list of tool names
    tool_results_summary = Column(JSONB, default=dict)  # condensed tool output

    # LLM metadata
    model_used = Column(String(64))
    response_latency_ms = Column(Float)

    # Quality signals (for filtering fine-tuning data)
    requires_human_review = Column(Boolean, default=False)
    customer_context = Column(JSONB, default=dict)

    created_at = Column(DateTime, server_default=func.now())


# ═══════════════════════════════════════════════════════════════════════════
# NEW: Agent action log for debugging
# ═══════════════════════════════════════════════════════════════════════════

class AgentActionLog(Base):
    """Detailed log of every agent decision step for debugging.

    Captures the full chain: intent classification → tool selection → SQL
    execution → result processing → response generation.
    """
    __tablename__ = "agent_action_logs"
    __table_args__ = {"schema": "agent_meta"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)

    # Action metadata
    action_type = Column(String(32), nullable=False)
    # Values: 'intent_classify', 'query_plan', 'mcp_tool_call', 'llm_generate',
    #         'governance_check', 'error'

    # Details
    action_input = Column(JSONB)   # what went into this step
    action_output = Column(JSONB)  # what came out
    duration_ms = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
