import json
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from sgc_shared.constants import IntentType, TaskType
from sgc_shared.types import ContextEnvelope
from sgc_tools.registry import ToolRegistry


INTENT_TOOL_MAP: dict[IntentType, str] = {
    IntentType.PARTS: "search_parts",
    IntentType.SERVICES_PRICING: "compare_service_packages",
    IntentType.QUICK_SERVICE: "list_quick_services",
    IntentType.CLAIMS: "get_claim_status",
    IntentType.RSA: "triage_emergency",
    IntentType.GARAGE_MATCH: "recommend_garages",
    IntentType.DIAGNOSTICS: "diagnose_symptom",
    IntentType.VEHICLE_INFO: "fetch_pikpart_vehicle_details",
}


def _extract_amounts(data: dict | list | None) -> list[float]:
    amounts: list[float] = []
    if isinstance(data, dict):
        for key, val in data.items():
            if any(k in key for k in ("cost", "price", "total", "liability", "amount")):
                if isinstance(val, (int, float, Decimal)):
                    amounts.append(float(val))
            elif isinstance(val, (dict, list)):
                amounts.extend(_extract_amounts(val))
    elif isinstance(data, list):
        for item in data:
            amounts.extend(_extract_amounts(item))
    return amounts


async def execute_intent_tools(
    intent: IntentType,
    message: str,
    context: ContextEnvelope,
    registry: ToolRegistry,
    session: AsyncSession,
) -> tuple[list[dict], list[dict], list[float]]:
    tool_name = INTENT_TOOL_MAP.get(intent)
    if not tool_name:
        return [], [], []

    customer = context.customer
    kwargs: dict = {}

    if tool_name == "search_parts":
        kwargs = {
            "query": message,
            "make": customer.vehicle_make,
            "model": customer.vehicle_model,
            "fuel_type": customer.fuel_type,
        }
    elif tool_name == "estimate_service_cost":
        tool_name = "compare_service_packages"
        kwargs = {}
    elif tool_name == "list_quick_services":
        kwargs = {"symptom": message, "segment_id": "SEG-HATCH-PETROL"}
    elif tool_name == "get_claim_status":
        kwargs = {"vehicle_reg_no": customer.registration_no}
    elif tool_name == "triage_emergency":
        kwargs = {"reported_issue": message}
    elif tool_name == "recommend_garages":
        loc = context.location
        kwargs = {
            "service_category": "AC Repair" if "ac" in message.lower() else "Periodic Service",
            "vehicle_brand": customer.vehicle_make or "",
            "vehicle_model": customer.vehicle_model or "",
            "customer_lat": loc.latitude if loc else None,
            "customer_lng": loc.longitude if loc else None,
            "needs_pickup": "pickup" in message.lower(),
        }
    elif tool_name == "diagnose_symptom":
        kwargs = {
            "symptom_text": message,
            "vehicle_make": customer.vehicle_make,
            "vehicle_model": customer.vehicle_model,
            "fuel_type": customer.fuel_type,
            "mileage_km": customer.mileage_km,
        }
    elif tool_name == "fetch_pikpart_vehicle_details":
        import re
        match = re.search(r'[A-Z]{2}[0-9]{1,2}[A-Z0-9]{0,3}[0-9]{4}', message.replace(" ", "").upper())
        vehicle_num = match.group(0) if match else ""
        kwargs = {"vehicle_number": vehicle_num}

    result = await registry.invoke(tool_name, session, **kwargs)
    tool_data = {
        "tool_name": result.tool_name,
        "success": result.success,
        "data": result.data,
        "error": result.error,
    }
    refs = [r.model_dump() for r in result.source_refs]
    amounts = _extract_amounts(result.data)
    return [tool_data], refs, amounts


def format_tool_results_for_prompt(tool_results: list[dict]) -> str:
    if not tool_results:
        return "No tool data available."
    return json.dumps(tool_results, indent=2, default=str)
