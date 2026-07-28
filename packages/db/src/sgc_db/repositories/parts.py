from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from sgc_db.models.catalog import Part, PartFitment, PartInterchange


class PartsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_parts(
        self,
        query: str | None = None,
        oem_number: str | None = None,
        make: str | None = None,
        model: str | None = None,
        fuel_type: str | None = None,
        limit: int = 20,
    ) -> list[Part]:
        stmt = select(Part)

        if oem_number:
            stmt = stmt.where(Part.oem_part_number.ilike(f"%{oem_number}%"))
        elif query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Part.part_name.ilike(pattern),
                    Part.oem_part_number.ilike(pattern),
                    Part.search_tags.any(query.lower()),
                )
            )

        if make or model or fuel_type:
            stmt = stmt.join(PartFitment).where(PartFitment.part_id == Part.part_id)
            if make:
                stmt = stmt.where(PartFitment.vehicle_make.ilike(f"%{make}%"))
            if model:
                stmt = stmt.where(PartFitment.vehicle_model.ilike(f"%{model}%"))
            if fuel_type:
                stmt = stmt.where(PartFitment.fuel_type.ilike(f"%{fuel_type}%"))

        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_part_by_id(self, part_id: str) -> Part | None:
        result = await self.session.execute(select(Part).where(Part.part_id == part_id))
        return result.scalar_one_or_none()

    async def check_fitment(
        self,
        part_id: str,
        make: str,
        model: str,
        fuel_type: str | None = None,
        year: int | None = None,
    ) -> bool:
        stmt = select(PartFitment).where(
            PartFitment.part_id == part_id,
            PartFitment.vehicle_make.ilike(f"%{make}%"),
            PartFitment.vehicle_model.ilike(f"%{model}%"),
        )
        if fuel_type:
            stmt = stmt.where(PartFitment.fuel_type.ilike(f"%{fuel_type}%"))
        if year:
            stmt = stmt.where(
                (PartFitment.year_from.is_(None) | (PartFitment.year_from <= year)),
                (PartFitment.year_to.is_(None) | (PartFitment.year_to >= year)),
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_alternates(self, part_id: str) -> list[Part]:
        stmt = (
            select(Part)
            .join(PartInterchange, PartInterchange.alternate_part_id == Part.part_id)
            .where(PartInterchange.part_id == part_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
