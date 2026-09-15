"""SGC MCP Server — Read-only access to prod_pikpart tables via SSE.

This server exposes 11 MCP tools for querying 9 tables in the prod_pikpart
database.  **All access is strictly read-only** — every query passes through
the SQL guard before execution.

Run standalone::

    python -m sgc_mcp.server          # default port 8001
    SGC_MCP_PORT=9000 python -m sgc_mcp.server

The agent connects to this server over SSE at ``http://localhost:8001/sse``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)
from sqlalchemy import text
from starlette.applications import Starlette
from starlette.routing import Mount, Route
import uvicorn

from sgc_mcp.db import get_pikpart_session, dispose_pikpart_engine
from sgc_mcp.sql_guard import (
    SQLGuardError,
    validate_query,
    validate_table_name,
    MAX_RESULT_LIMIT,
)
from sgc_mcp.descriptions import TABLE_DESCRIPTIONS, COLUMN_DESCRIPTIONS

logger = logging.getLogger("agent.mcp.server")

# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------
mcp = Server("sgc-pikpart-mcp")


# ---------------------------------------------------------------------------
# Helper: execute a read-only query
# ---------------------------------------------------------------------------
async def _execute_readonly(sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    """Execute a validated SELECT query and return rows as dicts."""
    start = time.perf_counter()
    safe_sql = validate_query(sql)

    async for session in get_pikpart_session():
        result = await session.execute(text(safe_sql), params or {})
        rows = [dict(row._mapping) for row in result]
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "Query executed",
            extra={
                "query_preview": safe_sql[:120],
                "row_count": len(rows),
                "duration_ms": elapsed_ms,
            },
        )
        return rows
    return []


def _json_serial(obj: Any) -> str:
    """JSON serialiser for datetime and other non-standard types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__str__"):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def _format_result(rows: list[dict], tool_name: str) -> list[TextContent]:
    """Format query results as MCP TextContent."""
    if not rows:
        return [TextContent(type="text", text=f"No results found for {tool_name}.")]
    return [
        TextContent(
            type="text",
            text=json.dumps(rows, indent=2, default=_json_serial),
        )
    ]


