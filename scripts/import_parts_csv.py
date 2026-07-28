#!/usr/bin/env python3
"""Import spare parts from CSV into agent catalog."""

import asyncio
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "db" / "src"))

from sgc_db.models.catalog import Part, PartFitment
from sgc_db.models.sync import ImportJob
from sgc_db.session import get_session_factory


async def import_parts_csv(csv_path: str) -> None:
    factory = get_session_factory()
    async with factory() as session:
        job = ImportJob(source_name=csv_path, job_type="parts_csv", status="running")
        session.add(job)
        await session.commit()

        count = 0
        with Path(csv_path).open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                part = Part(
                    part_id=row["part_id"],
                    sku=row.get("sku", row["part_id"]),
                    oem_part_number=row.get("oem_part_number"),
                    part_name=row["part_name"],
                    category=row.get("category"),
                    part_brand=row.get("part_brand"),
                    stock_quantity=int(row.get("stock_quantity", 0)),
                    selling_price=float(row["selling_price"]) if row.get("selling_price") else None,
                    search_tags=row.get("search_tags", "").split("|") if row.get("search_tags") else [],
                )
                session.add(part)

                if row.get("vehicle_make") and row.get("vehicle_model"):
                    session.add(PartFitment(
                        part_id=row["part_id"],
                        vehicle_make=row["vehicle_make"],
                        vehicle_model=row["vehicle_model"],
                        fuel_type=row.get("fuel_type"),
                        year_from=int(row["year_from"]) if row.get("year_from") else None,
                        year_to=int(row["year_to"]) if row.get("year_to") else None,
                    ))
                count += 1

        job.status = "completed"
        job.records_processed = count
        await session.commit()
        print(f"Imported {count} parts from {csv_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_parts_csv.py <path/to/parts.csv>")
        sys.exit(1)
    asyncio.run(import_parts_csv(sys.argv[1]))
