"""Inspect prod_pikpart database schema and sample data."""
import psycopg2
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_URL = "postgresql://postgres:xk916FJTbOEBsiUw@uatrestore.cxjvk9n7ljbw.ap-south-1.rds.amazonaws.com:5432/prod_pikpart"

TABLES = [
    "customers",
    "services",
    "customer_vehicles",
    "vehicle_services",
    "service_centre_services",
    "booking_services",
    "bookings",
    "vehicle_brands",
    "vehicle_categories",
]

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

for t in TABLES:
    print(f"\n{'='*80}")
    print(f"TABLE: {t}")
    print(f"{'='*80}")

    # Schema
    cur.execute(
        "SELECT column_name, data_type, is_nullable, column_default "
        "FROM information_schema.columns "
        f"WHERE table_name = '{t}' AND table_schema = 'public' "
        "ORDER BY ordinal_position"
    )
    rows = cur.fetchall()
    print("\nCOLUMNS:")
    for r in rows:
        print(f"  {r[0]:40s} | {r[1]:30s} | nullable={r[2]:3s} | default={r[3]}")

    # Row count
    cur.execute(f"SELECT COUNT(*) FROM public.{t}")
    count = cur.fetchone()[0]
    print(f"\nTOTAL ROWS: {count}")

    # Sample data (only first 3 rows for brevity, truncate long values)
    cur.execute(f"SELECT * FROM public.{t} LIMIT 3")
    cols = [d[0] for d in cur.description]
    sample_rows = cur.fetchall()
    print(f"\nSAMPLE DATA ({len(sample_rows)} rows):")
    for row in sample_rows:
        print("  ---")
        for col, val in zip(cols, row):
            val_str = str(val)
            if len(val_str) > 100:
                val_str = val_str[:100] + "..."
            print(f"    {col}: {val_str}")

conn.close()
print("\nDone.")
