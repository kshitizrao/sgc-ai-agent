from sqlalchemy import Boolean, Column, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY

from sgc_db.base import Base


class Garage(Base):
    __tablename__ = "garages"
    __table_args__ = {"schema": "marketplace"}

    garage_id = Column(String(32), primary_key=True)
    garage_name = Column(String(256), nullable=False)
    location_lat = Column(Numeric(10, 7))
    location_lng = Column(Numeric(10, 7))
    address_area = Column(String(128))
    overall_rating = Column(Numeric(3, 2), default=4.0)
    standard_labor_rate = Column(Numeric(12, 2))


class GarageCapability(Base):
    __tablename__ = "garage_capabilities"
    __table_args__ = {"schema": "marketplace"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    garage_id = Column(String(32), nullable=False, index=True)
    service_categories = Column(ARRAY(String), default=list)
    cashless_insurance_tieups = Column(ARRAY(String), default=list)
    has_paint_booth = Column(Boolean, default=False)
    has_oem_scanner = Column(Boolean, default=False)


class GarageAnalytics(Base):
    __tablename__ = "garage_analytics"
    __table_args__ = {"schema": "marketplace"}

    garage_id = Column(String(32), primary_key=True)
    avg_vehicles_per_day = Column(Integer, default=10)
    top_brands_serviced = Column(ARRAY(String), default=list)
    top_models_serviced = Column(ARRAY(String), default=list)
    specialization_tag = Column(String(128))
    current_wait_time_days = Column(Integer, default=0)


class GarageExperience(Base):
    __tablename__ = "garage_experience"
    __table_args__ = {"schema": "marketplace"}

    garage_id = Column(String(32), primary_key=True)
    offers_pickup_drop = Column(Boolean, default=False)
    pickup_radius_km = Column(Numeric(6, 2))
    has_customer_lounge = Column(Boolean, default=False)
    provides_warranty = Column(String(128))
    live_video_feed = Column(Boolean, default=False)
