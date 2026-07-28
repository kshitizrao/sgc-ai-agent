"""Seed sample garage data for development."""

SEED_PARTS = [
    {
        "part_id": "PRT-8932",
        "sku": "SKU-BRK-SWIFT-01",
        "oem_part_number": "55810M68K00",
        "part_name": "Front Disc Brake Pad Set",
        "category": "Braking System",
        "part_brand": "Bosch",
        "part_type": "Aftermarket",
        "stock_quantity": 14,
        "selling_price": 1850.00,
        "bin_location": "Rack A-02",
        "search_tags": ["brake shoe", "break pad", "swift brake", "front brakes"],
    },
    {
        "part_id": "PRT-1102",
        "sku": "SKU-BRK-SWIFT-OEM",
        "oem_part_number": "55810M68K00-OEM",
        "part_name": "Front Disc Brake Pad Set OEM",
        "category": "Braking System",
        "part_brand": "Maruti Suzuki",
        "part_type": "OEM",
        "stock_quantity": 0,
        "selling_price": 2400.00,
        "bin_location": "Rack A-01",
        "search_tags": ["brake pad", "swift brake", "oem"],
    },
    {
        "part_id": "PRT-4491",
        "sku": "SKU-AF-CRETA-01",
        "oem_part_number": "28113-A0100",
        "part_name": "Engine Air Filter",
        "category": "Engine",
        "part_brand": "TVS",
        "part_type": "Aftermarket",
        "stock_quantity": 22,
        "selling_price": 380.00,
        "bin_location": "Rack B-05",
        "search_tags": ["air filter", "creta filter"],
    },
]

SEED_FITMENTS = [
    {"part_id": "PRT-8932", "vehicle_make": "Maruti Suzuki", "vehicle_model": "Swift", "fuel_type": "Petrol", "year_from": 2018, "year_to": 2022},
    {"part_id": "PRT-1102", "vehicle_make": "Maruti Suzuki", "vehicle_model": "Swift", "fuel_type": "Petrol", "year_from": 2018, "year_to": 2022},
    {"part_id": "PRT-4491", "vehicle_make": "Hyundai", "vehicle_model": "Creta", "fuel_type": "Diesel", "year_from": 2018, "year_to": 2024},
]

SEED_INTERCHANGES = [
    {"part_id": "PRT-8932", "alternate_part_id": "PRT-1102", "notes": "OEM equivalent"},
]

SEED_SEGMENTS = [
    {"segment_id": "SEG-HATCH-PETROL", "body_type": "Hatchback", "fuel_type": "Petrol", "engine_oil_capacity": 3.0},
    {"segment_id": "SEG-SUV-DIESEL", "body_type": "Compact_SUV", "fuel_type": "Diesel", "engine_oil_capacity": 5.3},
]

SEED_PACKAGES = [
    {"package_id": "PKG-BASIC", "package_name": "Basic Service", "interval_km": 5000, "interval_months": 6, "package_description": "Essential maintenance for everyday driving."},
    {"package_id": "PKG-STD", "package_name": "Standard Service", "interval_km": 10000, "interval_months": 12, "package_description": "Includes wheel alignment and more filter replacements."},
    {"package_id": "PKG-COMP", "package_name": "Comprehensive Service", "interval_km": 20000, "interval_months": 24, "package_description": "Major service with fluid flushes and deep cleaning."},
]

SEED_INCLUSIONS = [
    {"package_id": "PKG-BASIC", "inclusion_key": "Engine_Oil_&_Oil_Filter", "inclusion_value": "Replace"},
    {"package_id": "PKG-BASIC", "inclusion_key": "Wheel_Alignment", "inclusion_value": "No"},
    {"package_id": "PKG-STD", "inclusion_key": "Engine_Oil_&_Oil_Filter", "inclusion_value": "Replace"},
    {"package_id": "PKG-STD", "inclusion_key": "Wheel_Alignment", "inclusion_value": "Yes"},
    {"package_id": "PKG-COMP", "inclusion_key": "Throttle_Body_Cleaning", "inclusion_value": "Yes"},
]

SEED_PRICING = [
    {"pricing_id": "PRC-001", "package_id": "PKG-STD", "segment_id": "SEG-HATCH-PETROL", "labour_cost": 1200, "consumables_cost": 2300, "total_estimated_cost": 3500, "service_duration_hrs": 3},
    {"pricing_id": "PRC-009", "package_id": "PKG-STD", "segment_id": "SEG-SUV-DIESEL", "labour_cost": 2000, "consumables_cost": 4500, "total_estimated_cost": 6500, "service_duration_hrs": 4.5},
]

SEED_TRIAGE = [
    {"symptom_id": "SYM-PUNCTURE", "symptom_tags": ["flat tyre", "puncture", "tyre burst"], "severity_level": "Low", "required_action": "Mobile_Mechanic", "safety_prompt": "Pull over safely and turn on hazard lights."},
    {"symptom_id": "SYM-ACCIDENT", "symptom_tags": ["accident", "crashed", "collision"], "severity_level": "High", "required_action": "Tow_Truck", "safety_prompt": "Exit the vehicle and stand safely behind the barricade."},
]

SEED_GARAGES = [
    {"garage_id": "GRG-DEL-045", "garage_name": "Euro Motors", "location_lat": 28.6139, "location_lng": 77.2090, "address_area": "Karol Bagh", "overall_rating": 4.6, "standard_labor_rate": 850},
    {"garage_id": "GRG-DEL-012", "garage_name": "Sharma Auto Works", "location_lat": 28.6200, "location_lng": 77.2100, "address_area": "Karol Bagh", "overall_rating": 4.0, "standard_labor_rate": 450},
]

SEED_DIAGNOSTICS = [
    {"issue_id": "ISS-DPF-01", "issue_name": "DPF Clogging", "system_category": "Engine", "severity_level": "Moderate", "is_safety_risk": False, "resolution_service_id": "SRV-DPF-CLEAN"},
    {"symptom_id": "SYM-SMOKE-01", "issue_id": "ISS-DPF-01", "customer_keywords": ["black smoke", "sluggish", "poor pickup"], "sensory_category": "Sight", "ai_diagnostic_question": "Does the smoke appear mostly during acceleration?"},
    {"prediction_id": "PRED-CRETA-045", "issue_id": "ISS-DPF-01", "vehicle_make": "Hyundai", "vehicle_model": "Creta", "fuel_type": "Diesel", "risk_start_km": 60000, "risk_end_km": 80000, "probability_score": "High"},
]

SEED_CLAIMS = [
    {"claim_id": "CLM-2024-089", "vehicle_reg_no": "DL-8C-AA-1122", "insurance_provider": "HDFC Ergo", "claim_type": "Cashless", "claim_status": "Surveyor_Approved"},
    {"policy_id": "POL-1122", "vehicle_reg_no": "DL-8C-AA-1122", "policy_type": "Comprehensive", "compulsory_deductible": 1000, "consumables_cover_addon": False},
    {"estimate_line_id": "ELI-001", "claim_id": "CLM-2024-089", "part_id": "PRT-BUMPER-F", "part_material": "Plastic", "garage_est_amount": 5500, "surveyor_apprv_amount": 5500, "surveyor_action": "Approved", "customer_liability": 2750},
]
