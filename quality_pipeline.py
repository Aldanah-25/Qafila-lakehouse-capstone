
import duckdb
from pathlib import Path

LABS = Path(__file__).resolve().parent
RAW = LABS / "data/raw"
DB = LABS / "artifacts/capstone/qafila.duckdb"

def run():
    assert DB.exists(), "Run the official SDAIA pipeline first"
    con = duckdb.connect(str(DB))

    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS quarantine")
        con.execute("CREATE SCHEMA IF NOT EXISTS incremental")

        # Quarantine invalid payment amounts
        con.execute("""
            CREATE OR REPLACE TABLE quarantine.invalid_payments AS
            SELECT *,
                   'NON_POSITIVE_AMOUNT' AS rejection_reason
            FROM raw.payments
            WHERE amount IS NULL OR amount <= 0
        """)

        # Quarantine invalid order quantities
        con.execute("""
            CREATE OR REPLACE TABLE quarantine.invalid_order_items AS
            SELECT *,
                   'NON_POSITIVE_QUANTITY' AS rejection_reason
            FROM raw.order_items
            WHERE quantity IS NULL OR quantity <= 0
        """)



        # Normalize Arabic digits and decimal separators
        con.execute("""
            CREATE OR REPLACE TABLE quarantine.invalid_supplier_prices AS
            WITH normalized AS (
                SELECT *,
                    TRANSLATE(
                        COALESCE(cost_sar, unit_cost),
                        '٠١٢٣٤٥٦٧٨٩٫٬',
                        '0123456789.,'
                    ) AS normalized_price
                FROM raw.supplier_prices
            ),
            parsed AS (
                SELECT *,
                    TRY_CAST(
                        REPLACE(normalized_price, ',', '.')
                        AS DOUBLE
                    ) AS parsed_price
                FROM normalized
            )
            SELECT * EXCLUDE (normalized_price, parsed_price),
                   CASE
                       WHEN parsed_price IS NULL
                           THEN 'INVALID_PRICE_FORMAT'
                       ELSE 'NON_POSITIVE_UNIT_COST'
                   END AS rejection_reason
            FROM parsed
            WHERE parsed_price IS NULL OR parsed_price <= 0
        """)

        # Incremental payment ingestion using stable event IDs
        con.execute("""
            CREATE TABLE IF NOT EXISTS incremental.payments AS
            SELECT * FROM raw.payments WHERE 1=0
        """)

        con.execute("""
            DELETE FROM incremental.payments
            WHERE payment_id IN (
                SELECT payment_id FROM raw.payments
                WHERE payment_id IS NOT NULL
            )
        """)

        con.execute("""
            INSERT INTO incremental.payments
            SELECT * EXCLUDE (rn)
            FROM (
                SELECT *,
                       ROW_NUMBER() OVER (
                           PARTITION BY payment_id
                           ORDER BY TRY_CAST(updated_at AS TIMESTAMP) DESC
                                    NULLS LAST
                       ) AS rn
                FROM raw.payments
                WHERE payment_id IS NOT NULL
            )
            WHERE rn = 1
        """)

        # Incremental delivery events
        con.execute("""
            CREATE TABLE IF NOT EXISTS incremental.delivery_events AS
            SELECT * FROM raw.delivery_events WHERE 1=0
        """)

        con.execute("""
            INSERT INTO incremental.delivery_events
            SELECT * EXCLUDE (rn)
            FROM (
                SELECT *,
                       ROW_NUMBER() OVER (
                           PARTITION BY event_id
                           ORDER BY TRY_CAST(ingest_time AS TIMESTAMP)
                                    DESC NULLS LAST
                       ) AS rn
                FROM raw.delivery_events
                WHERE event_id IS NOT NULL
            )
            WHERE rn = 1
              AND event_id NOT IN (
                  SELECT event_id
                  FROM incremental.delivery_events
                  WHERE event_id IS NOT NULL
              )
        """)

        for schema, table in [
            ("quarantine", "invalid_payments"),
            ("quarantine", "invalid_order_items"),
            ("incremental", "payments"),
            ("incremental", "delivery_events")
        ]:
            count = con.execute(
                f"SELECT COUNT(*) FROM {schema}.{table}"
            ).fetchone()[0]
            print(f"{schema}.{table}: {count:,} rows")

        print("Quality extension completed!")
    finally:
        con.close()

if __name__ == "__main__":
    run()
