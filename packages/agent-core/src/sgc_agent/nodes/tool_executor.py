"""Tool executor — routes intents to the right tool implementation.

For ``PIKPART_QUERY`` intents, the executor uses the MCP client and an LLM
query planner to decide which MCP tools to call and with what parameters.
"""

from __future__ import annotations

import json
import logging
import time
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from sgc_shared.constants import IntentType, TaskType
from sgc_shared.types import ContextEnvelope
from sgc_tools.registry import ToolRegistry

logger = logging.getLogger("agent.tool_executor")

# ── Legacy intent → tool mapping (for non-MCP intents) ─────────────────
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


async def execute_pikpart_query(
    message: str,
    context: ContextEnvelope,
    llm_router,
    session_id: str | None = None,
) -> tuple[list[dict], list[dict], list[float]]:
    """Execute a PIKPART_QUERY intent via MCP tools.

    Uses an LLM query planner to decide which MCP tools to call, then
    executes them and returns the aggregated results.
    """
    from sgc_agent.mcp_client import get_mcp_client
    from sgc_agent.persona.system_prompts import QUERY_PLANNER_PROMPT

    start = time.perf_counter()
    mcp_client = await get_mcp_client()
    tools_desc = mcp_client.get_tools_description()

    # ── Step 1: Ask LLM to plan the query ──────────────────────────────
    planner_prompt = QUERY_PLANNER_PROMPT.format(tools_description=tools_desc)
    customer = context.customer

    # Build context string for the planner
    context_parts = []
    if customer.customer_id:
        context_parts.append(f"Known customer_id: {customer.customer_id}")
    if customer.registration_no:
        context_parts.append(f"Vehicle registration: {customer.registration_no}")
    if customer.vehicle_make:
        context_parts.append(f"Vehicle make: {customer.vehicle_make}")
    if customer.vehicle_model:
        context_parts.append(f"Vehicle model: {customer.vehicle_model}")

    context_str = "\n".join(context_parts) if context_parts else "No prior context available."

    planner_messages = [
        {"role": "system", "content": planner_prompt},
        {"role": "user", "content": (
            f"Customer context:\n{context_str}\n\n"
            f"Customer message: {message}"
        )},
    ]

    try:
        plan_response = await llm_router.complete(planner_messages, task=TaskType.TOOL_NLG)
        plan_raw = plan_response.content.strip()

        # Extract JSON from the response (handle markdown code blocks)
        if "```json" in plan_raw:
            plan_raw = plan_raw.split("```json")[1].split("```")[0].strip()
        elif "```" in plan_raw:
            plan_raw = plan_raw.split("```")[1].split("```")[0].strip()

        plan = json.loads(plan_raw)
        logger.info(
            "Query plan created",
            extra={
                "session_id": session_id,
                "tool_calls": [tc["tool"] for tc in plan.get("tool_calls", [])],
                "missing_info": plan.get("missing_info"),
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            },
        )

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(
            "Query planner failed, attempting direct tool inference",
            extra={"error": str(e), "session_id": session_id},
        )
        # Fallback: try to infer the tool from the message
        plan = _infer_tool_from_message(message, context)

    # ── Step 2: Handle missing info ────────────────────────────────────
    missing = plan.get("missing_info")
    if missing and not plan.get("tool_calls"):
        return [
            {
                "tool_name": "query_planner",
                "success": True,
                "data": {"missing_info": missing},
            }
        ], [], []

    # ── Step 3: Execute MCP tool calls ─────────────────────────────────
    all_results = []
    all_refs = []
    all_amounts = []

    for tc in plan.get("tool_calls", []):
        tool_name = tc.get("tool", "")
        tool_args = tc.get("arguments", {})

        logger.info(
            "Executing MCP tool",
            extra={
                "session_id": session_id,
                "tool": tool_name,
                "tool_args": tool_args,
            },
        )

        result = await mcp_client.call_tool(tool_name, tool_args)
        all_results.append(result)

        if result.get("data"):
            amounts = _extract_amounts(result["data"])
            all_amounts.extend(amounts)

    elapsed = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "PIKPART_QUERY execution completed",
        extra={
            "session_id": session_id,
            "tools_called": len(all_results),
            "total_duration_ms": elapsed,
        },
    )

    return all_results, all_refs, all_amounts


def _infer_tool_from_message(message: str, context: ContextEnvelope) -> dict:
    """Simple heuristic fallback to infer MCP tool from the message."""
    lowered = message.lower()
    customer = context.customer

    # Phone number detection
    import re
    phone_match = re.search(r'\b[6-9]\d{9}\b', message)
    vehicle_match = re.search(r'\b[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{4}\b', message.upper().replace(" ", ""))

    if phone_match:
        phone = phone_match.group(0)
        if any(w in lowered for w in ["booking", "history", "pichli", "service kab"]):
            return {"tool_calls": [{"tool": "get_booking_history", "arguments": {"phone_number": phone}}]}
        return {"tool_calls": [{"tool": "lookup_customer", "arguments": {"phone_number": phone}}]}

    if vehicle_match:
        veh_no = vehicle_match.group(0)
        if any(w in lowered for w in ["service", "price", "seva", "kitna"]):
            return {"tool_calls": [{"tool": "find_services_for_vehicle", "arguments": {"vehicle_no": veh_no}}]}
        return {"tool_calls": [{"tool": "get_customer_vehicles", "arguments": {"vehicle_no": veh_no}}]}

    if any(w in lowered for w in ["booking", "bukking", "status"]):
        if customer.customer_id:
            return {"tool_calls": [{"tool": "get_bookings", "arguments": {"customer_id": int(customer.customer_id)}}]}
        return {"tool_calls": [], "missing_info": "Aapka phone number ya booking ID share kar dijiye."}

    if any(w in lowered for w in ["brand", "company", "kaun si"]):
        return {"tool_calls": [{"tool": "list_vehicle_brands", "arguments": {}}]}

    if any(w in lowered for w in ["category", "type", "prakar"]):
        return {"tool_calls": [{"tool": "list_vehicle_categories", "arguments": {}}]}

    if any(w in lowered for w in ["service", "seva", "price", "kitna"]):
        if customer.vehicle_model:
            return {"tool_calls": [{"tool": "find_services_for_vehicle", "arguments": {"model": customer.vehicle_model}}]}
        return {"tool_calls": [{"tool": "search_services", "arguments": {}}]}

    return {"tool_calls": [], "missing_info": "Aap kya jaanna chahte hain? Please thoda detail mein batayein."}


async def execute_intent_tools(
    intent: IntentType,
    message: str,
    context: ContextEnvelope,
    registry: ToolRegistry,
    session: AsyncSession,
) -> tuple[list[dict], list[dict], list[float]]:
    """Execute tools based on classified intent.

    For PIKPART_QUERY, routes to MCP. For other intents, uses the legacy
    tool registry.
    """
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
