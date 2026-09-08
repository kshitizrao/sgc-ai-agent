#!/usr/bin/env python3
"""Seed the agent database with sample Smart Garage data."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "db" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "shared" / "src"))

from sqlalchemy import select
from sgc_db.models.catalog import (
    Part,
    PartFitment,
    PartInterchange,
    PricingMatrix,
    ServiceInclusion,
    ServicePackage,
    VehicleSegment,
)
from sgc_db.models.diagnostics import PredictiveFailureMatrix, SymptomMapping, VehicleIssue
from sgc_db.models.marketplace import Garage, GarageAnalytics, GarageCapability, GarageExperience
from sgc_db.models.operations import Claim, ClaimLineItem, EmergencyTriageRule, FieldResource, PolicyRule
from sgc_db.seeds.sample_data import (
    SEED_CLAIMS,
    SEED_DIAGNOSTICS,
    SEED_FITMENTS,
    SEED_GARAGES,
    SEED_INCLUSIONS,
    SEED_INTERCHANGES,
    SEED_PACKAGES,
    SEED_PARTS,
    SEED_PRICING,
    SEED_SEGMENTS,
    SEED_TRIAGE,
)
from sgc_db.session import get_session_factory


async def seed() -> None:
    factory = get_session_factory()
    async with factory() as session:
        for row in SEED_PARTS:
            session.add(Part(**row))
        await session.flush()
        for row in SEED_FITMENTS:
            session.add(PartFitment(**row))
        for row in SEED_INTERCHANGES:
            session.add(PartInterchange(**row))
        await session.flush()
        for row in SEED_SEGMENTS:
            session.add(VehicleSegment(**row))
        await session.flush()
        for row in SEED_PACKAGES:
            session.add(ServicePackage(**row))
        await session.flush()
        for row in SEED_INCLUSIONS:
            session.add(ServiceInclusion(**row))
        for row in SEED_PRICING:
            session.add(PricingMatrix(**row))
        await session.flush()
        for row in SEED_TRIAGE:
            session.add(EmergencyTriageRule(**row))
        await session.flush()
        for row in SEED_GARAGES:
            session.add(Garage(**row))
        await session.flush()
        for g in SEED_GARAGES:
            session.add(GarageCapability(
                garage_id=g["garage_id"],
                service_categories=["Periodic Service", "AC Repair", "Denting & Painting"],
                cashless_insurance_tieups=["HDFC Ergo", "Acko"],
                has_paint_booth=g["garage_id"] == "GRG-DEL-045",
                has_oem_scanner=True,
            ))
            session.add(GarageAnalytics(
                garage_id=g["garage_id"],
                avg_vehicles_per_day=15 if g["garage_id"] == "GRG-DEL-045" else 20,
                top_brands_serviced=["Volkswagen", "Hyundai"] if g["garage_id"] == "GRG-DEL-045" else ["Maruti Suzuki", "Hyundai"],
                top_models_serviced=["Polo", "Creta"] if g["garage_id"] == "GRG-DEL-045" else ["Swift", "Creta"],
                specialization_tag="German Car Expert" if g["garage_id"] == "GRG-DEL-045" else "AC Specialist",
                current_wait_time_days=1 if g["garage_id"] == "GRG-DEL-045" else 0,
            ))
            session.add(GarageExperience(
                garage_id=g["garage_id"],
                offers_pickup_drop=True,
                pickup_radius_km=10,
                has_customer_lounge=True,
                provides_warranty="6 Months on Parts, 1 Month on Labor",
            ))
        await session.flush()
        for row in SEED_DIAGNOSTICS:
            if "issue_name" in row:
                session.add(VehicleIssue(**row))
            elif "symptom_id" in row and "customer_keywords" in row:
                session.add(SymptomMapping(**row))
            elif "prediction_id" in row:
                session.add(PredictiveFailureMatrix(**row))
        await session.flush()
        for row in SEED_CLAIMS:
            if "claim_id" in row and "insurance_provider" in row:
                session.add(Claim(**row))
            elif "policy_id" in row:
                session.add(PolicyRule(**row))
            elif "estimate_line_id" in row:
                session.add(ClaimLineItem(**row))
        await session.flush()

        session.add(FieldResource(
            resource_id="MECH-BIKE-04",
            resource_type="Bike_Mechanic",
            current_lat=28.6150,
            current_lng=77.2080,
            availability_status="Available",
            max_operating_radius_km=15,
            contact_number="+919876543210",
        ))
        session.add(FieldResource(
            resource_id="DRV-FLATBED-01",
            resource_type="Flatbed_Tow",
            current_lat=28.6100,
            current_lng=77.2050,
            availability_status="Available",
            max_operating_radius_km=30,
            contact_number="+919876543211",
        ))

        await session.commit()
        print("Seed data inserted successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
