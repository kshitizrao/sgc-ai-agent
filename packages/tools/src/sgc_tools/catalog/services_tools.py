from decimal import Decimal

from sqlalchemy import select

from sgc_db.models.catalog import AddOnRepair, QuickService, QuickServicePricing
from sgc_db.repositories.services import ServicesRepository
from sgc_domain.pricing_calculator import PricingCalculator
from sgc_shared.types import SourceRef, ToolResult
from sgc_tools.registry import BaseTool


class CompareServicePackagesTool(BaseTool):
    name = "compare_service_packages"
    description = "Compare Basic, Standard, and Comprehensive service packages"

    async def execute(self, session, **kwargs):
        repo = ServicesRepository(session)
        packages = await repo.get_packages()
        comparison = []
        for pkg in packages:
            inclusions = await repo.get_inclusions(pkg.package_id)
            comparison.append({
                "package_id": pkg.package_id,
                "package_name": pkg.package_name,
                "interval_km": pkg.interval_km,
                "description": pkg.package_description,
                "inclusions": {i.inclusion_key: i.inclusion_value for i in inclusions},
            })
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=comparison,
            source_refs=[SourceRef(table="catalog.service_packages", record_id=p["package_id"]) for p in comparison],
        )


class EstimateServiceCostTool(BaseTool):
    name = "estimate_service_cost"
    description = "Calculate service cost for a package and vehicle segment"

    async def execute(self, session, package_id, segment_id, **kwargs):
        repo = ServicesRepository(session)
        pricing = await repo.get_pricing(package_id, segment_id)
        if not pricing:
            return ToolResult(tool_name=self.name, success=False, error="Pricing not found for package/segment")

        calc = PricingCalculator()
        breakdown = calc.calculate_package_cost(
            labour_cost=Decimal(str(pricing.labour_cost)),
            consumables_cost=Decimal(str(pricing.consumables_cost)),
        )
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "package_id": package_id,
                "segment_id": segment_id,
                "labour_cost": float(breakdown.labour),
                "labour_gst": float(breakdown.labour_gst),
                "consumables": float(breakdown.consumables),
                "total": float(breakdown.total),
                "duration_hrs": float(pricing.service_duration_hrs) if pricing.service_duration_hrs else None,
            },
            source_refs=[SourceRef(table="catalog.pricing_matrix", record_id=pricing.pricing_id)],
        )


class EstimateRepairCostTool(BaseTool):
    name = "estimate_repair_cost"
    description = "Estimate cost for a specific repair based on symptoms and vehicle segment"

    async def execute(self, session, symptom=None, segment="Hatchback", **kwargs):
        result = await session.execute(select(AddOnRepair))
        repairs = list(result.scalars().all())
        matched = None
        if symptom:
            for repair in repairs:
                if any(symptom.lower() in tag.lower() for tag in (repair.symptom_tags or [])):
                    matched = repair
                    break

        if not matched and repairs:
            matched = repairs[0]

        if not matched:
            return ToolResult(tool_name=self.name, success=False, error="No matching repair found")

        cost_field = {
            "Hatchback": matched.cost_hatchback,
            "Sedan": matched.cost_sedan,
            "SUV": matched.cost_suv,
        }.get(segment, matched.cost_hatchback)

        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "repair_id": matched.repair_id,
                "repair_name": matched.repair_name,
                "estimated_cost": float(cost_field) if cost_field else None,
                "is_safety_critical": matched.is_safety_critical,
            },
            source_refs=[SourceRef(table="catalog.add_on_repairs", record_id=matched.repair_id)],
        )


class ListQuickServicesTool(BaseTool):
    name = "list_quick_services"
    description = "List 15-minute express quick services and pricing"

    async def execute(self, session, segment_id=None, symptom=None, **kwargs):
        qs_result = await session.execute(select(QuickService))
        services = list(qs_result.scalars().all())

        if symptom:
            services = [
                s for s in services
                if any(symptom.lower() in tag.lower() for tag in (s.symptom_tags or []))
            ]

        data = []
        for svc in services:
            entry = {
                "service_id": svc.service_id,
                "service_name": svc.service_name,
                "duration_mins": svc.duration_mins,
                "category": svc.service_category,
            }
            if segment_id:
                price_result = await session.execute(
                    select(QuickServicePricing).where(
                        QuickServicePricing.service_id == svc.service_id,
                        QuickServicePricing.segment_id == segment_id,
                    )
                )
                pricing = price_result.scalar_one_or_none()
                if pricing:
                    entry["total_cost"] = float(pricing.total_estimated_cost)
            data.append(entry)

        return ToolResult(
            tool_name=self.name,
            success=True,
            data=data,
            source_refs=[SourceRef(table="catalog.quick_services", record_id=d["service_id"]) for d in data],
        )