# ═══════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """Return all available MCP tools."""
    return [
        # ── 1. lookup_customer ──────────────────────────────────────────
        Tool(
            name="lookup_customer",
            description=(
                "Find a customer by phone number, name, or customer ID. "
                "Returns customer profile with name, phone, vehicle type preference, "
                "business status, and activity info. "
                "Best lookup key is phone_number (10-digit Indian mobile)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "10-digit Indian mobile number to search",
                    },
                    "customer_id": {
                        "type": "integer",
                        "description": "Unique customer ID",
                    },
                    "name": {
                        "type": "string",
                        "description": "Customer name (partial match, case-insensitive)",
                    },
                },
            },
        ),
        # ── 2. get_customer_vehicles ────────────────────────────────────
        Tool(
            name="get_customer_vehicles",
            description=(
                "Get all vehicles registered to a customer. Returns vehicle_no "
                "(registration number), make (brand), model, fuel_type, engine_cc, "
                "insurance/pollution expiry dates, and next_service_date."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "Customer ID to look up vehicles for",
                    },
                    "vehicle_no": {
                        "type": "string",
                        "description": "Vehicle registration number (e.g., 'UP45W1315')",
                    },
                },
            },
        ),
        # ── 3. search_services ──────────────────────────────────────────
        Tool(
            name="search_services",
            description=(
                "Search the service catalog by name, vehicle type, fuel type, or "
                "service type. Returns service name, base_price, tier prices, "
                "GST rate, duration, and recommendations. "
                "Use vehicle_type='bike'/'scooty'/'car' and fuel_type='petrol'/'diesel'/'cng'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Service name to search (partial match)",
                    },
                    "vehicle_type": {
                        "type": "string",
                        "description": "Vehicle type: 'bike', 'scooty', or 'car'",
                    },
                    "fuel_type": {
                        "type": "string",
                        "description": "Fuel type: 'petrol', 'diesel', 'cng', 'electric'",
                    },
                    "is_quick": {
                        "type": "boolean",
                        "description": "True to filter for quick/express services only",
                    },
                    "serve_vehicle_type": {
                        "type": "string",
                        "description": "Vehicle category: '2W' or '4W'",
                    },
                },
            },
        ),
        # ── 4. get_service_price ────────────────────────────────────────
        Tool(
            name="get_service_price",
            description=(
                "Get the exact price of a service for a specific vehicle model. "
                "Queries the vehicle_services table (14.7M rows) which has per-model pricing. "
                "Returns price, discount_percent, tier_type, and transmission_type."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "integer",
                        "description": "Service ID from services table",
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Vehicle model name (e.g., 'WR-V', 'CITY IVTEC')",
                    },
                    "fuel_type": {
                        "type": "string",
                        "description": "Fuel type filter",
                    },
                    "tier_type": {
                        "type": "string",
                        "description": "Tier filter: 'tier1', 'tier2', 'tier3'",
                    },
                },
                "required": ["service_id"],
            },
        ),
        # ── 5. get_service_centre_services ──────────────────────────────
        Tool(
            name="get_service_centre_services",
            description=(
                "Find which service centres offer a specific service, optionally "
                "filtered by vehicle model. Returns service_centres_id, model_name, "
                "and engine CC range."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "integer",
                        "description": "Service ID to look up",
                    },
                    "service_centres_id": {
                        "type": "integer",
                        "description": "Specific service centre ID to check",
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Vehicle model name filter",
                    },
                },
            },
        ),
        # ── 6. get_bookings ─────────────────────────────────────────────
        Tool(
            name="get_bookings",
            description=(
                "Get bookings for a customer or vehicle. Returns booking status, "
                "price, payment_status, vehicle_no, service centre info, jobcard number, "
                "dates (booking, confirmed, service start/end). "
                "Status values: 'requested', 'confirmed', 'wip', 'completed', 'cancelled'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "Customer ID",
                    },
                    "vehicle_no": {
                        "type": "string",
                        "description": "Vehicle registration number",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status: 'requested'/'confirmed'/'wip'/'completed'/'cancelled'",
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "Customer phone number (bookings table has denormalized phone)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 20)",
                    },
                },
            },
        ),
        # ── 7. get_booking_services ─────────────────────────────────────
        Tool(
            name="get_booking_services",
            description=(
                "Get all services included in a specific booking. Returns service "
                "name, selling_price, status, item_type (Service/Package), "
                "customer_approval_status, discount, and tax_rate."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "integer",
                        "description": "Booking ID to look up services for",
                    },
                },
                "required": ["booking_id"],
            },
        ),
        # ── 8. list_vehicle_brands ──────────────────────────────────────
        Tool(
            name="list_vehicle_brands",
            description=(
                "List all vehicle brands (308 total). Optionally filter by "
                "vehicle_type or popularity. Returns brand name, Hindi name, "
                "fuel_type, and popularity flag."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vehicle_type": {
                        "type": "string",
                        "description": "Filter by vehicle type",
                    },
                    "is_popular": {
                        "type": "boolean",
                        "description": "True to show only popular brands",
                    },
                    "name": {
                        "type": "string",
                        "description": "Search by brand name (partial match)",
                    },
                },
            },
        ),
        # ── 9. list_vehicle_categories ──────────────────────────────────
        Tool(
            name="list_vehicle_categories",
            description=(
                "List vehicle categories: 2W (two-wheeler), 3W (three-wheeler), "
                "4W (four-wheeler). Small reference table with 3 rows."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # ── 10. find_services_for_vehicle (SMART) ───────────────────────
        Tool(
            name="find_services_for_vehicle",
            description=(
                "SMART TOOL: Given a vehicle registration number OR make/model, "
                "find all applicable services with prices. First looks up the vehicle "
                "in customer_vehicles, then joins with vehicle_services and services "
                "to get a complete service+price list. Very useful for answering "
                "'what services are available for my bike?' type queries."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vehicle_no": {
                        "type": "string",
                        "description": "Vehicle registration number",
                    },
                    "make": {
                        "type": "string",
                        "description": "Vehicle brand/make (e.g., 'Hero', 'TVS')",
                    },
                    "model": {
                        "type": "string",
                        "description": "Vehicle model (e.g., 'Splendor Plus')",
                    },
                    "fuel_type": {
                        "type": "string",
                        "description": "Fuel type filter",
                    },
                },
            },
        ),
        # ── 11. get_booking_history (SMART) ─────────────────────────────
        Tool(
            name="get_booking_history",
            description=(
                "SMART TOOL: Full booking history with services for a customer. "
                "Given a customer_id or phone_number, returns all bookings with "
                "their associated services, prices, and statuses. Perfect for "
                "'show me my past bookings' or 'meri pichli service kab hui thi?'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "Customer ID",
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "10-digit Indian mobile number",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max bookings to return (default 10)",
                    },
                },
            },
        ),
        # ── 12. fetch_pikpart_vehicle_details ───────────────────────────
        Tool(
            name="fetch_pikpart_vehicle_details",
            description=(
                "Fetch detailed vehicle information from Pikpart API using a vehicle registration number (e.g., DL10CT9251). "
                "Always use this when the customer provides a vehicle registration number."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vehicle_number": {
                        "type": "string",
                        "description": "Vehicle registration number",
                    },
                },
                "required": ["vehicle_number"],
            },
        ),
        # ── 13. fetch_pikpart_customer_service_details ─────────────────
        Tool(
            name="fetch_pikpart_customer_service_details",
            description=(
                "Fetch customer details, vehicle details, service types, garage details, service pricing, and discount against vehicle details. Supports customers with multiple vehicles. Requires phone number and service centre id. Optionally filter by vehicle_no."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "10-digit Indian mobile number",
                    },
                    "service_centre_id": {
                        "type": "integer",
                        "description": "ID of the service centre",
                    },
                    "vehicle_no": {
                        "type": "string",
                        "description": "Optional vehicle registration number to filter a specific vehicle if customer has multiple",
                    },
                },
                "required": ["phone_number", "service_centre_id"],
            },
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════

