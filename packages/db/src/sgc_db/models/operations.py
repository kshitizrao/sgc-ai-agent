from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from sgc_db.base import Base


class Claim(Base):
    __tablename__ = "claims"
    __table_args__ = {"schema": "operations"}

    claim_id = Column(String(32), primary_key=True)
    vehicle_reg_no = Column(String(32), index=True)
    insurance_provider = Column(String(128))
    claim_type = Column(String(32))
    incident_date = Column(DateTime)
    intimation_date = Column(DateTime)
    claim_status = Column(String(64), default="Intimated")
    surveyor_name = Column(String(128))
    surveyor_contact = Column(String(32))
    symptom_tags = Column(ARRAY(String), default=list)


class PolicyRule(Base):
    __tablename__ = "policy_rules"
    __table_args__ = {"schema": "operations"}

    policy_id = Column(String(32), primary_key=True)
    vehicle_reg_no = Column(String(32), index=True)
    policy_type = Column(String(64))
    compulsory_deductible = Column(Numeric(12, 2), default=1000)
    consumables_cover_addon = Column(Boolean, default=False)
    engine_protect_addon = Column(Boolean, default=False)
    salvage_value_logic = Column(Numeric(5, 2), default=5.0)


class ClaimLineItem(Base):
    __tablename__ = "claim_line_items"
    __table_args__ = {"schema": "operations"}

    estimate_line_id = Column(String(32), primary_key=True)
    claim_id = Column(String(32), ForeignKey("operations.claims.claim_id"))
    part_id = Column(String(32))
    part_material = Column(String(32))
    garage_est_amount = Column(Numeric(12, 2))
    surveyor_apprv_amount = Column(Numeric(12, 2))
    surveyor_action = Column(String(32))
    rejection_reason = Column(Text)
    customer_liability = Column(Numeric(12, 2))


class EmergencyTriageRule(Base):
    __tablename__ = "emergency_triage_rules"
    __table_args__ = {"schema": "operations"}

    symptom_id = Column(String(32), primary_key=True)
    symptom_tags = Column(ARRAY(String), default=list)
    severity_level = Column(String(16))
    required_action = Column(String(32))
    safety_prompt = Column(Text)


class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"
    __table_args__ = {"schema": "operations"}

    request_id = Column(String(32), primary_key=True)
    customer_vehicle_id = Column(String(32))
    reported_issue = Column(Text)
    ai_matched_symptom = Column(String(32))
    customer_lat = Column(Numeric(10, 7))
    customer_lng = Column(Numeric(10, 7))
    maps_pin_url = Column(String(512))
    status = Column(String(32), default="Assessing")
    created_at = Column(DateTime, server_default=func.now())


class FieldResource(Base):
    __tablename__ = "field_resources"
    __table_args__ = {"schema": "operations"}

    resource_id = Column(String(32), primary_key=True)
    resource_type = Column(String(32))
    current_lat = Column(Numeric(10, 7))
    current_lng = Column(Numeric(10, 7))
    availability_status = Column(String(16), default="Available")
    max_operating_radius_km = Column(Numeric(6, 2))
    contact_number = Column(String(32))
