from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB

from sgc_db.base import Base


class GovernancePolicy(Base):
    __tablename__ = "policies"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_name = Column(String(128), unique=True, nullable=False)
    policy_type = Column(String(64))
    rules = Column(JSONB, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_key = Column(String(64), nullable=False, index=True)
    version = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class GovernanceEvent(Base):
    __tablename__ = "guardrail_events"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True)
    event_type = Column(String(64))
    model_used = Column(String(128))
    prompt_version = Column(String(16))
    tools_called = Column(JSONB, default=list)
    decision = Column(String(32))
    details = Column(JSONB, default=dict)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
