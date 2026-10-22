# Qafila Lakehouse — Data Engineering Capstone

**Program:** SDAIA Academy Data Engineering  
**Capstone option:** Option 1 — Qafila Lakehouse

## Problem
Qafila operates across orders, payments, deliveries, suppliers,
and customer reviews. This project integrates these sources into
an analytics-ready lakehouse to support operational reporting
and data quality monitoring.

## Sources

| Source | Type | Loading |
|---|---|---|
| Qafila OLTP | SQLite database | Snapshot ingestion |
| Payments | API-style JSONL extract | Snapshot + keyed extension |
| Delivery events | Event JSONL | Snapshot + event-ID deduplication |
| Supplier prices | Weekly CSV files | Snapshot |
| Customer reviews | CSV | Snapshot |

All sample data is synthetic.

## Architecture

SQLite / JSONL / CSV
        |
        v
Dagster ingestion
        |
        v
DuckDB raw (Bronze)
        |
        v
dbt staging (Silver)
        |
        v
dbt marts (Gold)
        |
        v
Iceberg publication

Additional extension:
raw -> quarantine and incremental tables

The official starter provides Dagster orchestration,
dbt transformations, tests, contract checks, and Iceberg output.

## Data model

The dbt project contains customer, order, product and other
analytical models, including the order fact and daily city
sales mart. The order fact is modeled at order grain;
the daily city sales mart is aggregated by date and city.

See dbt_qafila/models for the full SQL definitions.

## Quality and observability

The pipeline executes dbt tests and Dagster asset checks.
The verified standalone run reported:
- 30 assets materialized
- 45 checks
- dbt: 63 PASS, 3 WARN, 0 ERROR

Observed data quality findings:
- 16 payments with non-positive amounts
- 142 order items with non-positive quantities
- 4 supplier prices with non-positive costs
- 258 order/payment reconciliation discrepancies

Custom quarantine tables capture invalid payment amounts,
order quantities, and supplier prices. Supplier costs are
normalized across Arabic digits and decimal separator formats.

These findings remain documented warnings in the original
pipeline; quarantine does not automatically remove them
from all downstream marts.

## Incremental loads and re-runs

The extension uses payment_id to refresh payment records
and event_id to avoid inserting duplicate delivery events.
The baseline ingestion uses replacement snapshots.

The unified pipeline was successfully run with:

    python run_pipeline.py

A separate rerun/idempotency test should be retained as
evidence before claiming complete idempotency under
updates, late-arriving events, and changing source data.

## Governance note

The dataset is synthetic. Customer contact details,
national identifiers, and bank account identifiers should
be treated as sensitive.

Raw datasets and generated databases are excluded from Git.
Access controls, masking and deletion handling would need
additional implementation before use with real personal data.

See GOVERNANCE.md.

## Reproduce

Use a Python environment compatible with
requirements-colab.txt.

1. Install dependencies:

    pip install -r requirements-colab.txt

2. Generate the synthetic Qafila source files using
   prepare_data.py. Check its CLI/help or source for the
   appropriate invocation.

3. Confirm the generated files are under data/raw.

4. Run the end-to-end pipeline:

    python run_pipeline.py

5. Optional Dagster UI:

    dagster dev -f capstone/pipeline.py

The runner uses project-local paths. The DuckDB database
and lakehouse are written under artifacts/capstone/.

## Limitations and next steps

- Sources are simulated batch extracts, not live APIs or streams.
- Full snapshot ingestion remains in the official raw assets.
- Quarantine does not yet enforce downstream exclusion.
- Order/payment reconciliation warnings need root-cause analysis.
- Production PII masking, retention, and erasure are not implemented.
- Incremental loading needs tests for updates and late arrivals.
- Large-scale operation would require partitions and backfills.

## Attribution

Based on the official SDAIA Academy Qafila starter:
https://github.com/SDAIAAcademy/data-engineering

Custom extensions: quality quarantine, keyed loading,
verification, project packaging and documentation.
