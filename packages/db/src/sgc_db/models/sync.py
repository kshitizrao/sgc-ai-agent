from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB

from sgc_db.base import Base


class ImportJob(Base):
    __tablename__ = "import_jobs"
    __table_args__ = {"schema": "sync"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(128), nullable=False)
    job_type = Column(String(64))
    status = Column(String(32), default="pending")
    records_processed = Column(Integer, default=0)
    error_log = Column(Text)
    job_metadata = Column(JSONB, default=dict)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)


class SourceMapping(Base):
    __tablename__ = "source_mappings"
    __table_args__ = {"schema": "sync"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    backend_system = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    backend_field = Column(String(128))
    agent_field = Column(String(128))
    transform_rule = Column(String(256))
