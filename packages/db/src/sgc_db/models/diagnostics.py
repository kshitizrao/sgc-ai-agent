from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY

from sgc_db.base import Base


class VehicleIssue(Base):
    __tablename__ = "vehicle_issues"
    __table_args__ = {"schema": "diagnostics"}

    issue_id = Column(String(32), primary_key=True)
    issue_name = Column(String(256), nullable=False)
    system_category = Column(String(64))
    severity_level = Column(String(16))
    is_safety_risk = Column(Boolean, default=False)
    standard_obd2_code = Column(String(16))
    resolution_service_id = Column(String(32))


class PredictiveFailureMatrix(Base):
    __tablename__ = "predictive_failure_matrix"
    __table_args__ = {"schema": "diagnostics"}

    prediction_id = Column(String(32), primary_key=True)
    issue_id = Column(String(32), nullable=False)
    vehicle_make = Column(String(64))
    vehicle_model = Column(String(64))
    fuel_type = Column(String(32))
    risk_start_km = Column(Integer)
    risk_end_km = Column(Integer)
    risk_start_age_months = Column(Integer)
    probability_score = Column(String(16))


class SymptomMapping(Base):
    __tablename__ = "symptom_mapping"
    __table_args__ = {"schema": "diagnostics"}

    symptom_id = Column(String(32), primary_key=True)
    issue_id = Column(String(32), nullable=False)
    customer_keywords = Column(ARRAY(String), default=list)
    sensory_category = Column(String(32))
    ai_diagnostic_question = Column(Text)
