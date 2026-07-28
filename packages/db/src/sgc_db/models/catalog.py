from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from sgc_db.base import Base


class Part(Base):
    __tablename__ = "parts"
    __table_args__ = {"schema": "catalog"}

    part_id = Column(String(32), primary_key=True)
    sku = Column(String(64), nullable=False, index=True)
    oem_part_number = Column(String(64), index=True)
    manufacturer_part_number = Column(String(64))
    part_name = Column(String(256), nullable=False)
    category = Column(String(64))
    sub_category = Column(String(64))
    part_brand = Column(String(64))
    part_type = Column(String(32))
    condition = Column(String(32), default="New")
    warranty_months = Column(Integer)
    stock_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=5)
    bin_location = Column(String(64))
    supplier_name = Column(String(128))
    cost_price = Column(Numeric(12, 2))
    selling_price = Column(Numeric(12, 2))
    labour_code = Column(String(32))
    gst_slab = Column(Numeric(5, 2), default=28.0)
    search_tags = Column(ARRAY(String), default=list)
    installation_notes = Column(Text)
    embedding = Column(Text)  # pgvector stored via raw migration

    fitments = relationship("PartFitment", back_populates="part")
    interchanges_from = relationship(
        "PartInterchange",
        foreign_keys="PartInterchange.part_id",
        back_populates="part",
    )


class PartFitment(Base):
    __tablename__ = "part_fitment"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    part_id = Column(String(32), ForeignKey("catalog.parts.part_id"), nullable=False)
    vehicle_make = Column(String(64), nullable=False, index=True)
    vehicle_model = Column(String(64), nullable=False, index=True)
    vehicle_variant = Column(String(64))
    fuel_type = Column(String(32), index=True)
    transmission_type = Column(String(32))
    year_from = Column(Integer)
    year_to = Column(Integer)

    part = relationship("Part", back_populates="fitments")


class PartInterchange(Base):
    __tablename__ = "part_interchanges"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    part_id = Column(String(32), ForeignKey("catalog.parts.part_id"), nullable=False)
    alternate_part_id = Column(String(32), ForeignKey("catalog.parts.part_id"), nullable=False)
    notes = Column(Text)

    part = relationship("Part", foreign_keys=[part_id], back_populates="interchanges_from")


class VehicleSegment(Base):
    __tablename__ = "vehicle_segments"
    __table_args__ = {"schema": "catalog"}

    segment_id = Column(String(32), primary_key=True)
    body_type = Column(String(64), nullable=False)
    fuel_type = Column(String(32), nullable=False)
    engine_oil_capacity = Column(Numeric(5, 2))
    description = Column(Text)


class ServicePackage(Base):
    __tablename__ = "service_packages"
    __table_args__ = {"schema": "catalog"}

    package_id = Column(String(32), primary_key=True)
    package_name = Column(String(128), nullable=False)
    interval_km = Column(Integer)
    interval_months = Column(Integer)
    package_description = Column(Text)


