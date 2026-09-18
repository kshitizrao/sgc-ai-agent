from pydantic import BaseModel, Field


class CustomerContext(BaseModel):
    customer_id: str | None = None
    phone_number: str | None = None
    vehicle_id: str | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    vehicle_variant: str | None = None
    fuel_type: str | None = None
    registration_no: str | None = None
    mileage_km: int | None = None
    vehicle_age_months: int | None = None
    locale: str = "en-IN"


class LocationContext(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    area: str | None = None


class ContextEnvelope(BaseModel):
    customer: CustomerContext = Field(default_factory=CustomerContext)
    location: LocationContext | None = None
    garage_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class SourceRef(BaseModel):
    table: str
    record_id: str
    field: str | None = None


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: dict | list | None = None
    source_refs: list[SourceRef] = Field(default_factory=list)
    error: str | None = None
