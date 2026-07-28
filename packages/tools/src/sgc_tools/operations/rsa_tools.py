import math
from decimal import Decimal

from sqlalchemy import select

from sgc_db.models.operations import EmergencyRequest, EmergencyTriageRule, FieldResource
from sgc_domain.triage_engine import TriageEngine
from sgc_shared.types import SourceRef, ToolResult
from sgc_tools.registry import BaseTool


class TriageEmergencyTool(BaseTool):
    name = "triage_emergency"
    description = "Triage roadside emergency and determine dispatch action"

    async def execute(self, session, reported_issue, **kwargs):
        result = await session.execute(select(EmergencyTriageRule))
        rules = [
            {
                "symptom_id": r.symptom_id,
                "symptom_tags": r.symptom_tags or [],
                "severity_level": r.severity_level,
                "required_action": r.required_action,
                "safety_prompt": r.safety_prompt,
            }
            for r in result.scalars().all()
        ]
        engine = TriageEngine()
        triage = engine.triage(reported_issue, rules)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "symptom_id": triage.symptom_id,
                "severity_level": triage.severity_level,
                "required_action": triage.required_action,
                "safety_prompt": triage.safety_prompt,
                "confidence": triage.confidence,
                "requires_human_review": triage.requires_human_review,
                "clarifying_question": triage.clarifying_question,
            },
            source_refs=[SourceRef(table="operations.emergency_triage_rules", record_id=triage.symptom_id or "rule")],
        )


class DispatchResourceTool(BaseTool):
    name = "dispatch_resource"
    description = "Find nearest available tow truck or mobile mechanic"

    async def execute(self, session, required_action, customer_lat, customer_lng, **kwargs):
        resource_type_map = {
            "Tow_Truck": ["Flatbed_Tow", "Hydraulic_Tow"],
            "Mobile_Mechanic": ["Bike_Mechanic", "Mobile_Van"],
        }
        types = resource_type_map.get(required_action, [])

        result = await session.execute(
            select(FieldResource).where(FieldResource.availability_status == "Available")
        )
        resources = list(result.scalars().all())

        best = None
        best_dist = float("inf")
        for res in resources:
            if types and res.resource_type not in types:
                continue
            if res.current_lat and res.current_lng:
                dist = _haversine(
                    float(customer_lat), float(customer_lng),
                    float(res.current_lat), float(res.current_lng),
                )
                if dist < best_dist and dist <= float(res.max_operating_radius_km or 50):
                    best_dist = dist
                    best = res

        if not best:
            return ToolResult(tool_name=self.name, success=False, error="No available resources nearby")

        eta_mins = int(best_dist * 3)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "resource_id": best.resource_id,
                "resource_type": best.resource_type,
                "distance_km": round(best_dist, 1),
                "eta_minutes": eta_mins,
                "contact_number": best.contact_number,
            },
            source_refs=[SourceRef(table="operations.field_resources", record_id=best.resource_id)],
        )


class LogEmergencyRequestTool(BaseTool):
    name = "log_emergency_request"
    description = "Log an active emergency request for tracking"

    async def execute(self, session, request_id, reported_issue, customer_lat, customer_lng, ai_matched_symptom=None, **kwargs):
        req = EmergencyRequest(
            request_id=request_id,
            reported_issue=reported_issue,
            customer_lat=Decimal(str(customer_lat)),
            customer_lng=Decimal(str(customer_lng)),
            ai_matched_symptom=ai_matched_symptom,
            maps_pin_url=f"https://maps.google.com/?q={customer_lat},{customer_lng}",
            status="Dispatching",
        )
        session.add(req)
        await session.commit()
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"request_id": request_id, "status": "Dispatching"},
            source_refs=[SourceRef(table="operations.emergency_requests", record_id=request_id)],
        )


def _haversine(lat1, lng1, lat2, lng2) -> float:
    r = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
