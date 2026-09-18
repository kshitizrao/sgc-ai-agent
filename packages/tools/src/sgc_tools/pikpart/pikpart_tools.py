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



# ════════════════════════════════════════════════════════════════════════════
# BOOKING FLOW TOOLS  (AI-Agent Service Booking)
# ════════════════════════════════════════════════════════════════════════════

from datetime import date, datetime, timedelta


class GetCustomerProfileAndContextTool(BaseTool):
    name = "get_customer_profile_and_context"
    description = (
        "Fetch complete customer context for service booking personalisation. "
        "Returns customer profile, all registered vehicles, booking history, "
        "preferred garage, last used garage, pickup/walk-in preference, "
        "and vehicle expiry alerts (insurance, PUC, next service date). "
        "Call this IMMEDIATELY when a service booking intent is detected. "
        "Requires phone_number (str)."
    )

    async def execute(self, session, phone_number: str, **kwargs):
        try:
            profile_q = text("""
                SELECT
                    c.id AS customer_id, c.first_name, c.last_name,
                    c.phone_number, c.last_pincode, c.opted_wa,
                    cv.id AS vehicle_id, cv.vehicle_no, cv.make, cv.model,
                    cv.fuel_type, cv.vehicle_model_type, cv.engine_cc, cv.year,
                    cv.insurance_expiry_date, cv.pollution_expiry_date,
                    cv.pucc_expiry_date, cv.next_service_date
                FROM customers c
                LEFT JOIN customer_vehicles cv ON cv.customer_id = c.id AND cv.is_active = true
                WHERE RIGHT(c.phone_number, 10) = RIGHT(:phone, 10)
                   OR RIGHT(c.alt_phone_number, 10) = RIGHT(:phone, 10)
                ORDER BY cv.id ASC
            """)
            profile_rows = (await session.execute(profile_q, {"phone": phone_number})).mappings().all()
            if not profile_rows:
                return ToolResult(tool_name=self.name, success=True,
                                  data={"customer": None, "vehicles": [], "new_customer": True})

            first = profile_rows[0]
            customer = {
                "customer_id": first["customer_id"], "first_name": first["first_name"],
                "last_name": first["last_name"], "phone_number": first["phone_number"],
                "last_pincode": first["last_pincode"], "opted_wa": first["opted_wa"],
            }
            today = date.today()
            vehicles = []
            for r in profile_rows:
                if r["vehicle_id"] is None:
                    continue
                alerts = []
                for label, val in [
                    ("Insurance", r["insurance_expiry_date"]),
                    ("PUC", r["pucc_expiry_date"] or r["pollution_expiry_date"]),
                    ("Next Service", r["next_service_date"]),
                ]:
                    if val:
                        exp = val.date() if hasattr(val, "date") else val
                        delta = (exp - today).days
                        if delta <= 30:
                            alerts.append({"type": label, "expiry_date": str(exp),
                                           "days_remaining": delta, "urgent": delta <= 7})
                vehicles.append({
                    "vehicle_id": r["vehicle_id"], "vehicle_no": r["vehicle_no"],
                    "make": r["make"], "model": r["model"], "fuel_type": r["fuel_type"],
                    "vehicle_model_type": r["vehicle_model_type"], "engine_cc": r["engine_cc"],
                    "year": r["year"], "alerts": alerts,
                })

            cust_id = customer["customer_id"]
            history_q = text("""
                SELECT b.id AS booking_id, b.booking_datetime AS booking_date,
                    b.booking_slot, b.service_centre_id AS garage_id,
                    COALESCE(sc.garage_name, sc.name) AS garage_name,
                    b.pickup_facility, b.drop_facility, b.status, b.estimated_price,
                    b.customer_comment,
                    ARRAY_AGG(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) AS services,
                    MAX(rt.rate) AS rating_given
                FROM bookings b
                LEFT JOIN service_centres sc ON sc.id = b.service_centre_id
                LEFT JOIN booking_services bs ON bs.booking_id = b.id
                LEFT JOIN services s ON s.id = bs.service_id
                LEFT JOIN ratings rt ON rt.service_centre_id = b.service_centre_id AND rt.customer_id = :cid
                WHERE b.customer_id = :cid
                GROUP BY b.id, sc.garage_name, sc.name
                ORDER BY b."createdAt" DESC LIMIT 5
            """)
            booking_history = [dict(r) for r in (await session.execute(history_q, {"cid": cust_id})).mappings().all()]

            pref_q = text("""
                SELECT b.service_centre_id AS garage_id,
                    COALESCE(sc.garage_name, sc.name) AS garage_name,
                    COUNT(*) AS visit_count, MAX(rt.rate) AS rating_given
                FROM bookings b
                LEFT JOIN service_centres sc ON sc.id = b.service_centre_id
                LEFT JOIN ratings rt ON rt.service_centre_id = b.service_centre_id AND rt.customer_id = :cid
                WHERE b.customer_id = :cid AND b.service_centre_id IS NOT NULL
                GROUP BY b.service_centre_id, sc.garage_name, sc.name
                ORDER BY visit_count DESC LIMIT 1
            """)
            pref_row = (await session.execute(pref_q, {"cid": cust_id})).mappings().first()
            preferred_garage = dict(pref_row) if pref_row else None
            last_garage = ({"garage_id": booking_history[0]["garage_id"],
                             "garage_name": booking_history[0]["garage_name"]}
                           if booking_history and booking_history[0].get("garage_id") else None)
            pickup_count = sum(1 for b in booking_history if b.get("pickup_facility"))
            preferred_mode = "pickup" if pickup_count >= max(len(booking_history) / 2, 1) else "walkin"

            return ToolResult(tool_name=self.name, success=True, data={
                "customer": customer, "vehicles": vehicles, "booking_history": booking_history,
                "preferred_garage": preferred_garage, "last_garage": last_garage,
                "preferred_mode": preferred_mode, "new_customer": False,
            })
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


