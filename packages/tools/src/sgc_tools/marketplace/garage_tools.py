from sqlalchemy import select

from sgc_db.models.marketplace import Garage, GarageAnalytics, GarageCapability, GarageExperience
from sgc_domain.garage_scorer import GarageScorer
from sgc_shared.types import SourceRef, ToolResult
from sgc_tools.registry import BaseTool


class RecommendGaragesTool(BaseTool):
    name = "recommend_garages"
    description = "Recommend garages based on capability, expertise, and convenience"

    async def execute(
        self,
        session,
        service_category=None,
        vehicle_brand="",
        vehicle_model="",
        customer_lat=None,
        customer_lng=None,
        needs_pickup=False,
        limit=3,
        **kwargs,
    ):
        garages_result = await session.execute(select(Garage))
        garages = list(garages_result.scalars().all())

        enriched = []
        for g in garages:
            cap = await session.execute(
                select(GarageCapability).where(GarageCapability.garage_id == g.garage_id)
            )
            analytics = await session.execute(
                select(GarageAnalytics).where(GarageAnalytics.garage_id == g.garage_id)
            )
            experience = await session.execute(
                select(GarageExperience).where(GarageExperience.garage_id == g.garage_id)
            )
            cap_row = cap.scalar_one_or_none()
            ana_row = analytics.scalar_one_or_none()
            exp_row = experience.scalar_one_or_none()

            if service_category and cap_row:
                categories = cap_row.service_categories or []
                if service_category not in categories:
                    continue

            enriched.append({
                "garage_id": g.garage_id,
                "garage_name": g.garage_name,
                "location_lat": float(g.location_lat) if g.location_lat else None,
                "location_lng": float(g.location_lng) if g.location_lng else None,
                "overall_rating": float(g.overall_rating) if g.overall_rating else 4.0,
                "top_brands_serviced": ana_row.top_brands_serviced if ana_row else [],
                "top_models_serviced": ana_row.top_models_serviced if ana_row else [],
                "specialization_tag": ana_row.specialization_tag if ana_row else "",
                "avg_vehicles_per_day": ana_row.avg_vehicles_per_day if ana_row else 0,
                "current_wait_time_days": ana_row.current_wait_time_days if ana_row else 3,
                "offers_pickup_drop": exp_row.offers_pickup_drop if exp_row else False,
                "pickup_radius_km": float(exp_row.pickup_radius_km) if exp_row and exp_row.pickup_radius_km else 0,
            })

        scorer = GarageScorer()
        ranked = scorer.rank(
            enriched,
            customer_lat=customer_lat,
            customer_lng=customer_lng,
            vehicle_brand=vehicle_brand,
            vehicle_model=vehicle_model,
            needs_pickup=needs_pickup,
        )[:limit]

        data = [
            {
                "garage_id": s.garage_id,
                "garage_name": s.garage_name,
                "match_score": s.total_score,
                "breakdown": s.breakdown,
                "match_reasons": s.match_reasons,
            }
            for s in ranked
        ]
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=data,
            source_refs=[SourceRef(table="marketplace.garages", record_id=d["garage_id"]) for d in data],
        )
