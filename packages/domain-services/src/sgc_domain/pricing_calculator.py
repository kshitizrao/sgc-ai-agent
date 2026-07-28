from decimal import Decimal
from dataclasses import dataclass


@dataclass
class CostBreakdown:
    labour: Decimal
    labour_gst: Decimal
    parts_total: Decimal
    consumables: Decimal
    total: Decimal
    line_items: list[dict]


DEPRECIATION_RATES = {
    "Plastic": Decimal("0.50"),
    "Rubber": Decimal("0.50"),
    "Glass": Decimal("0.00"),
    "Metal": Decimal("0.25"),
}


class PricingCalculator:
    """Deterministic service cost calculator — no LLM math."""

    LABOUR_GST = Decimal("0.18")

    def calculate_package_cost(
        self,
        labour_cost: Decimal,
        consumables_cost: Decimal,
        parts: list[dict] | None = None,
        mandatory_consumables_fee: Decimal = Decimal("150"),
    ) -> CostBreakdown:
        labour = Decimal(str(labour_cost))
        consumables = Decimal(str(consumables_cost))
        parts_total = Decimal("0")
        line_items = []

        for part in parts or []:
            qty = Decimal(str(part.get("quantity", 1)))
            price = Decimal(str(part.get("price", 0)))
            gst_pct = Decimal(str(part.get("gst_percent", 28))) / Decimal("100")
            part_total = price * qty * (Decimal("1") + gst_pct)
            parts_total += part_total
            line_items.append({
                "name": part.get("name", "Part"),
                "quantity": float(qty),
                "total": float(part_total.quantize(Decimal("0.01"))),
            })

        labour_gst = (labour * self.LABOUR_GST).quantize(Decimal("0.01"))
        consumables_fee = mandatory_consumables_fee
        total = labour + labour_gst + consumables + parts_total + consumables_fee

        return CostBreakdown(
            labour=labour,
            labour_gst=labour_gst,
            parts_total=parts_total,
            consumables=consumables + consumables_fee,
            total=total.quantize(Decimal("0.01")),
            line_items=line_items,
        )

    def calculate_repair_cost(
        self,
        base_cost: Decimal,
        segment_multiplier: Decimal = Decimal("1.0"),
    ) -> Decimal:
        return (Decimal(str(base_cost)) * segment_multiplier).quantize(Decimal("0.01"))