class FindNearbyGaragesTool(BaseTool):
    name = "find_nearby_garages"
    description = (
        "Find garages within radius_km of the customer's GPS location using Haversine formula. "
        "Requires latitude (float) and longitude (float). "
        "Returns garages sorted by distance with avg_rating, my_rating (customer-specific), "
        "opening hours, address, phone. "
        "Optional: customer_id (int), radius_km (int, default 15)."
    )

    async def execute(self, session, latitude: float, longitude: float,
                      radius_km: int = 15, customer_id: int | None = None, **kwargs):
        try:
            q = text("""
                SELECT sc.id AS service_centre_id,
                    COALESCE(sc.business_name, sc.garage_name, sc.name) AS garage_name,
                    sc.business_name, sc.name AS centre_name, sc.phone_number,
                    sc.opening_hour, sc.closing_hour, sc.day_of_week,
                    sc.garage_type, sc.garage_category, sc.tier_type,
                    a.full_address, a.city, a.pincode,
                    a.latitude AS garage_lat, a.longitude AS garage_lng,
                    (6371 * ACOS(LEAST(1.0,
                        COS(RADIANS(:lat)) * COS(RADIANS(a.latitude))
                        * COS(RADIANS(a.longitude) - RADIANS(:lng))
                        + SIN(RADIANS(:lat)) * SIN(RADIANS(a.latitude))
                    ))) AS distance_km,
                    ROUND(AVG(rt.rate)::numeric, 1) AS avg_rating,
                    COUNT(rt.id) AS total_ratings,
                    MAX(CASE WHEN rt.customer_id = :cust_id THEN rt.rate END) AS my_rating
                FROM service_centres sc
                JOIN addresses a ON a.resource_id = sc.id AND a.resource_type = 'service_centre'
                    AND a.latitude IS NOT NULL AND a.longitude IS NOT NULL AND a.is_active = true
                LEFT JOIN ratings rt ON rt.service_centre_id = sc.id
                WHERE sc.is_active = true AND (sc.is_onboard = true OR sc.is_default = true)
                GROUP BY sc.id, sc.business_name, sc.garage_name, sc.name, sc.phone_number,
                    sc.opening_hour, sc.closing_hour, sc.day_of_week,
                    sc.garage_type, sc.garage_category, sc.tier_type,
                    a.full_address, a.city, a.pincode, a.latitude, a.longitude
                HAVING (6371 * ACOS(LEAST(1.0,
                    COS(RADIANS(:lat)) * COS(RADIANS(a.latitude))
                    * COS(RADIANS(a.longitude) - RADIANS(:lng))
                    + SIN(RADIANS(:lat)) * SIN(RADIANS(a.latitude))
                ))) <= :radius
                ORDER BY distance_km ASC
            """)
            rows = (await session.execute(q, {"lat": latitude, "lng": longitude,
                                              "radius": radius_km, "cust_id": customer_id})).mappings().all()
            garages = [{
                "service_centre_id": r["service_centre_id"],
                "garage_name": r["garage_name"] or r["centre_name"],
                "phone_number": r["phone_number"], "opening_hour": r["opening_hour"],
                "closing_hour": r["closing_hour"], "day_of_week": r["day_of_week"],
                "garage_type": r["garage_type"], "tier_type": r["tier_type"],
                "address": r["full_address"], "city": r["city"], "pincode": r["pincode"],
                "distance_km": round(float(r["distance_km"]), 2),
                "avg_rating": float(r["avg_rating"]) if r["avg_rating"] else None,
                "total_ratings": int(r["total_ratings"]),
                "my_rating": float(r["my_rating"]) if r["my_rating"] else None,
            } for r in rows]
            return ToolResult(tool_name=self.name, success=True, data={
                "garages": garages, "count": len(garages),
                "searched_radius_km": radius_km, "no_garages_nearby": len(garages) == 0,
            })
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


