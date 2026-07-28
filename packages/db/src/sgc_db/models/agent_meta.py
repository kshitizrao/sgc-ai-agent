from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
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
