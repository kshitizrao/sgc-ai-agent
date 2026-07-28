from decimal import Decimal
from dataclasses import dataclass

from sgc_domain.pricing_calculator import DEPRECIATION_RATES


@dataclass
class LiabilityBreakdown:
    total_liability: Decimal
    deductible: Decimal
    depreciation_deductions: Decimal
    consumables_out_of_pocket: Decimal
    line_items: list[dict]
    explanation_parts: list[str]


class ClaimLiabilityEngine:
    """Deterministic insurance claim liability calculator."""

    CONSUMABLE_ESTIMATE = Decimal("800")

    def calculate(
        self,
        policy_type: str,
        compulsory_deductible: Decimal,
        consumables_cover: bool,
        line_items: list[dict],
    ) -> LiabilityBreakdown:
        deductible = Decimal(str(compulsory_deductible))
        depreciation_total = Decimal("0")
        consumables_oop = Decimal("0")
        explanation_parts: list[str] = []
        processed_items: list[dict] = []

        is_zero_dep = policy_type.lower().startswith("zero")

        for item in line_items:
            material = item.get("part_material", "Metal")
            approved = Decimal(str(item.get("surveyor_apprv_amount", 0)))
            liability = Decimal(str(item.get("customer_liability", 0)))
            action = item.get("surveyor_action", "Approved")

            if action == "Rejected":
                liability = Decimal(str(item.get("garage_est_amount", 0)))
                explanation_parts.append(
                    f"Rejected item '{item.get('part_id')}': customer pays full ₹{liability}"
                )
            elif not is_zero_dep and material in DEPRECIATION_RATES:
                dep_rate = DEPRECIATION_RATES[material]
                dep_amount = (approved * dep_rate).quantize(Decimal("0.01"))
                depreciation_total += dep_amount
                liability = dep_amount
                explanation_parts.append(
                    f"{material} part depreciated at {int(dep_rate * 100)}%: ₹{dep_amount}"
                )

            processed_items.append({
                "part_id": item.get("part_id"),
                "customer_liability": float(liability),
                "action": action,
            })

        if not consumables_cover:
            consumables_oop = self.CONSUMABLE_ESTIMATE
            explanation_parts.append(
                f"No consumables add-on: engine oil/coolant out-of-pocket ₹{consumables_oop}"
            )

        explanation_parts.append(f"Compulsory deductible: ₹{deductible}")

        total = deductible + depreciation_total + consumables_oop
        for item in processed_items:
            if item["action"] == "Rejected":
                total += Decimal(str(item["customer_liability"]))

        return LiabilityBreakdown(
            total_liability=total.quantize(Decimal("0.01")),
            deductible=deductible,
            depreciation_deductions=depreciation_total,
            consumables_out_of_pocket=consumables_oop,
            line_items=processed_items,
            explanation_parts=explanation_parts,
        )