class GetServicesForVehicleAtGarageTool(BaseTool):
    name = "get_services_for_vehicle_at_garage"
    description = (
        "Fetch individual services at a garage for a customer vehicle "
        "(filtered by make, model, fuel_type). Returns categories with services, "
        "pricing, duration, recommendation flags. "
        "Requires service_centre_id (int) and customer_vehicle_id (int). "
        "NOTE: call get_service_packages_for_vehicle separately for packages."
    )

    async def execute(self, session, service_centre_id: int, customer_vehicle_id: int, **kwargs):
        try:
            q = text("""
                WITH veh AS (
                    SELECT id, make, model, fuel_type, engine_cc, vehicle_id
                    FROM customer_vehicles WHERE id = :cv_id AND is_active = true LIMIT 1
                )
                SELECT scat.id AS category_id, scat.name AS category_name, scat.priority,
                    s.id AS service_id, s.name AS service_name, s.service_code,
                    s.service_duration, s.service_recommendation, s.is_recommended, s.is_highlighted,
                    vs.id AS vehicle_service_id, vs.price AS base_price,
                    COALESCE(vs.discount_percent, 0) AS discount_percent,
                    ROUND((vs.price - (vs.price * COALESCE(vs.discount_percent, 0) / 100.0))::numeric, 2) AS discounted_price,
                    vs.tier_type
                FROM vehicle_services vs
                JOIN veh ON (
                    vs.service_centre_id = :sc_id AND vs.is_active = true
                    AND (vs.vehicle_model_id = veh.vehicle_id OR LOWER(vs.model_name) = LOWER(veh.model) OR vs.vehicle_model_id IS NULL)
                    AND (vs.fuel_type IS NULL OR LOWER(vs.fuel_type) = LOWER(veh.fuel_type))
                )
                JOIN services s ON s.id = vs.service_id AND s.is_active = true
                JOIN service_categories scat ON scat.id = vs.service_category_id AND scat.is_active = true
                ORDER BY scat.priority ASC NULLS LAST, s.name ASC
            """)
            rows = (await session.execute(q, {"cv_id": customer_vehicle_id, "sc_id": service_centre_id})).mappings().all()
            categories: dict = {}
            for r in rows:
                cid = r["category_id"]
                if cid not in categories:
                    categories[cid] = {"category_id": cid, "category_name": r["category_name"], "services": []}
                categories[cid]["services"].append({
                    "service_id": r["service_id"], "vehicle_service_id": r["vehicle_service_id"],
                    "name": r["service_name"], "service_code": r["service_code"],
                    "duration": r["service_duration"], "recommendation": r["service_recommendation"],
                    "is_recommended": r["is_recommended"], "is_highlighted": r["is_highlighted"],
                    "base_price": r["base_price"], "discount_percent": float(r["discount_percent"]),
                    "discounted_price": float(r["discounted_price"]) if r["discounted_price"] else None,
                    "tier_type": r["tier_type"],
                })
            return ToolResult(tool_name=self.name, success=True, data={
                "service_centre_id": service_centre_id, "customer_vehicle_id": customer_vehicle_id,
                "categories": list(categories.values()), "total_services": len(rows),
            })
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


