from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sgc_db.models.catalog import (
    PricingMatrix,
    ServiceInclusion,
    ServicePackage,
    VehicleSegment,
)


class ServicesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_packages(self) -> list[ServicePackage]:
        result = await self.session.execute(select(ServicePackage))
        return list(result.scalars().all())

    async def get_inclusions(self, package_id: str) -> list[ServiceInclusion]:
        result = await self.session.execute(
            select(ServiceInclusion).where(ServiceInclusion.package_id == package_id)
        )
        return list(result.scalars().all())

    async def get_pricing(self, package_id: str, segment_id: str) -> PricingMatrix | None:
        result = await self.session.execute(
            select(PricingMatrix).where(
                PricingMatrix.package_id == package_id,
                PricingMatrix.segment_id == segment_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_segment(self, segment_id: str) -> VehicleSegment | None:
        result = await self.session.execute(
            select(VehicleSegment).where(VehicleSegment.segment_id == segment_id)
        )
        return result.scalar_one_or_none()

    async def find_segment(
        self, body_type: str, fuel_type: str
    ) -> VehicleSegment | None:
        result = await self.session.execute(
            select(VehicleSegment).where(
                VehicleSegment.body_type.ilike(f"%{body_type}%"),
                VehicleSegment.fuel_type.ilike(f"%{fuel_type}%"),
            )
        )
        return result.scalar_one_or_none()
