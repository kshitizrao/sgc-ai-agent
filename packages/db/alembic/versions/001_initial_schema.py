"""Initial schema migration."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMAS = ["catalog", "operations", "marketplace", "diagnostics", "agent_meta", "governance", "sync"]


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    op.create_table(
        "parts",
        sa.Column("part_id", sa.String(32), primary_key=True),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("oem_part_number", sa.String(64)),
        sa.Column("manufacturer_part_number", sa.String(64)),
        sa.Column("part_name", sa.String(256), nullable=False),
        sa.Column("category", sa.String(64)),
        sa.Column("sub_category", sa.String(64)),
        sa.Column("part_brand", sa.String(64)),
        sa.Column("part_type", sa.String(32)),
        sa.Column("condition", sa.String(32)),
        sa.Column("warranty_months", sa.Integer()),
        sa.Column("stock_quantity", sa.Integer()),
        sa.Column("reorder_level", sa.Integer()),
        sa.Column("bin_location", sa.String(64)),
        sa.Column("supplier_name", sa.String(128)),
        sa.Column("cost_price", sa.Numeric(12, 2)),
        sa.Column("selling_price", sa.Numeric(12, 2)),
        sa.Column("labour_code", sa.String(32)),
        sa.Column("gst_slab", sa.Numeric(5, 2)),
        sa.Column("search_tags", postgresql.ARRAY(sa.String())),
        sa.Column("installation_notes", sa.Text()),
        sa.Column("embedding", sa.Text()),
        schema="catalog",
    )
    op.create_index("ix_parts_sku", "parts", ["sku"], schema="catalog")
    op.create_index("ix_parts_oem", "parts", ["oem_part_number"], schema="catalog")

    op.create_table(
        "part_fitment",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("part_id", sa.String(32), sa.ForeignKey("catalog.parts.part_id")),
        sa.Column("vehicle_make", sa.String(64), nullable=False),
        sa.Column("vehicle_model", sa.String(64), nullable=False),
        sa.Column("vehicle_variant", sa.String(64)),
        sa.Column("fuel_type", sa.String(32)),
        sa.Column("transmission_type", sa.String(32)),
        sa.Column("year_from", sa.Integer()),
        sa.Column("year_to", sa.Integer()),
        schema="catalog",
    )
    op.create_index("ix_fitment_vehicle", "part_fitment", ["vehicle_make", "vehicle_model", "fuel_type"], schema="catalog")

    op.create_table(
        "part_interchanges",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("part_id", sa.String(32), sa.ForeignKey("catalog.parts.part_id")),
        sa.Column("alternate_part_id", sa.String(32), sa.ForeignKey("catalog.parts.part_id")),
        sa.Column("notes", sa.Text()),
        schema="catalog",
    )

    op.create_table(
        "vehicle_segments",
        sa.Column("segment_id", sa.String(32), primary_key=True),
        sa.Column("body_type", sa.String(64), nullable=False),
        sa.Column("fuel_type", sa.String(32), nullable=False),
        sa.Column("engine_oil_capacity", sa.Numeric(5, 2)),
        sa.Column("description", sa.Text()),
        schema="catalog",
    )

    op.create_table(
        "service_packages",
        sa.Column("package_id", sa.String(32), primary_key=True),
        sa.Column("package_name", sa.String(128), nullable=False),
        sa.Column("interval_km", sa.Integer()),
        sa.Column("interval_months", sa.Integer()),
        sa.Column("package_description", sa.Text()),
        schema="catalog",
    )

    op.create_table(
        "service_inclusions",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("package_id", sa.String(32), sa.ForeignKey("catalog.service_packages.package_id")),
        sa.Column("inclusion_key", sa.String(64), nullable=False),
        sa.Column("inclusion_value", sa.String(128), nullable=False),
        schema="catalog",
    )

    op.create_table(
        "pricing_matrix",
        sa.Column("pricing_id", sa.String(32), primary_key=True),
        sa.Column("package_id", sa.String(32), sa.ForeignKey("catalog.service_packages.package_id")),
        sa.Column("segment_id", sa.String(32), sa.ForeignKey("catalog.vehicle_segments.segment_id")),
        sa.Column("labour_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("consumables_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_estimated_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("service_duration_hrs", sa.Numeric(5, 2)),
        schema="catalog",
    )

    op.create_table(
        "add_on_repairs",
        sa.Column("repair_id", sa.String(32), primary_key=True),
        sa.Column("repair_name", sa.String(256), nullable=False),
        sa.Column("symptom_tags", postgresql.ARRAY(sa.String())),
        sa.Column("cost_hatchback", sa.Numeric(12, 2)),
        sa.Column("cost_sedan", sa.Numeric(12, 2)),
        sa.Column("cost_suv", sa.Numeric(12, 2)),
        sa.Column("is_safety_critical", sa.Boolean()),
        schema="catalog",
    )

    op.create_table(
        "quick_services",
        sa.Column("service_id", sa.String(32), primary_key=True),
        sa.Column("service_name", sa.String(128), nullable=False),
        sa.Column("service_category", sa.String(64)),
        sa.Column("duration_mins", sa.Integer()),
        sa.Column("symptom_tags", postgresql.ARRAY(sa.String())),
        sa.Column("action_type", sa.String(64)),
        schema="catalog",
    )

    op.create_table(
        "quick_service_pricing",
        sa.Column("pricing_id", sa.String(32), primary_key=True),
        sa.Column("service_id", sa.String(32), sa.ForeignKey("catalog.quick_services.service_id")),
        sa.Column("segment_id", sa.String(32), sa.ForeignKey("catalog.vehicle_segments.segment_id")),
        sa.Column("labour_cost", sa.Numeric(12, 2)),
        sa.Column("consumables_cost", sa.Numeric(12, 2)),
        sa.Column("total_estimated_cost", sa.Numeric(12, 2)),
        schema="catalog",
    )

    op.create_table(
        "service_master",
        sa.Column("service_id", sa.String(32), primary_key=True),
        sa.Column("service_name", sa.String(256), nullable=False),
        sa.Column("service_category", sa.String(64)),
        sa.Column("standard_labor_hours", sa.Numeric(5, 2)),
        sa.Column("is_package", sa.Boolean()),
        schema="catalog",
    )

    op.create_table(
        "labor_cost_matrix",
        sa.Column("labor_rate_id", sa.String(32), primary_key=True),
        sa.Column("service_id", sa.String(32), sa.ForeignKey("catalog.service_master.service_id")),
        sa.Column("vehicle_segment", sa.String(64), nullable=False),
        sa.Column("base_labor_cost_inr", sa.Numeric(12, 2)),
        sa.Column("labor_gst_percent", sa.Numeric(5, 2)),
        sa.Column("total_labor_cost_inc_tax", sa.Numeric(12, 2)),
        schema="catalog",
    )

    op.create_table(
        "service_parts_bom",
        sa.Column("bom_id", sa.String(32), primary_key=True),
        sa.Column("service_id", sa.String(32), sa.ForeignKey("catalog.service_master.service_id")),
        sa.Column("variant_id", sa.String(64)),
        sa.Column("part_id", sa.String(32), sa.ForeignKey("catalog.parts.part_id")),
        sa.Column("required_quantity", sa.Numeric(10, 2)),
        sa.Column("unit_of_measure", sa.String(32)),
        schema="catalog",
    )

    op.create_table(
        "parts_cost_master",
        sa.Column("part_cost_id", sa.String(32), primary_key=True),
        sa.Column("part_id", sa.String(32), sa.ForeignKey("catalog.parts.part_id")),
        sa.Column("part_grade_type", sa.String(32)),
        sa.Column("part_mrp_inr", sa.Numeric(12, 2)),
        sa.Column("garage_purchase_cost_inr", sa.Numeric(12, 2)),
        sa.Column("part_gst_percent", sa.Numeric(5, 2)),
        sa.Column("selling_price_excl_tax", sa.Numeric(12, 2)),
        schema="catalog",
    )

    op.create_table(
        "auxiliary_charges",
        sa.Column("aux_charge_id", sa.String(32), primary_key=True),
        sa.Column("charge_name", sa.String(128), nullable=False),
        sa.Column("calculation_type", sa.String(32)),
        sa.Column("charge_value", sa.Numeric(12, 2)),
        sa.Column("aux_gst_percent", sa.Numeric(5, 2)),
        sa.Column("is_mandatory", sa.Boolean()),
        schema="catalog",
    )

    # Operations
    op.create_table(
        "claims",
        sa.Column("claim_id", sa.String(32), primary_key=True),
        sa.Column("vehicle_reg_no", sa.String(32)),
        sa.Column("insurance_provider", sa.String(128)),
        sa.Column("claim_type", sa.String(32)),
        sa.Column("incident_date", sa.DateTime()),
        sa.Column("intimation_date", sa.DateTime()),
        sa.Column("claim_status", sa.String(64)),
        sa.Column("surveyor_name", sa.String(128)),
        sa.Column("surveyor_contact", sa.String(32)),
        sa.Column("symptom_tags", postgresql.ARRAY(sa.String())),
        schema="operations",
    )

    op.create_table(
        "policy_rules",
        sa.Column("policy_id", sa.String(32), primary_key=True),
        sa.Column("vehicle_reg_no", sa.String(32)),
        sa.Column("policy_type", sa.String(64)),
        sa.Column("compulsory_deductible", sa.Numeric(12, 2)),
        sa.Column("consumables_cover_addon", sa.Boolean()),
        sa.Column("engine_protect_addon", sa.Boolean()),
        sa.Column("salvage_value_logic", sa.Numeric(5, 2)),
        schema="operations",
    )

    op.create_table(
        "claim_line_items",
        sa.Column("estimate_line_id", sa.String(32), primary_key=True),
        sa.Column("claim_id", sa.String(32), sa.ForeignKey("operations.claims.claim_id")),
        sa.Column("part_id", sa.String(32)),
        sa.Column("part_material", sa.String(32)),
        sa.Column("garage_est_amount", sa.Numeric(12, 2)),
        sa.Column("surveyor_apprv_amount", sa.Numeric(12, 2)),
        sa.Column("surveyor_action", sa.String(32)),
        sa.Column("rejection_reason", sa.Text()),
        sa.Column("customer_liability", sa.Numeric(12, 2)),
        schema="operations",
    )

    op.create_table(
        "emergency_triage_rules",
        sa.Column("symptom_id", sa.String(32), primary_key=True),
        sa.Column("symptom_tags", postgresql.ARRAY(sa.String())),
        sa.Column("severity_level", sa.String(16)),
        sa.Column("required_action", sa.String(32)),
        sa.Column("safety_prompt", sa.Text()),
        schema="operations",
    )

    op.create_table(
        "emergency_requests",
        sa.Column("request_id", sa.String(32), primary_key=True),
        sa.Column("customer_vehicle_id", sa.String(32)),
        sa.Column("reported_issue", sa.Text()),
        sa.Column("ai_matched_symptom", sa.String(32)),
        sa.Column("customer_lat", sa.Numeric(10, 7)),
        sa.Column("customer_lng", sa.Numeric(10, 7)),
        sa.Column("maps_pin_url", sa.String(512)),
        sa.Column("status", sa.String(32)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        schema="operations",
    )

    op.create_table(
        "field_resources",
        sa.Column("resource_id", sa.String(32), primary_key=True),
        sa.Column("resource_type", sa.String(32)),
        sa.Column("current_lat", sa.Numeric(10, 7)),
        sa.Column("current_lng", sa.Numeric(10, 7)),
        sa.Column("availability_status", sa.String(16)),
        sa.Column("max_operating_radius_km", sa.Numeric(6, 2)),
        sa.Column("contact_number", sa.String(32)),
        schema="operations",
    )

    # Marketplace
    for tbl, cols in [
        ("garages", [
            ("garage_id", sa.String(32), True),
            ("garage_name", sa.String(256), False),
            ("location_lat", sa.Numeric(10, 7), False),
            ("location_lng", sa.Numeric(10, 7), False),
            ("address_area", sa.String(128), False),
            ("overall_rating", sa.Numeric(3, 2), False),
            ("standard_labor_rate", sa.Numeric(12, 2), False),
        ]),
    ]:
        op.create_table(
            tbl,
            *[sa.Column(c[0], c[1], primary_key=c[2], nullable=not c[2] and c[0] != "garage_id") for c in cols],
            schema="marketplace",
        )

    op.create_table(
        "garage_capabilities",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("garage_id", sa.String(32), nullable=False),
        sa.Column("service_categories", postgresql.ARRAY(sa.String())),
        sa.Column("cashless_insurance_tieups", postgresql.ARRAY(sa.String())),
        sa.Column("has_paint_booth", sa.Boolean()),
        sa.Column("has_oem_scanner", sa.Boolean()),
        schema="marketplace",
    )

    op.create_table(
        "garage_analytics",
        sa.Column("garage_id", sa.String(32), primary_key=True),
        sa.Column("avg_vehicles_per_day", sa.Integer()),
        sa.Column("top_brands_serviced", postgresql.ARRAY(sa.String())),
        sa.Column("top_models_serviced", postgresql.ARRAY(sa.String())),
        sa.Column("specialization_tag", sa.String(128)),
        sa.Column("current_wait_time_days", sa.Integer()),
        schema="marketplace",
    )

    op.create_table(
        "garage_experience",
        sa.Column("garage_id", sa.String(32), primary_key=True),
        sa.Column("offers_pickup_drop", sa.Boolean()),
        sa.Column("pickup_radius_km", sa.Numeric(6, 2)),
        sa.Column("has_customer_lounge", sa.Boolean()),
        sa.Column("provides_warranty", sa.String(128)),
        sa.Column("live_video_feed", sa.Boolean()),
        schema="marketplace",
    )

    # Diagnostics
    op.create_table(
        "vehicle_issues",
        sa.Column("issue_id", sa.String(32), primary_key=True),
        sa.Column("issue_name", sa.String(256), nullable=False),
        sa.Column("system_category", sa.String(64)),
        sa.Column("severity_level", sa.String(16)),
        sa.Column("is_safety_risk", sa.Boolean()),
        sa.Column("standard_obd2_code", sa.String(16)),
        sa.Column("resolution_service_id", sa.String(32)),
        schema="diagnostics",
    )

    op.create_table(
        "predictive_failure_matrix",
        sa.Column("prediction_id", sa.String(32), primary_key=True),
        sa.Column("issue_id", sa.String(32), nullable=False),
        sa.Column("vehicle_make", sa.String(64)),
        sa.Column("vehicle_model", sa.String(64)),
        sa.Column("fuel_type", sa.String(32)),
        sa.Column("risk_start_km", sa.Integer()),
        sa.Column("risk_end_km", sa.Integer()),
        sa.Column("risk_start_age_months", sa.Integer()),
        sa.Column("probability_score", sa.String(16)),
        schema="diagnostics",
    )

    op.create_table(
        "symptom_mapping",
        sa.Column("symptom_id", sa.String(32), primary_key=True),
        sa.Column("issue_id", sa.String(32), nullable=False),
        sa.Column("customer_keywords", postgresql.ARRAY(sa.String())),
        sa.Column("sensory_category", sa.String(32)),
        sa.Column("ai_diagnostic_question", sa.Text()),
        schema="diagnostics",
    )

    # Agent meta
    op.create_table(
        "conversations",
        sa.Column("session_id", sa.String(64), primary_key=True),
        sa.Column("customer_id", sa.String(64)),
        sa.Column("vehicle_id", sa.String(64)),
        sa.Column("context_snapshot", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        schema="agent_meta",
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_refs", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        schema="agent_meta",
    )

    op.create_table(
        "tool_invocations",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("input_payload", postgresql.JSONB()),
        sa.Column("output_payload", postgresql.JSONB()),
        sa.Column("success", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        schema="agent_meta",
    )

    op.create_table(
        "customer_context_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("customer_id", sa.String(64)),
        sa.Column("vehicle_id", sa.String(64)),
        sa.Column("context_data", postgresql.JSONB()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        schema="agent_meta",
    )

    # Governance
    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("policy_name", sa.String(128), unique=True, nullable=False),
        sa.Column("policy_type", sa.String(64)),
        sa.Column("rules", postgresql.JSONB()),
        sa.Column("is_active", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        schema="governance",
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("prompt_key", sa.String(64), nullable=False),
        sa.Column("version", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        schema="governance",
    )

    op.create_table(
        "guardrail_events",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("session_id", sa.String(64)),
        sa.Column("event_type", sa.String(64)),
        sa.Column("model_used", sa.String(128)),
        sa.Column("prompt_version", sa.String(16)),
        sa.Column("tools_called", postgresql.JSONB()),
        sa.Column("decision", sa.String(32)),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        schema="governance",
    )

    # Sync
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("source_name", sa.String(128), nullable=False),
        sa.Column("job_type", sa.String(64)),
        sa.Column("status", sa.String(32)),
        sa.Column("records_processed", sa.Integer()),
        sa.Column("error_log", sa.Text()),
        sa.Column("job_metadata", postgresql.JSONB()),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime()),
        schema="sync",
    )

    op.create_table(
        "source_mappings",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("backend_system", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("backend_field", sa.String(128)),
        sa.Column("agent_field", sa.String(128)),
        sa.Column("transform_rule", sa.String(256)),
        schema="sync",
    )


def downgrade() -> None:
    for schema in reversed(SCHEMAS):
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