class GetServicePackagesForVehicleTool(BaseTool):
    name = "get_service_packages_for_vehicle"
    description = (
        "Fetch bundled service packages at a garage for a customer vehicle "
        "(filtered by vehicle_id and engine_cc range). "
        "Show as SEPARATE step after individual service selection. "
        "Requires service_centre_id (int) and customer_vehicle_id (int)."
    )

    async def execute(self, session, service_centre_id: int, customer_vehicle_id: int, **kwargs):
        try:
            q = text("""
                WITH veh AS (
                    SELECT id, vehicle_id, engine_cc FROM customer_vehicles
                    WHERE id = :cv_id AND is_active = true LIMIT 1
                )
                SELECT sp.id AS package_id, sp.name AS package_name, sp.actual_price,
                    sp.price AS discounted_price, sp.discount, sp.description,
                    sp.tier_type, sp.icon_url, scat.name AS category_name
                FROM service_packages sp
                JOIN veh ON (
                    sp.service_centre_id = :sc_id AND sp.is_active = true
                    AND (sp.vehicle_id IS NULL OR sp.vehicle_id = veh.vehicle_id)
                    AND (sp.start_engine_cc IS NULL OR veh.engine_cc IS NULL
                         OR veh.engine_cc BETWEEN sp.start_engine_cc AND COALESCE(sp.end_engine_cc, 99999))
                )
                LEFT JOIN service_categories scat ON scat.id = sp.service_category_id
                ORDER BY sp.price ASC
            """)
            rows = (await session.execute(q, {"cv_id": customer_vehicle_id, "sc_id": service_centre_id})).mappings().all()
            return ToolResult(tool_name=self.name, success=True, data={
                "service_centre_id": service_centre_id, "customer_vehicle_id": customer_vehicle_id,
                "packages": [dict(r) for r in rows], "count": len(rows),
            })
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


class GetAvailableSlotsTool(BaseTool):
    """
    Derives booking slots: hourly from opening_hour to closing_hour.
    Garage capacity = 5 concurrent services/slot. Deducts booked count.
    """
    name = "get_available_slots"
    description = (
        "Return available booking slots at a garage for the next N days. "
        "1 slot = 1 hour; capacity 5/slot; existing bookings deducted. "
        "Requires service_centre_id (int). "
        "Optional: from_date (ISO date str), days_ahead (int, default 7)."
    )
    GARAGE_CAPACITY = 5

    async def execute(self, session, service_centre_id: int,
                      from_date: str | None = None, days_ahead: int = 7, **kwargs):
        try:
            hours_row = (await session.execute(
                text("SELECT opening_hour, closing_hour, day_of_week FROM service_centres WHERE id=:sc_id AND is_active=true LIMIT 1"),
                {"sc_id": service_centre_id}
            )).mappings().first()
            if not hours_row:
                return ToolResult(tool_name=self.name, success=False, error="Garage not found.")

            def _hr(s: str) -> int:
                s = str(s).strip()
                for fmt in ("%I:%M %p", "%H:%M", "%H"):
                    try:
                        return datetime.strptime(s, fmt).hour
                    except ValueError:
                        pass
                try:
                    return int(s.split(":")[0])
                except Exception:
                    return 9

            open_hr, close_hr = _hr(hours_row["opening_hour"]), _hr(hours_row["closing_hour"])
            day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
            raw = hours_row["day_of_week"] or ""
            working = ({day_map[d.strip().lower()[:3]] for d in raw.split(",") if d.strip().lower()[:3] in day_map}
                       if raw.strip() else {0, 1, 2, 3, 4, 5})

            start = date.today() + timedelta(days=1)
            if from_date:
                try:
                    start = date.fromisoformat(from_date)
                except ValueError:
                    pass
            end = start + timedelta(days=days_ahead - 1)

            booked_res = await session.execute(text("""
                SELECT booking_datetime AS bdate,
                    EXTRACT(HOUR FROM booking_slot) AS bslot_hr, COUNT(*) AS cnt
                FROM bookings
                WHERE service_centre_id=:sc_id AND status NOT IN ('cancelled','rejected')
                  AND booking_datetime BETWEEN :s AND :e AND booking_slot IS NOT NULL
                GROUP BY booking_datetime, bslot_hr
            """), {"sc_id": service_centre_id, "s": start, "e": end})
            booked_map = {(str(r["bdate"]), int(r["bslot_hr"])): int(r["cnt"])
                          for r in booked_res.mappings().all() if r["bslot_hr"] is not None}

            names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            days_out = []
            for i in range(days_ahead):
                d = start + timedelta(days=i)
                if d.weekday() not in working:
                    continue
                slots = [{"time": f"{hr:02d}:00", "available": self.GARAGE_CAPACITY - booked_map.get((str(d), hr), 0)}
                         for hr in range(open_hr, close_hr)
                         if self.GARAGE_CAPACITY - booked_map.get((str(d), hr), 0) > 0]
                if slots:
                    days_out.append({"date": str(d), "day_name": names[d.weekday()],
                                     "slots": slots, "slot_count": len(slots)})

            return ToolResult(tool_name=self.name, success=True, data={
                "service_centre_id": service_centre_id, "available_days": days_out, "days_returned": len(days_out),
            })
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


