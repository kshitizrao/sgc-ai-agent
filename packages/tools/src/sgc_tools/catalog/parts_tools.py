from decimal import Decimal

from sgc_db.repositories.parts import PartsRepository
from sgc_shared.types import SourceRef, ToolResult
from sgc_tools.registry import BaseTool


class SearchPartsTool(BaseTool):
    name = "search_parts"
    description = "Search spare parts by name, OEM number, or vehicle fitment"

    async def execute(self, session, query=None, oem_number=None, make=None, model=None, fuel_type=None, **kwargs):
        repo = PartsRepository(session)
        parts = await repo.search_parts(query=query, oem_number=oem_number, make=make, model=model, fuel_type=fuel_type)
        data = [
            {
                "part_id": p.part_id,
                "part_name": p.part_name,
                "oem_part_number": p.oem_part_number,
                "part_brand": p.part_brand,
                "stock_quantity": p.stock_quantity,
                "selling_price": float(p.selling_price) if p.selling_price else None,
                "bin_location": p.bin_location,
            }
            for p in parts
        ]
        refs = [SourceRef(table="catalog.parts", record_id=p["part_id"]) for p in data]
        return ToolResult(tool_name=self.name, success=True, data=data, source_refs=refs)


class CheckPartFitmentTool(BaseTool):
    name = "check_part_fitment"
    description = "Check if a part fits a specific vehicle"

    async def execute(self, session, part_id, make, model, fuel_type=None, year=None, **kwargs):
        repo = PartsRepository(session)
        fits = await repo.check_fitment(part_id, make, model, fuel_type, year)
        part = await repo.get_part_by_id(part_id)
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "part_id": part_id,
                "part_name": part.part_name if part else None,
                "fits": fits,
                "vehicle": {"make": make, "model": model, "fuel_type": fuel_type, "year": year},
            },
            source_refs=[SourceRef(table="catalog.part_fitment", record_id=part_id)],
        )


class SuggestAlternatesTool(BaseTool):
    name = "suggest_alternates"
    description = "Suggest interchangeable alternate parts when primary is out of stock"

    async def execute(self, session, part_id, **kwargs):
        repo = PartsRepository(session)
        alternates = await repo.get_alternates(part_id)
        data = [
            {
                "part_id": p.part_id,
                "part_name": p.part_name,
                "part_brand": p.part_brand,
                "part_type": p.part_type,
                "stock_quantity": p.stock_quantity,
                "selling_price": float(p.selling_price) if p.selling_price else None,
            }
            for p in alternates
        ]
        refs = [SourceRef(table="catalog.part_interchanges", record_id=part_id)]
        return ToolResult(tool_name=self.name, success=True, data=data, source_refs=refs)
