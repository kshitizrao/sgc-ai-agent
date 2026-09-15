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

from sqlalchemy import text



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

class FetchPikpartCustomerServiceDetailsTool(BaseTool):
    name = "fetch_pikpart_customer_service_details"
    description = "Fetch customer details, vehicle details, service types, garage details, service pricing, and discount against vehicle details. Requires phone number and service centre id."

    async def execute(self, session, phone_number: str, service_centre_id: int, **kwargs):
        query_str = """
            SELECT 
                c.id AS customer_id,
                c.first_name || ' ' || COALESCE(c.last_name, '') AS customer_name,
                c.phone_number,
                cv.id AS customer_vehicle_id,
                cv.vehicle_no,
                cv.make,
                cv.model AS customer_vehicle_model,
                cv.fuel_type AS customer_fuel_type,
                vs.id AS vehicle_service_id,
                s.id AS service_id,
                s.name AS service_name,
                s.service_code,
                scat.name AS service_category,
                vs.price AS base_price,
                COALESCE(vs.discount_percent, 0) AS discount_percent,
                ROUND((vs.price - (vs.price * COALESCE(vs.discount_percent, 0) / 100.0))::numeric, 2) AS discounted_price,
                vs.tier_type,
                vs.service_centre_id AS garage_id
            FROM customers c
            LEFT JOIN customer_vehicles cv 
                ON cv.customer_id = c.id 
               AND cv.is_active = true
            LEFT JOIN vehicle_services vs 
                ON vs.service_centre_id = :service_centre_id
               AND vs.is_active = true
               AND (
                   vs.vehicle_model_id = cv.vehicle_id 
                   OR LOWER(vs.model_name) = LOWER(cv.model)
                   OR vs.vehicle_model_id IS NULL
               )
               AND (
                   vs.fuel_type IS NULL 
                   OR LOWER(vs.fuel_type) = LOWER(cv.fuel_type)
               )
            LEFT JOIN services s 
                ON s.id = vs.service_id 
               AND s.is_active = true
            LEFT JOIN service_categories scat 
                ON scat.id = vs.service_category_id
            WHERE (
                RIGHT(c.phone_number, 10) = RIGHT(:phone_number, 10) 
                OR RIGHT(c.alt_phone_number, 10) = RIGHT(:phone_number, 10)
            )
            ORDER BY cv.id, scat.name, s.name ASC;
        """
        query = text(query_str)
        params = {
            "phone_number": phone_number,
            "service_centre_id": service_centre_id
        }
        
        try:
            result = await session.execute(query, params)
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=[dict(row._mapping) for row in result]
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e)
            )