@mcp.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Route MCP tool calls to their implementations."""
    args = arguments or {}
    logger.info(
        f"[MCP Server] Tool call received: '{name}' | Handled in File: '{__file__}'", 
        extra={"tool": name, "tool_args": args, "file": __file__}
    )
    start = time.perf_counter()

    try:
        result = await _dispatch_tool(name, args)
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "Tool call completed",
            extra={"tool": name, "duration_ms": elapsed, "result_count": len(result)},
        )
        return result
    except SQLGuardError as e:
        logger.warning("SQL guard blocked query", extra={"tool": name, "error": str(e)})
        return [TextContent(type="text", text=f"Query blocked by safety guard: {e}")]
    except Exception as e:
        logger.error("Tool call failed", extra={"tool": name, "error": str(e)}, exc_info=True)
        return [TextContent(type="text", text=f"Error executing {name}: {e}")]


async def _dispatch_tool(name: str, args: dict[str, Any]) -> list[TextContent]:
    """Dispatch to the correct tool handler."""
    match name:
        case "lookup_customer":
            return await _lookup_customer(args)
        case "get_customer_vehicles":
            return await _get_customer_vehicles(args)
        case "search_services":
            return await _search_services(args)
        case "get_service_price":
            return await _get_service_price(args)
        case "get_service_centre_services":
            return await _get_service_centre_services(args)
        case "get_bookings":
            return await _get_bookings(args)
        case "get_booking_services":
            return await _get_booking_services(args)
        case "list_vehicle_brands":
            return await _list_vehicle_brands(args)
        case "list_vehicle_categories":
            return await _list_vehicle_categories(args)
        case "find_services_for_vehicle":
            return await _find_services_for_vehicle(args)
        case "get_booking_history":
            return await _get_booking_history(args)
        case "fetch_pikpart_vehicle_details":
            return await _fetch_pikpart_vehicle_details(args)
        case "fetch_pikpart_customer_service_details":
            return await _fetch_pikpart_customer_service_details(args)
        case _:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ---------------------------------------------------------------------------
# Individual tool handlers
# ---------------------------------------------------------------------------

async def _fetch_pikpart_customer_service_details(args: dict) -> list[TextContent]:
    phone_number = args.get("phone_number")
    service_centre_id = args.get("service_centre_id", 218)
    vehicle_no = args.get("vehicle_no")
    
    if not phone_number:
        return [TextContent(type="text", text="Please provide phone_number.")]
        
    veh_filter = f"AND LOWER(cv.vehicle_no) = LOWER('{vehicle_no}') " if vehicle_no else ""

    sql = (
        f"SELECT "
        f"c.id AS customer_id, "
        f"c.first_name || ' ' || COALESCE(c.last_name, '') AS customer_name, "
        f"c.phone_number, "
        f"cv.id AS customer_vehicle_id, "
        f"cv.vehicle_no, "
        f"cv.make, "
        f"cv.model AS customer_vehicle_model, "
        f"cv.fuel_type AS customer_fuel_type, "
        f"cv.vehicle_model_type, "
        f"vs.id AS vehicle_service_id, "
        f"s.id AS service_id, "
        f"s.name AS service_name, "
        f"s.service_code, "
        f"scat.name AS service_category, "
        f"vs.price AS base_price, "
        f"COALESCE(vs.discount_percent, 0) AS discount_percent, "
        f"ROUND((vs.price - (vs.price * COALESCE(vs.discount_percent, 0) / 100.0))::numeric, 2) AS discounted_price, "
        f"vs.tier_type, "
        f"vs.service_centre_id AS garage_id "
        f"FROM customers c "
        f"LEFT JOIN customer_vehicles cv "
        f"    ON cv.customer_id = c.id "
        f"   AND cv.is_active = true "
        f"   {veh_filter}"
        f"LEFT JOIN vehicle_services vs "
        f"    ON vs.service_centre_id = {int(service_centre_id)} "
        f"   AND vs.is_active = true "
        f"   AND ( "
        f"       vs.vehicle_model_id = cv.vehicle_id "
        f"       OR LOWER(vs.model_name) = LOWER(cv.model) "
        f"       OR vs.vehicle_model_id IS NULL "
        f"   ) "
        f"   AND ( "
        f"       vs.fuel_type IS NULL "
        f"       OR LOWER(vs.fuel_type) = LOWER(cv.fuel_type) "
        f"   ) "
        f"LEFT JOIN services s "
        f"    ON s.id = vs.service_id "
        f"   AND s.is_active = true "
        f"LEFT JOIN service_categories scat "
        f"    ON scat.id = vs.service_category_id "
        f"WHERE ( "
        f"    RIGHT(c.phone_number, 10) = RIGHT('{phone_number}', 10) "
        f"    OR RIGHT(c.alt_phone_number, 10) = RIGHT('{phone_number}', 10) "
        f") "
        f"ORDER BY cv.id, scat.name, s.name ASC"
    )
    rows = await _execute_readonly(sql)
    return _format_result(rows, "fetch_pikpart_customer_service_details")

async def _lookup_customer(args: dict) -> list[TextContent]:
    conditions = []
    if args.get("phone_number"):
        conditions.append(f"phone_number = '{args['phone_number']}'")
    if args.get("customer_id"):
        conditions.append(f"id = {int(args['customer_id'])}")
    if args.get("name"):
        conditions.append(f"LOWER(first_name) LIKE LOWER('%{args['name']}%')")

    if not conditions:
        return [TextContent(type="text", text="Please provide phone_number, customer_id, or name.")]

    where = " OR ".join(conditions)
    sql = (
        f"SELECT id, first_name, last_name, phone_number, email, "
        f"is_active, is_business, business_name, serve_vehicle_type, "
        f"resource_type, last_selected_vehicle_type, "
        f"\"createdAt\", last_login "
        f"FROM public.customers WHERE {where} LIMIT 10"
    )
    rows = await _execute_readonly(sql)
    return _format_result(rows, "lookup_customer")


async def _get_customer_vehicles(args: dict) -> list[TextContent]:
    conditions = []
    if args.get("customer_id"):
        conditions.append(f"customer_id = {int(args['customer_id'])}")
    if args.get("vehicle_no"):
        conditions.append(f"UPPER(vehicle_no) = UPPER('{args['vehicle_no']}')")

    if not conditions:
        return [TextContent(type="text", text="Please provide customer_id or vehicle_no.")]

    where = " AND ".join(conditions)
    sql = (
        f"SELECT id, customer_id, vehicle_no, make, model, fuel_type, "
        f"engine_cc, vehicle_type, vehicle_model_type, year, "
        f"insurance_expiry_date, pollution_expiry_date, next_service_date, "
        f"transmission_type, avg_daily_run, is_active "
        f"FROM public.customer_vehicles WHERE {where} AND is_active = true LIMIT 20"
    )
    rows = await _execute_readonly(sql)
    return _format_result(rows, "get_customer_vehicles")


async def _search_services(args: dict) -> list[TextContent]:
    conditions = ["is_active = true"]
    if args.get("name"):
        conditions.append(f"LOWER(name) LIKE LOWER('%{args['name']}%')")
    if args.get("vehicle_type"):
        conditions.append(f"vehicle_type = '{args['vehicle_type']}'")
    if args.get("fuel_type"):
        conditions.append(f"fuel_type = '{args['fuel_type']}'")
    if args.get("is_quick") is not None:
        conditions.append(f"is_quick = {args['is_quick']}")
    if args.get("serve_vehicle_type"):
        conditions.append(f"serve_vehicle_type = '{args['serve_vehicle_type']}'")

    where = " AND ".join(conditions)
    sql = (
        f"SELECT id, name, base_price, vehicle_type, fuel_type, "
        f"tier1_price, tier2_price, tier3_price, gst_rate, "
        f"service_duration, service_recommendation, serve_vehicle_type, "
        f"service_type, is_quick, model_name, service_code, discount "
        f"FROM public.services WHERE {where} "
        f"ORDER BY name LIMIT 30"
    )
    rows = await _execute_readonly(sql)
    return _format_result(rows, "search_services")


async def _get_service_price(args: dict) -> list[TextContent]:
    service_id = int(args["service_id"])
    conditions = [f"vs.service_id = {service_id}", "vs.is_active = true"]
    if args.get("model_name"):
        conditions.append(f"LOWER(vs.model_name) LIKE LOWER('%{args['model_name']}%')")
    if args.get("fuel_type"):
        conditions.append(f"vs.fuel_type = '{args['fuel_type']}'")
    if args.get("tier_type"):
        conditions.append(f"vs.tier_type = '{args['tier_type']}'")

    where = " AND ".join(conditions)
    sql = (
        f"SELECT vs.id, vs.model_name, vs.fuel_type, vs.transmission_type, "
        f"vs.price, vs.discount_percent, vs.tier_type, "
        f"s.name as service_name, s.gst_rate "
        f"FROM public.vehicle_services vs "
        f"JOIN public.services s ON s.id = vs.service_id "
        f"WHERE {where} LIMIT 30"
    )
    rows = await _execute_readonly(sql)
    return _format_result(rows, "get_service_price")


async def _get_service_centre_services(args: dict) -> list[TextContent]:
    conditions = ["scs.is_active = true"]
    if args.get("service_id"):
        conditions.append(f"scs.service_id = {int(args['service_id'])}")
    if args.get("service_centres_id"):
        conditions.append(f"scs.service_centres_id = {int(args['service_centres_id'])}")
    if args.get("model_name"):
        conditions.append(f"LOWER(scs.model_name) LIKE LOWER('%{args['model_name']}%')")

    if len(conditions) <= 1:
        return [TextContent(type="text", text="Please provide service_id, service_centres_id, or model_name.")]

    where = " AND ".join(conditions)
    sql = (
        f"SELECT scs.id, scs.service_id, scs.service_centres_id, "
        f"scs.model_name, scs.start_engine_cc, scs.end_engine_cc "
        f"FROM public.service_centre_services scs "
        f"WHERE {where} LIMIT 30"
    )
    rows = await _execute_readonly(sql)
    return _format_result(rows, "get_service_centre_services")


async def _get_bookings(args: dict) -> list[TextContent]:
    conditions = []
    if args.get("customer_id"):
        conditions.append(f"customer_id = {int(args['customer_id'])}")
    if args.get("vehicle_no"):
        conditions.append(f"UPPER(vehicle_no) = UPPER('{args['vehicle_no']}')")
    if args.get("status"):
        conditions.append(f"status = '{args['status']}'")
    if args.get("phone_number"):
        conditions.append(f"phone_number = '{args['phone_number']}'")

    if not conditions:
        return [TextContent(type="text", text="Please provide customer_id, vehicle_no, or phone_number.")]

    limit = min(int(args.get("limit", 20)), MAX_RESULT_LIMIT)
    where = " AND ".join(conditions)
    sql = (
        f"SELECT id, customer_id, customer_vehicle_id, service_centre_id, "
        f"status, price, payment_status, vehicle_no, "
        f"booking_datetime, first_name, phone_number, jobcard_number, "
        f"confirmed_date, service_start_date, service_end_date, "
        f"pickup_facility, drop_facility, is_quick, "
        f"created_by_user_name as service_centre_name, "
        f"cancel_reason, estimated_price, paid_total "
        f"FROM public.bookings WHERE {where} "
        f"ORDER BY \"createdAt\" DESC LIMIT {limit}"
    )
    rows = await _execute_readonly(sql)
    return _format_result(rows, "get_bookings")


async def _get_booking_services(args: dict) -> list[TextContent]:
    booking_id = int(args["booking_id"])
    sql = (
        f"SELECT bs.id, bs.booking_id, bs.service_id, bs.name, "
        f"bs.selling_price, bs.status, bs.item_type, "
        f"bs.customer_approval_status, bs.discount, bs.discount_percent, "
        f"bs.tax_rate, bs.qty, bs.checkpoint_name, "
        f"bs.approved_selling_price "
        f"FROM public.booking_services bs "
        f"WHERE bs.booking_id = {booking_id} "
        f"ORDER BY bs.id"
    )
    rows = await _execute_readonly(sql)
    return _format_result(rows, "get_booking_services")


async def _list_vehicle_brands(args: dict) -> list[TextContent]:
    conditions = []
    if args.get("vehicle_type"):
        conditions.append(f"vehicle_type = '{args['vehicle_type']}'")
    if args.get("is_popular"):
        conditions.append("is_popular = true")
    if args.get("name"):
        conditions.append(f"LOWER(name) LIKE LOWER('%{args['name']}%')")

    where = " AND ".join(conditions) if conditions else "1=1"
    sql = (
        f"SELECT id, name, name_hi, vehicle_type, fuel_type, "
        f"is_popular, priority "
        f"FROM public.vehicle_brands WHERE {where} "
        f"ORDER BY priority NULLS LAST, name LIMIT 50"
    )
    rows = await _execute_readonly(sql)
    return _format_result(rows, "list_vehicle_brands")


async def _list_vehicle_categories(args: dict) -> list[TextContent]:
    sql = "SELECT id, name, is_active FROM public.vehicle_categories ORDER BY id"
    rows = await _execute_readonly(sql)
    return _format_result(rows, "list_vehicle_categories")


async def _find_services_for_vehicle(args: dict) -> list[TextContent]:
    # Step 1: Find the vehicle
    vehicle_conditions = []
    if args.get("vehicle_no"):
        vehicle_conditions.append(f"UPPER(cv.vehicle_no) = UPPER('{args['vehicle_no']}')")
    if args.get("make"):
        vehicle_conditions.append(f"LOWER(cv.make) LIKE LOWER('%{args['make']}%')")
    if args.get("model"):
        vehicle_conditions.append(f"LOWER(cv.model) LIKE LOWER('%{args['model']}%')")

    if not vehicle_conditions:
        return [TextContent(type="text", text="Please provide vehicle_no, make, or model.")]

    veh_where = " AND ".join(vehicle_conditions)
    fuel_filter = f"AND vs.fuel_type = '{args['fuel_type']}'" if args.get("fuel_type") else ""

    sql = (
        f"SELECT DISTINCT s.id as service_id, s.name as service_name, "
        f"s.base_price, s.service_type, s.service_duration, "
        f"s.service_recommendation, s.gst_rate, s.is_quick, "
        f"vs.price as vehicle_specific_price, vs.tier_type, "
        f"cv.vehicle_no, cv.make, cv.model, cv.fuel_type "
        f"FROM public.customer_vehicles cv "
        f"LEFT JOIN public.vehicle_services vs ON LOWER(vs.model_name) = LOWER(cv.model) "
        f"AND vs.fuel_type = cv.fuel_type AND vs.is_active = true "
        f"LEFT JOIN public.services s ON s.id = vs.service_id AND s.is_active = true "
        f"WHERE {veh_where} AND cv.is_active = true {fuel_filter} "
        f"AND s.id IS NOT NULL "
        f"ORDER BY s.name LIMIT 50"
    )
    rows = await _execute_readonly(sql)

    if not rows:
        # Fallback: just return the vehicle info
        fallback_sql = (
            f"SELECT id, vehicle_no, make, model, fuel_type, engine_cc, vehicle_type "
            f"FROM public.customer_vehicles cv WHERE {veh_where} AND is_active = true LIMIT 5"
        )
        veh_rows = await _execute_readonly(fallback_sql)
        if veh_rows:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "message": "Vehicle found but no model-specific service pricing available. "
                               "Showing general services instead.",
                    "vehicle": veh_rows,
                }, indent=2, default=_json_serial),
            )]
        return [TextContent(type="text", text="No vehicle found matching the criteria.")]

    return _format_result(rows, "find_services_for_vehicle")


async def _get_booking_history(args: dict) -> list[TextContent]:
    # Step 1: Resolve customer_id from phone if needed
    customer_id = args.get("customer_id")
    if not customer_id and args.get("phone_number"):
        cust_sql = f"SELECT id FROM public.customers WHERE phone_number = '{args['phone_number']}' LIMIT 1"
        cust_rows = await _execute_readonly(cust_sql)
        if cust_rows:
            customer_id = cust_rows[0]["id"]
        else:
            return [TextContent(type="text", text=f"No customer found with phone {args['phone_number']}")]

    if not customer_id:
        return [TextContent(type="text", text="Please provide customer_id or phone_number.")]

    limit = min(int(args.get("limit", 10)), 20)

    # Step 2: Get bookings with their services
    sql = (
        f"SELECT b.id as booking_id, b.booking_datetime, b.status, "
        f"b.price as total_price, b.payment_status, b.vehicle_no, "
        f"b.first_name, b.phone_number, b.jobcard_number, "
        f"b.service_start_date, b.service_end_date, "
        f"b.created_by_user_name as service_centre_name, "
        f"bs.name as service_name, bs.selling_price as service_price, "
        f"bs.status as service_status, bs.item_type "
        f"FROM public.bookings b "
        f"LEFT JOIN public.booking_services bs ON bs.booking_id = b.id "
        f"WHERE b.customer_id = {int(customer_id)} "
        f"ORDER BY b.\"createdAt\" DESC LIMIT {limit * 5}"
    )
    rows = await _execute_readonly(sql)
    return _format_result(rows, "get_booking_history")


async def _fetch_pikpart_vehicle_details(args: dict) -> list[TextContent]:
    vehicle_number = args.get("vehicle_number")
    if not vehicle_number:
        return [TextContent(type="text", text="Please provide vehicle_number.")]

    url = "https://uatapi.pikpart.com/api/Customer/searchVehicles"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"object_hash": {"vehicle_number": vehicle_number}})
            response.raise_for_status()
            data = response.json()
        return [TextContent(type="text", text=json.dumps(data, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Failed to fetch vehicle details from API: {e}")]


# ═══════════════════════════════════════════════════════════════════════════
# SSE Server Setup
# ═══════════════════════════════════════════════════════════════════════════

def create_app() -> Starlette:
    """Create the Starlette app with SSE transport for MCP."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(scope, receive, send):
        async with sse.connect_sse(
            scope, receive, send
        ) as streams:
            await mcp.run(
                streams[0], streams[1], mcp.create_initialization_options()
            )

    app = Starlette(
        debug=True,
        routes=[
            Mount("/sse/messages/", app=sse.handle_post_message),
            Mount("/sse", app=handle_sse),
        ],
    )

    return app


def main():
    """Entry point — run the MCP server as an SSE HTTP server."""
    port = int(os.environ.get("SGC_MCP_PORT", "8001"))
    host = os.environ.get("SGC_MCP_HOST", "0.0.0.0")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)-30s | %(levelname)-5s | %(message)s",
    )
    logger.info("Starting SGC MCP Server on %s:%d (SSE transport)", host, port)

    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