class GetPickupChargesTool(BaseTool):
    name = "get_pickup_charges"
    description = (
        "Fetch pickup/drop charges for a garage based on distance. "
        "Requires service_centre_id (int) and distance_km (float). "
        "Returns pickup_charge, drop_charge, combined_charge, distance_range."
    )

    async def execute(self, session, service_centre_id: int, distance_km: float, **kwargs):
        try:
            rows = (await session.execute(
                text('SELECT distance_range, "pickAmount" AS pc, "dropAmount" AS dc FROM pick_drop_charges WHERE service_centre_id=:sc_id AND is_active=true ORDER BY id ASC'),
                {"sc_id": service_centre_id}
            )).mappings().all()
            matched = None
            for r in rows:
                parts = (r["distance_range"] or "").replace(" ", "").split("-")
                if len(parts) == 2:
                    try:
                        lo, hi = float(parts[0]), float(parts[1])
                        if lo <= distance_km < hi:
                            matched = r
                            break
                    except ValueError:
                        pass
            if not matched and rows:
                matched = rows[-1]
            if not matched:
                return ToolResult(tool_name=self.name, success=True,
                                  data={"pickup_charge": 0, "drop_charge": 0, "combined_charge": 0,
                                        "note": "Pickup/drop charges not configured for this garage."})
            p, d = float(matched["pc"] or 0), float(matched["dc"] or 0)
            return ToolResult(tool_name=self.name, success=True, data={
                "service_centre_id": service_centre_id, "distance_km": distance_km,
                "distance_range": matched["distance_range"],
                "pickup_charge": p, "drop_charge": d, "combined_charge": round(p + d, 2),
            })
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))


