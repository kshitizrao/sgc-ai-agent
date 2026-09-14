import httpx
from sqlalchemy import text
from sgc_shared.types import ToolResult
from sgc_tools.registry import BaseTool

class FetchPikpartServicesTool(BaseTool):
    name = "fetch_pikpart_services"
    description = "Fetch services from the prod_pikpart database"

    async def execute(self, session, limit=10, **kwargs):
        query = text("SELECT * FROM public.services LIMIT :limit")
        result = await session.execute(query, {"limit": limit})
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=[dict(row._mapping) for row in result]
        )

class FetchPikpartCustomersTool(BaseTool):
    name = "fetch_pikpart_customers"
    description = "Fetch customers from the prod_pikpart database"

    async def execute(self, session, limit=10, **kwargs):
        query = text("SELECT * FROM public.customers LIMIT :limit")
        result = await session.execute(query, {"limit": limit})
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=[dict(row._mapping) for row in result]
        )

class FetchPikpartCustomerVehiclesTool(BaseTool):
    name = "fetch_pikpart_customer_vehicles"
    description = "Fetch customer vehicles from the prod_pikpart database"

    async def execute(self, session, limit=10, **kwargs):
        query = text("SELECT * FROM public.customer_vehicles LIMIT :limit")
        result = await session.execute(query, {"limit": limit})
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=[dict(row._mapping) for row in result]
        )

class FetchPikpartVehicleServicesTool(BaseTool):
    name = "fetch_pikpart_vehicle_services"
    description = "Fetch vehicle services from the prod_pikpart database"

    async def execute(self, session, limit=10, **kwargs):
        query = text("SELECT * FROM public.vehicle_services LIMIT :limit")
        result = await session.execute(query, {"limit": limit})
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=[dict(row._mapping) for row in result]
        )

class FetchPikpartBookingServicesTool(BaseTool):
    name = "fetch_pikpart_booking_services"
    description = "Fetch booking services from the prod_pikpart database"

    async def execute(self, session, limit=10, **kwargs):
        query = text("SELECT * FROM public.booking_services LIMIT :limit")
        result = await session.execute(query, {"limit": limit})
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=[dict(row._mapping) for row in result]
        )

class FetchPikpartBookingsTool(BaseTool):
    name = "fetch_pikpart_bookings"
    description = "Fetch bookings from the prod_pikpart database"

    async def execute(self, session, limit=10, **kwargs):
        query = text("SELECT * FROM public.bookings LIMIT :limit")
        result = await session.execute(query, {"limit": limit})
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=[dict(row._mapping) for row in result]
        )

class FetchPikpartVehicleBrandsTool(BaseTool):
    name = "fetch_pikpart_vehicle_brands"
    description = "Fetch vehicle brands from the prod_pikpart database"

    async def execute(self, session, limit=10, **kwargs):
        query = text("SELECT * FROM public.vehicle_brands LIMIT :limit")
        result = await session.execute(query, {"limit": limit})
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=[dict(row._mapping) for row in result]
        )

class FetchPikpartVehicleCategoriesTool(BaseTool):
    name = "fetch_pikpart_vehicle_categories"
    description = "Fetch vehicle categories from the prod_pikpart database"

    async def execute(self, session, limit=10, **kwargs):
        query = text("SELECT * FROM public.vehicle_categories LIMIT :limit")
        result = await session.execute(query, {"limit": limit})
        return ToolResult(
            tool_name=self.name,
            success=True,
            data=[dict(row._mapping) for row in result]
        )

class FetchPikpartVehicleDetailsTool(BaseTool):
    name = "fetch_pikpart_vehicle_details"
    description = "Fetch detailed vehicle information from Pikpart API using a vehicle registration number (e.g., DL10CT9251)"

    async def execute(self, session, vehicle_number: str, **kwargs):
        url = "https://uatapi.pikpart.com/api/Customer/searchVehicles"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={"object_hash": {"vehicle_number": vehicle_number}})
                response.raise_for_status()
                data = response.json()
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))

