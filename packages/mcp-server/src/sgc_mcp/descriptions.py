"""Rich, LLM-friendly descriptions for prod_pikpart tables and columns.

These descriptions are embedded in MCP tool definitions so the LLM understands
what each tool accesses and can generate appropriate queries.  Descriptions are
written from the actual schema inspection and sample data analysis performed on
2026-09-12.
"""

# ---------------------------------------------------------------------------
# Table-level descriptions
# ---------------------------------------------------------------------------
TABLE_DESCRIPTIONS: dict[str, str] = {
    "customers": (
        "Customer master table (136K+ rows). Contains customer profiles including "
        "name (first_name, last_name), phone_number, email, business info, "
        "vehicle type preference (serve_vehicle_type: '2W'/'4W'), KYC status, "
        "and activity flags. Primary lookup is by phone_number or id. "
        "resource_type is typically 'Customer'."
    ),
    "services": (
        "Service catalog (129K+ rows). Each row is a specific service offering "
        "(e.g., 'Air Filter Replacement', 'Basic Service') with pricing tiers "
        "(tier1_price, tier2_price, tier3_price), GST info (gst_rate, gst_type), "
        "vehicle_type ('bike'/'scooty'/'car'), fuel_type ('petrol'/'diesel'/'cng'), "
        "engine CC range (start_engine_cc, end_engine_cc), service_duration in minutes, "
        "service_recommendation text, and model_name for vehicle-specific services. "
        "service_type can be 'Service' or 'Package'. is_quick flags express services."
    ),
    "customer_vehicles": (
        "Vehicles registered by customers (59K+ rows). Links customer_id to their "
        "vehicle details: vehicle_no (registration number like 'UP45W1315'), "
        "make (brand like 'TVS', 'Hero', 'Bajaj'), model (like 'Jupitor 110', "
        "'Splendor Plus'), fuel_type, engine_cc, vehicle_type ('bike'/'scooty'/'car'), "
        "vehicle_model_type ('2W'/'4W'), insurance and pollution expiry dates, "
        "and next_service_date."
    ),
    "vehicle_services": (
        "Price matrix linking services to vehicle models (14.7M+ rows). Each row "
        "specifies the price of a service_id for a specific vehicle_model_id / "
        "model_name, with fuel_type, transmission_type, tier_type, and "
        "discount_percent. Use this to look up exact pricing for a service on a "
        "specific vehicle. Join with services table on service_id."
    ),
    "service_centre_services": (
        "Maps which services are offered at which service centres (3.2M+ rows). "
        "Links service_id to service_centres_id, with engine CC range and "
        "model_name filters. Use this to check if a specific service centre "
        "offers a particular service for a given vehicle model."
    ),
    "booking_services": (
        "Individual services within a booking (51K+ rows). Each row is one service "
        "line item in a booking: booking_id, service_id, selling_price, status "
        "('pending'/'approved'/'completed'), item_type ('Service'/'Package'), "
        "customer_approval_status, discount info, tax_rate, and checkpoint info. "
        "Join with bookings on booking_id."
    ),
    "bookings": (
        "Booking lifecycle records (40K+ rows). Tracks full booking workflow: "
        "customer_id, customer_vehicle_id, service_centre_id, status "
        "('requested'/'confirmed'/'wip'/'completed'/'cancelled'), "
        "price, payment_status ('paid'/'pending'), vehicle_no, booking_datetime, "
        "pickup/drop facilities, jobcard_number, first_name/phone_number of customer. "
        "Rich date tracking: confirmed_date, service_start_date, service_end_date."
    ),
    "vehicle_brands": (
        "Vehicle brand master data (308 rows). Brand names (e.g., 'Hero', 'TVS', "
        "'Bajaj', 'Honda'), vehicle_type, fuel_type, is_popular flag, and "
        "Hindi name (name_hi). Small lookup table."
    ),
    "vehicle_categories": (
        "Vehicle category types (3 rows): '2W' (two-wheeler), '4W' (four-wheeler), "
        "'3W' (three-wheeler). Simple reference table."
    ),
}