class CreateServiceBookingTool(BaseTool):
    """
    Final booking commit after customer confirmation.
    Inserts into bookings + booking_services + addresses (if pickup).
    Sets booking_type='ai_agent' and initiated_by_app='ai_agent'.
    """
    name = "create_service_booking"
    description = (
        "Create a confirmed service booking after customer approval. "
        "Writes to bookings + booking_services + addresses tables. "
        "Required: customer_id (int), customer_vehicle_id (int), service_centre_id (int), "
        "service_ids (list[int]), booking_date (str ISO), booking_slot (str HH:MM), "
        "mode (str: 'pickup'|'walkin'|'drop'), estimated_price (float). "
        "Optional: package_ids (list[int]), customer_comment (str), "
        "address (dict: address_line_1, city, pincode, latitude, longitude)."
    )

    async def execute(self, session, customer_id: int, customer_vehicle_id: int,
                      service_centre_id: int, service_ids: list, booking_date: str,
                      booking_slot: str, mode: str, estimated_price: float,
                      package_ids: list | None = None, customer_comment: str | None = None,
                      address: dict | None = None, **kwargs):
        try:
            snap = (await session.execute(text("""
                SELECT c.first_name, c.last_name, c.phone_number,
                       cv.vehicle_no, cv.make, cv.model, cv.fuel_type
                FROM customers c JOIN customer_vehicles cv ON cv.id=:cv_id WHERE c.id=:cid LIMIT 1
            """), {"cid": customer_id, "cv_id": customer_vehicle_id})).mappings().first()
            if not snap:
                return ToolResult(tool_name=self.name, success=False, error="Customer or vehicle not found.")

            pickup_address_id = None
            if mode == "pickup" and address:
                full_addr = address.get("full_address") or (
                    f"{address.get('address_line_1','')} {address.get('city','')} {address.get('pincode','')}".strip())
                pickup_address_id = (await session.execute(text("""
                    INSERT INTO addresses (resource_id, resource_type, address_line_1, city, pincode,
                        latitude, longitude, full_address, is_active, created_by_user_type, "createdAt", "updatedAt")
                    VALUES (:rid,'booking',:l1,:city,:pin,:lat,:lng,:fa,true,'customer',NOW(),NOW()) RETURNING id
                """), {"rid": customer_id, "l1": address.get("address_line_1"), "city": address.get("city"),
                       "pin": address.get("pincode"), "lat": address.get("latitude"),
                       "lng": address.get("longitude"), "fa": full_addr})).scalar_one()

            booking_id = (await session.execute(text("""
                INSERT INTO bookings (
                    customer_id, customer_vehicle_id, service_centre_id,
                    booking_datetime, booking_slot, pickup_facility, drop_facility,
                    pickup_address_id, address_id, status, booking_type, initiated_by_app,
                    estimated_price, customer_comment, vehicle_no, first_name, last_name, phone_number,
                    created_by_user_type, created_by_user_name, "createdAt", "updatedAt"
                ) VALUES (
                    :cid,:cv_id,:sc_id,:bdate,:bslot,:pickup,:drop_fac,
                    :pad_id,:pad_id,'requested','ai_agent','ai_agent',
                    :price,:comment,:vno,:fn,:ln,:phone,'customer',:cname,NOW(),NOW()
                ) RETURNING id
            """), {
                "cid": customer_id, "cv_id": customer_vehicle_id, "sc_id": service_centre_id,
                "bdate": booking_date, "bslot": booking_slot,
                "pickup": mode == "pickup", "drop_fac": mode == "drop",
                "pad_id": pickup_address_id, "price": estimated_price, "comment": customer_comment,
                "vno": snap["vehicle_no"], "fn": snap["first_name"], "ln": snap["last_name"],
                "phone": snap["phone_number"],
                "cname": f"{snap['first_name']} {snap['last_name'] or ''}".strip(),
            })).scalar_one()

            for svc_id in (service_ids or []):
                vs = (await session.execute(text("""
                    SELECT vs.price, vs.discount_percent, s.name FROM vehicle_services vs
                    JOIN services s ON s.id=vs.service_id
                    WHERE vs.service_id=:sid AND vs.service_centre_id=:sc_id AND vs.is_active=true LIMIT 1
                """), {"sid": svc_id, "sc_id": service_centre_id})).mappings().first()
                price = float(vs["price"] or 0) if vs else 0.0
                disc  = float(vs["discount_percent"] or 0) if vs else 0.0
                await session.execute(text("""
                    INSERT INTO booking_services (booking_id, service_id, status, item_type,
                        selling_price, discount_percent, name, created_by_user_type, "createdAt", "updatedAt")
                    VALUES (:bid,:sid,'open','service',:sell,:disc,:nm,'customer',NOW(),NOW())
                """), {"bid": booking_id, "sid": svc_id,
                       "sell": round(price - price * disc / 100, 2), "disc": disc,
                       "nm": vs["name"] if vs else None})

            for pkg_id in (package_ids or []):
                pkg = (await session.execute(
                    text("SELECT name, price FROM service_packages WHERE id=:pid AND is_active=true LIMIT 1"),
                    {"pid": pkg_id})).mappings().first()
                await session.execute(text("""
                    INSERT INTO booking_services (booking_id, service_id, status, item_type,
                        selling_price, name, created_by_user_type, "createdAt", "updatedAt")
                    VALUES (:bid,:pid,'open','package',:price,:nm,'customer',NOW(),NOW())
                """), {"bid": booking_id, "pid": pkg_id,
                       "price": float(pkg["price"]) if pkg else 0.0,
                       "nm": pkg["name"] if pkg else None})

            await session.commit()
            return ToolResult(tool_name=self.name, success=True, data={
                "booking_id": booking_id, "status": "requested",
                "service_centre_id": service_centre_id, "booking_date": booking_date,
                "booking_slot": booking_slot, "mode": mode, "estimated_price": estimated_price,
                "services_booked": len(service_ids or []), "packages_booked": len(package_ids or []),
                "confirmation_message": (
                    f"Booking confirmed! Your booking ID is #{booking_id}. "
                    f"Service scheduled on {booking_date} at {booking_slot}."
                ),
            })
        except Exception as e:
            await session.rollback()
            return ToolResult(tool_name=self.name, success=False, error=str(e))