class ServiceInclusion(Base):
    __tablename__ = "service_inclusions"
    __table_args__ = {"schema": "catalog"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    package_id = Column(String(32), ForeignKey("catalog.service_packages.package_id"))
    inclusion_key = Column(String(64), nullable=False)
    inclusion_value = Column(String(128), nullable=False)


class PricingMatrix(Base):
    __tablename__ = "pricing_matrix"
    __table_args__ = {"schema": "catalog"}

    pricing_id = Column(String(32), primary_key=True)
    package_id = Column(String(32), ForeignKey("catalog.service_packages.package_id"))
    segment_id = Column(String(32), ForeignKey("catalog.vehicle_segments.segment_id"))
    labour_cost = Column(Numeric(12, 2), nullable=False)
    consumables_cost = Column(Numeric(12, 2), nullable=False)
    total_estimated_cost = Column(Numeric(12, 2), nullable=False)
    service_duration_hrs = Column(Numeric(5, 2))


class AddOnRepair(Base):
    __tablename__ = "add_on_repairs"
    __table_args__ = {"schema": "catalog"}

    repair_id = Column(String(32), primary_key=True)
    repair_name = Column(String(256), nullable=False)
    symptom_tags = Column(ARRAY(String), default=list)
    cost_hatchback = Column(Numeric(12, 2))
    cost_sedan = Column(Numeric(12, 2))
    cost_suv = Column(Numeric(12, 2))
    is_safety_critical = Column(Boolean, default=False)


class QuickService(Base):
    __tablename__ = "quick_services"
    __table_args__ = {"schema": "catalog"}

    service_id = Column(String(32), primary_key=True)
    service_name = Column(String(128), nullable=False)
    service_category = Column(String(64))
    duration_mins = Column(Integer, default=15)
    symptom_tags = Column(ARRAY(String), default=list)
    action_type = Column(String(64))


class QuickServicePricing(Base):
    __tablename__ = "quick_service_pricing"
    __table_args__ = {"schema": "catalog"}

    pricing_id = Column(String(32), primary_key=True)
    service_id = Column(String(32), ForeignKey("catalog.quick_services.service_id"))
    segment_id = Column(String(32), ForeignKey("catalog.vehicle_segments.segment_id"))
    labour_cost = Column(Numeric(12, 2))
    consumables_cost = Column(Numeric(12, 2))
    total_estimated_cost = Column(Numeric(12, 2))


class ServiceMaster(Base):
    __tablename__ = "service_master"
    __table_args__ = {"schema": "catalog"}

    service_id = Column(String(32), primary_key=True)
    service_name = Column(String(256), nullable=False)
    service_category = Column(String(64))
    standard_labor_hours = Column(Numeric(5, 2))
    is_package = Column(Boolean, default=False)


class LaborCostMatrix(Base):
    __tablename__ = "labor_cost_matrix"
    __table_args__ = {"schema": "catalog"}

    labor_rate_id = Column(String(32), primary_key=True)
    service_id = Column(String(32), ForeignKey("catalog.service_master.service_id"))
    vehicle_segment = Column(String(64), nullable=False)
    base_labor_cost_inr = Column(Numeric(12, 2))
    labor_gst_percent = Column(Numeric(5, 2), default=18.0)
    total_labor_cost_inc_tax = Column(Numeric(12, 2))


class ServicePartsBom(Base):
    __tablename__ = "service_parts_bom"
    __table_args__ = {"schema": "catalog"}

    bom_id = Column(String(32), primary_key=True)
    service_id = Column(String(32), ForeignKey("catalog.service_master.service_id"))
    variant_id = Column(String(64))
    part_id = Column(String(32), ForeignKey("catalog.parts.part_id"))
    required_quantity = Column(Numeric(10, 2))
    unit_of_measure = Column(String(32))


class PartsCostMaster(Base):
    __tablename__ = "parts_cost_master"
    __table_args__ = {"schema": "catalog"}

    part_cost_id = Column(String(32), primary_key=True)
    part_id = Column(String(32), ForeignKey("catalog.parts.part_id"))
    part_grade_type = Column(String(32))
    part_mrp_inr = Column(Numeric(12, 2))
    garage_purchase_cost_inr = Column(Numeric(12, 2))
    part_gst_percent = Column(Numeric(5, 2), default=28.0)
    selling_price_excl_tax = Column(Numeric(12, 2))


class AuxiliaryCharge(Base):
    __tablename__ = "auxiliary_charges"
    __table_args__ = {"schema": "catalog"}

    aux_charge_id = Column(String(32), primary_key=True)
    charge_name = Column(String(128), nullable=False)
    calculation_type = Column(String(32))
    charge_value = Column(Numeric(12, 2))
    aux_gst_percent = Column(Numeric(5, 2), default=18.0)
    is_mandatory = Column(Boolean, default=False)