# ---------------------------------------------------------------------------
# Column-level descriptions for key columns (used in tool parameter docs)
# ---------------------------------------------------------------------------
COLUMN_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "customers": {
        "id": "Unique customer ID (integer, auto-increment)",
        "first_name": "Customer's first name (may be None for new registrations)",
        "phone_number": "10-digit Indian mobile number — primary identifier for lookup",
        "is_active": "Whether the customer account is active",
        "serve_vehicle_type": "Vehicle type preference: '2W' or '4W'",
        "resource_type": "Always 'Customer' for customer records",
        "is_business": "True if customer is a business/shop",
        "last_selected_vehicle_type": "Last vehicle type selected by customer ('2W'/'4W')",
    },
    "services": {
        "id": "Unique service ID",
        "name": "Service name (e.g., 'Air Filter Replacement', 'Basic Service')",
        "base_price": "Base price in INR before discounts",
        "vehicle_type": "Target vehicle type: 'bike', 'scooty', 'car'",
        "fuel_type": "Target fuel type: 'petrol', 'diesel', 'cng', 'electric'",
        "service_code": "Internal service code (e.g., 'SC_AAA0113')",
        "gst_rate": "GST rate as percentage (typically 18.0)",
        "tier1_price": "Tier 1 service centre price in INR",
        "tier2_price": "Tier 2 service centre price in INR",
        "tier3_price": "Tier 3 service centre price in INR",
        "service_duration": "Duration in minutes (e.g., '15')",
        "service_recommendation": "When this service is recommended (e.g., 'Every 500 kms')",
        "serve_vehicle_type": "Vehicle category: '2W' or '4W'",
        "is_quick": "True for express/quick services",
        "model_name": "Specific vehicle model this service applies to",
        "service_type": "Type: 'Service' or 'Package'",
        "start_engine_cc": "Minimum engine CC this service applies to",
        "end_engine_cc": "Maximum engine CC this service applies to",
    },
    "customer_vehicles": {
        "id": "Unique vehicle registration ID",
        "customer_id": "FK to customers.id",
        "vehicle_no": "Vehicle registration number (e.g., 'UP45W1315')",
        "make": "Vehicle brand (e.g., 'TVS', 'Hero', 'Bajaj')",
        "model": "Vehicle model (e.g., 'Jupitor 110', 'Splendor Plus')",
        "fuel_type": "Fuel type: 'petrol', 'diesel', 'cng'",
        "engine_cc": "Engine displacement in CC",
        "vehicle_type": "Type: 'bike', 'scooty', 'car'",
        "vehicle_model_type": "Category: '2W' or '4W'",
        "next_service_date": "Next scheduled service date",
    },
    "bookings": {
        "id": "Unique booking ID",
        "customer_id": "FK to customers.id",
        "customer_vehicle_id": "FK to customer_vehicles.id",
        "service_centre_id": "FK to service centres table",
        "status": "Booking status: 'requested'/'confirmed'/'wip'/'completed'/'cancelled'",
        "price": "Total booking price in INR",
        "payment_status": "Payment status: 'paid'/'pending'",
        "vehicle_no": "Vehicle registration number",
        "booking_datetime": "Date of booking",
        "first_name": "Customer first name (denormalized)",
        "phone_number": "Customer phone number (denormalized)",
        "jobcard_number": "Job card reference number",
    },
    "booking_services": {
        "id": "Unique booking service line item ID",
        "booking_id": "FK to bookings.id",
        "service_id": "FK to services.id",
        "selling_price": "Selling price in INR for this service",
        "status": "Line item status: 'pending'/'approved'/'completed'",
        "name": "Service name (denormalized)",
        "item_type": "Type: 'Service' or 'Package'",
        "customer_approval_status": "Customer approval: 'approved'/'pending'/'rejected'",
        "tax_rate": "Tax rate percentage",
    },
    "vehicle_services": {
        "id": "Unique ID",
        "vehicle_model_id": "FK to vehicle model",
        "model_name": "Vehicle model name (e.g., 'WR-V', 'CITY IVTEC')",
        "service_id": "FK to services.id",
        "price": "Service price in INR for this vehicle model",
        "fuel_type": "Fuel type filter",
        "transmission_type": "Transmission: 'manual' or 'automatic'",
        "tier_type": "Service centre tier: 'tier1', 'tier2', 'tier3'",
        "service_centre_id": "FK to service centre",
    },
    "service_centre_services": {
        "id": "Unique ID",
        "service_id": "FK to services.id",
        "service_centres_id": "FK to service centres",
        "model_name": "Vehicle model this mapping applies to",
        "start_engine_cc": "Minimum engine CC range",
        "end_engine_cc": "Maximum engine CC range",
    },
    "vehicle_brands": {
        "id": "Unique brand ID",
        "name": "Brand name in English (e.g., 'Hero', 'TVS')",
        "name_hi": "Brand name in Hindi",
        "vehicle_type": "Vehicle type this brand makes",
        "fuel_type": "Primary fuel type",
        "is_popular": "True for popular/common brands",
    },
    "vehicle_categories": {
        "id": "Category ID",
        "name": "Category name: '2W', '3W', '4W'",
        "is_active": "Whether this category is active",
    },
}
