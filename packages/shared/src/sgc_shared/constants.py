from enum import StrEnum


class IntentType(StrEnum):
    PARTS = "parts"
    CLAIMS = "claims"
    RSA = "rsa"
    GARAGE_MATCH = "garage_match"
    DIAGNOSTICS = "diagnostics"
    GENERAL_FAQ = "general_faq"
    VEHICLE_INFO = "vehicle_info"
    PIKPART_QUERY = "pikpart_query"
    SERVICE_BOOKING = "service_booking"


class TaskType(StrEnum):
    CLASSIFY = "classify"
    TAG_MATCH = "tag_match"
    TRIAGE = "triage"
    TOOL_NLG = "tool_nlg"
    COMPLEX_REASONING = "complex_reasoning"
    CLAIMS_EXPLAIN = "claims_explain"


class FuelType(StrEnum):
    PETROL = "Petrol"
    DIESEL = "Diesel"
    CNG = "CNG"
    EV = "EV"


class VehicleSegment(StrEnum):
    HATCHBACK = "Hatchback"
    COMPACT_SEDAN = "Compact_Sedan"
    EXECUTIVE_SEDAN = "Executive_Sedan"
    COMPACT_SUV = "Compact_SUV"
    MID_SUV = "Mid_SUV"
    LUXURY_SUV = "Luxury_SUV"
