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

    async def execute(self, session, phone_number: str, service_centre_id: int, vehicle_no: str | None = None, **kwargs):
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
                cv.vehicle_model_type,
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
               AND (:vehicle_no IS NULL OR LOWER(cv.vehicle_no) = LOWER(:vehicle_no))
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
            "service_centre_id": service_centre_id,
            "vehicle_no": vehicle_no
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

class AddPikpartCustomerVehicleTool(BaseTool):
    name = "add_pikpart_customer_vehicle"
    description = (
        "Add or register a new vehicle entry under a customer's phone number. "
        "If the customer already exists, links the new vehicle to their existing customer ID, "
        "allowing multiple vehicle entries under the same customer without duplicating the profile. "
        "Requires phone_number, vehicle_no, make, model. Optional: fuel_type, customer_name."
    )

    async def execute(
        self,
        session,
        phone_number: str,
        vehicle_no: str,
        make: str,
        model: str,
        fuel_type: str | None = None,
        vehicle_model_type: str | None = None,
        customer_name: str | None = None,
        **kwargs
    ):
        try:
            # 1. Lookup customer by phone number
            cust_query = text("""
                SELECT id, first_name, last_name, phone_number 
                FROM customers 
                WHERE RIGHT(phone_number, 10) = RIGHT(:phone_number, 10)
                   OR RIGHT(alt_phone_number, 10) = RIGHT(:phone_number, 10)
                LIMIT 1;
            """)
            cust_res = await session.execute(cust_query, {"phone_number": phone_number})
            cust_row = cust_res.mappings().first()

            if cust_row:
                customer_id = cust_row["id"]
            else:
                first_name = customer_name or "Customer"
                insert_cust = text("""
                    INSERT INTO customers (first_name, phone_number, is_active)
                    VALUES (:first_name, :phone_number, true)
                    RETURNING id;
                """)
                res = await session.execute(insert_cust, {"first_name": first_name, "phone_number": phone_number})
                customer_id = res.scalar_one()

            # 2. Check if vehicle already exists for this customer
            veh_check = text("""
                SELECT id, vehicle_no, make, model, fuel_type, vehicle_model_type 
                FROM customer_vehicles 
                WHERE customer_id = :customer_id 
                  AND LOWER(REPLACE(vehicle_no, ' ', '')) = LOWER(REPLACE(:vehicle_no, ' ', ''))
                LIMIT 1;
            """)
            veh_res = await session.execute(veh_check, {"customer_id": customer_id, "vehicle_no": vehicle_no})
            existing_veh = veh_res.mappings().first()

            if existing_veh:
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    data={
                        "message": "Vehicle already registered for this customer",
                        "customer_id": customer_id,
                        "customer_vehicle_id": existing_veh["id"],
                        "vehicle_no": existing_veh["vehicle_no"],
                        "make": existing_veh["make"],
                        "model": existing_veh["model"],
                        "fuel_type": existing_veh["fuel_type"],
                        "vehicle_model_type": existing_veh["vehicle_model_type"],
                    }
                )

            # 3. Insert new vehicle entry linked to existing customer
            insert_veh = text("""
                INSERT INTO customer_vehicles (customer_id, vehicle_no, make, model, fuel_type, vehicle_model_type, is_active)
                VALUES (:customer_id, :vehicle_no, :make, :model, :fuel_type, :vehicle_model_type, true)
                RETURNING id, customer_id, vehicle_no, make, model, fuel_type, vehicle_model_type;
            """)
            veh_insert_res = await session.execute(
                insert_veh,
                {
                    "customer_id": customer_id,
                    "vehicle_no": vehicle_no.strip().upper(),
                    "make": make.strip(),
                    "model": model.strip(),
                    "fuel_type": fuel_type.strip().lower() if fuel_type else None,
                    "vehicle_model_type": vehicle_model_type.strip().upper() if vehicle_model_type else None,
                }
            )
            new_veh = veh_insert_res.mappings().first()
            await session.commit()

            return ToolResult(
                tool_name=self.name,
                success=True,
                data={
                    "message": "Vehicle successfully added under customer profile",
                    "customer_id": customer_id,
                    "customer_vehicle_id": new_veh["id"],
                    "vehicle_no": new_veh["vehicle_no"],
                    "make": new_veh["make"],
                    "model": new_veh["model"],
                    "fuel_type": new_veh["fuel_type"],
                    "vehicle_model_type": new_veh["vehicle_model_type"],
                }
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))