class GetBookingHistoryTool(BaseTool):
    name = "get_booking_history"
    description = (
        "Fetch last N bookings for a customer with garage name, services list, "
        "mode (pickup/walkin/drop), status, price, and rating given to each garage. "
        "For behavioral analysis and 'book again' quick-flow. "
        "Provide phone_number (str) OR customer_id (int). Optional: limit (int, default 10)."
    )

    async def execute(self, session, phone_number: str | None = None,
                      customer_id: int | None = None, limit: int = 10, **kwargs):
        try:
            if not phone_number and not customer_id:
                return ToolResult(tool_name=self.name, success=False, error="Provide phone_number or customer_id.")
            rows = (await session.execute(text("""
                SELECT b.id AS booking_id, b.booking_datetime AS booking_date,
                    b.booking_slot, b.service_centre_id AS garage_id,
                    COALESCE(sc.garage_name, sc.name) AS garage_name,
                    sc.phone_number AS garage_phone,
                    b.pickup_facility, b.drop_facility, b.status,
                    b.estimated_price, b.customer_comment, b.vehicle_no, b.booking_type,
                    ARRAY_AGG(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) AS services,
                    MAX(rt.rate) AS rating_given
                FROM bookings b
                LEFT JOIN service_centres sc ON sc.id=b.service_centre_id
                LEFT JOIN customers c ON c.id=b.customer_id
                LEFT JOIN booking_services bs ON bs.booking_id=b.id
                LEFT JOIN services s ON s.id=bs.service_id
                LEFT JOIN ratings rt ON rt.service_centre_id=b.service_centre_id AND rt.customer_id=b.customer_id
                WHERE (:phone IS NULL OR RIGHT(c.phone_number,10)=RIGHT(:phone,10))
                  AND (:cid IS NULL OR b.customer_id=:cid)
                GROUP BY b.id, sc.garage_name, sc.name, sc.phone_number
                ORDER BY b."createdAt" DESC LIMIT :lim
            """), {"phone": phone_number, "cid": customer_id, "lim": limit})).mappings().all()

            history = []
            for r in rows:
                mode = "pickup" if r["pickup_facility"] else ("drop" if r["drop_facility"] else "walkin")
                history.append({
                    "booking_id": r["booking_id"],
                    "booking_date": str(r["booking_date"]) if r["booking_date"] else None,
                    "booking_slot": str(r["booking_slot"]) if r["booking_slot"] else None,
                    "garage_id": r["garage_id"], "garage_name": r["garage_name"],
                    "garage_phone": r["garage_phone"], "mode": mode, "status": r["status"],
                    "estimated_price": r["estimated_price"], "customer_comment": r["customer_comment"],
                    "vehicle_no": r["vehicle_no"], "booking_type": r["booking_type"],
                    "services": r["services"] or [],
                    "rating_given": float(r["rating_given"]) if r["rating_given"] else None,
                })
            return ToolResult(tool_name=self.name, success=True, data={"bookings": history, "count": len(history)})
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=str(e))
