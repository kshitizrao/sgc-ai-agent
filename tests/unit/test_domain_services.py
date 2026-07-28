from decimal import Decimal

from sgc_domain.claim_liability_engine import ClaimLiabilityEngine
from sgc_domain.garage_scorer import GarageScorer
from sgc_domain.pricing_calculator import PricingCalculator
from sgc_domain.triage_engine import TriageEngine


def test_pricing_calculator():
    calc = PricingCalculator()
    result = calc.calculate_package_cost(
        labour_cost=Decimal("1200"),
        consumables_cost=Decimal("2300"),
    )
    assert result.total == Decimal("3866.00")


def test_claim_liability_comprehensive():
    engine = ClaimLiabilityEngine()
    result = engine.calculate(
        policy_type="Comprehensive",
        compulsory_deductible=Decimal("1000"),
        consumables_cover=False,
        line_items=[
            {
                "part_id": "PRT-BUMPER",
                "part_material": "Plastic",
                "surveyor_apprv_amount": 5500,
                "surveyor_action": "Approved",
                "customer_liability": 0,
            }
        ],
    )
    assert result.total_liability > Decimal("1000")
    assert len(result.explanation_parts) > 0


def test_garage_scorer():
    scorer = GarageScorer()
    garage = {
        "garage_id": "GRG-1",
        "garage_name": "Euro Motors",
        "location_lat": 28.6139,
        "location_lng": 77.2090,
        "overall_rating": 4.6,
        "top_brands_serviced": ["Volkswagen"],
        "top_models_serviced": ["Polo"],
        "specialization_tag": "German Car Expert",
        "avg_vehicles_per_day": 15,
        "current_wait_time_days": 1,
        "offers_pickup_drop": True,
        "pickup_radius_km": 10,
    }
    score = scorer.score(garage, 28.6140, 77.2095, "Volkswagen", "Polo", needs_pickup=True)
    assert score.total_score > 50
    assert "Volkswagen" in " ".join(score.match_reasons)


def test_triage_engine_high_severity():
    engine = TriageEngine()
    result = engine.triage("I hit a divider and there is smoke", [])
    assert result.severity_level == "High"
    assert result.requires_human_review


def test_triage_engine_puncture():
    engine = TriageEngine()
    rules = [{"symptom_id": "SYM-PUNCTURE", "symptom_tags": ["flat tyre", "puncture"], "severity_level": "Low", "required_action": "Mobile_Mechanic", "safety_prompt": "Stay safe."}]
    result = engine.triage("I have a flat tyre", rules)
    assert result.required_action == "Mobile_Mechanic"
