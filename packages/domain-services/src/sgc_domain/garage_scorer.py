from dataclasses import dataclass
from decimal import Decimal
import math


@dataclass
class GarageScore:
    garage_id: str
    garage_name: str
    total_score: float
    breakdown: dict[str, float]
    match_reasons: list[str]


class GarageScorer:
    """100-point garage matching algorithm from spec."""

    MAX_EXPERTISE = 40
    MAX_CONVENIENCE = 30
    MAX_TRUST = 15
    MAX_SPEED = 15

    def score(
        self,
        garage: dict,
        customer_lat: float | None,
        customer_lng: float | None,
        vehicle_brand: str,
        vehicle_model: str,
        needs_pickup: bool = False,
    ) -> GarageScore:
        breakdown: dict[str, float] = {}
        reasons: list[str] = []

        # Expertise (40 pts)
        expertise = 0.0
        top_brands = [b.lower() for b in garage.get("top_brands_serviced", [])]
        top_models = [m.lower() for m in garage.get("top_models_serviced", [])]
        if vehicle_brand.lower() in top_brands:
            expertise += 20
            reasons.append(f"Specialises in {vehicle_brand}")
        if vehicle_model.lower() in top_models:
            expertise += 10
            reasons.append(f"Frequently services {vehicle_model}")
        spec_tag = garage.get("specialization_tag", "")
        if spec_tag:
            expertise += 10
            reasons.append(spec_tag)
        breakdown["expertise"] = min(expertise, self.MAX_EXPERTISE)

        # Convenience (30 pts)
        convenience = 0.0
        dist_km = self._distance_km(
            customer_lat, customer_lng,
            garage.get("location_lat"), garage.get("location_lng"),
        )
        if dist_km is not None:
            if dist_km < 2:
                convenience += 15
            elif dist_km < 5:
                convenience += 10
            elif dist_km < 10:
                convenience += 5
            reasons.append(f"{dist_km:.1f} km away")

        if needs_pickup and garage.get("offers_pickup_drop"):
            pickup_radius = float(garage.get("pickup_radius_km", 0))
            if dist_km is None or dist_km <= pickup_radius:
                convenience += 15
                reasons.append("Offers pickup and drop")
        breakdown["convenience"] = min(convenience, self.MAX_CONVENIENCE)

        # Trust (15 pts)
        rating = float(garage.get("overall_rating", 4.0))
        trust = (rating / 5.0) * 10
        volume = garage.get("avg_vehicles_per_day", 0)
        if volume >= 15:
            trust += 5
        breakdown["trust"] = min(trust, self.MAX_TRUST)

        # Speed (15 pts)
        wait_days = garage.get("current_wait_time_days", 3)
        if wait_days == 0:
            speed = 15
            reasons.append("Available today")
        elif wait_days == 1:
            speed = 10
        else:
            speed = 0
        breakdown["speed"] = speed

        total = sum(breakdown.values())
        return GarageScore(
            garage_id=garage["garage_id"],
            garage_name=garage["garage_name"],
            total_score=total,
            breakdown=breakdown,
            match_reasons=reasons,
        )

    def _distance_km(
        self,
        lat1: float | None,
        lng1: float | None,
        lat2: float | None,
        lng2: float | None,
    ) -> float | None:
        if None in (lat1, lng1, lat2, lng2):
            return None
        r = 6371
        dlat = math.radians(float(lat2) - float(lat1))
        dlng = math.radians(float(lng2) - float(lng1))
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(float(lat1)))
            * math.cos(math.radians(float(lat2)))
            * math.sin(dlng / 2) ** 2
        )
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def rank(self, garages: list[dict], **kwargs) -> list[GarageScore]:
        scores = [self.score(g, **kwargs) for g in garages]
        return sorted(scores, key=lambda s: s.total_score, reverse=True)
