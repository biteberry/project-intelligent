# ADR-003: Database and Metadata Storage Decision

## Status
Accepted - DynamoDB for predictions and audit logs; SQLite for model metadata on EC2; PostgreSQL deferred on cloud but active on local laptop as secondary store (see ADR-004)

## Date
2026-05-07

## Context
The platform requires persistent storage for several distinct data types that do not fit naturally into the medallion S3 layers:
- Daily prediction outputs that the API must serve with low latency key lookups.
- Pipeline run audit logs for traceability and guardrail evidence.
- Model metadata and experiment tracking records.
- Universe selection audit snapshots.
- API response cache for latest prediction per symbol.

A relational database like PostgreSQL was evaluated as a single unified store for all of these needs. The evaluation was conducted under the hard constraint of near-zero budget on AWS free tier with no time-limited cost risk.

## Decision Drivers
- Budget: near-zero, AWS free tier, must be sustainable beyond 12 months.
- Access patterns: mostly key-based lookups and append-only writes, not complex joins.
- Operational complexity: no DBA, no managed cluster, minimal maintenance.
- Consistency with existing stack: DuckDB and Iceberg already cover all analytical queries.
- Immutability: audit logs and selection snapshots must not be editable.

## Options Evaluated

### Option 1 - PostgreSQL on AWS RDS
- Fully managed, familiar SQL interface.
- AWS free tier: 750 instance-hours per month for 12 months only, then paid.
- After free period: minimum ~$15 per month for db.t3.micro.
- Introduces ongoing cost risk after the 12-month window.
- Overkill for key-based prediction lookups and append-only audit logs.
- Verdict: rejected. Time-limited free tier creates unsustainable cost risk.

### Option 2 - PostgreSQL on EC2 t2.micro (Self-Managed)
- PostgreSQL software is free; EC2 t2.micro is free tier for 12 months.
- t2.micro has 1 GB RAM total, shared with pipeline jobs and the OS.
- Running PostgreSQL alongside Python pipeline jobs causes RAM contention.
- Self-managed: backups, patching, and recovery are manual operational burden.
- Verdict: viable in theory but RAM contention and ops burden make it fragile.

### Option 3 - AWS DynamoDB (Selected for Predictions and Audit Logs)
- 25 GB storage, 25 WCU, 25 RCU free forever under AWS free tier (not time-limited).
- Purpose-built for key-based lookups: symbol + date as partition and sort key.
- TTL support for automatic expiry of stale audit records.
- Fully managed: zero operational overhead.
- Not suitable for complex relational queries or joins.
- Verdict: selected for predictions, API cache, and pipeline audit logs.

### Option 4 - SQLite on EC2 (Selected for Model Metadata)
- Zero cost: file-based, no server, no license.
- Ideal for low-volume structured metadata: model versions, experiment runs, hyperparameters.
- Single writer at a time: acceptable for batch pipeline usage pattern.
- File stored on EC2 instance with S3 backup on each pipeline run.
- Not suitable for high-concurrency API reads.
- Verdict: selected for model metadata and experiment tracking.

### Option 5 - DuckDB on Iceberg Gold (Already Decided in ADR-002)
- Covers all analytical query needs: feature validation, backtest queries, drift checks.
- No additional storage required; queries run directly on existing Gold Iceberg tables.
- Verdict: already in stack; no additional database needed for analytics.

### Option 6 - S3 JSON Snapshots (Selected for Universe Selections)
- Universe selection outputs are small, infrequent, and read-only after creation.
- Storing as versioned JSON on S3 gives immutability, audit trail, and zero cost.
- No query engine needed; files are read in full by the pipeline once per week.
- Verdict: selected for universe selection snapshots and schema/contract registry.

## Decision
PostgreSQL is not adopted at this time.

The storage layer is split by access pattern and data type:

| Data Type | Store | Justification |
| --- | --- | --- |
| Daily predictions | DynamoDB | Fast key lookup, free forever |
| API prediction cache | DynamoDB | Same table, latest item per symbol |
| Pipeline audit logs | DynamoDB with TTL | Append-only, auto-expiry, free |
| Model metadata and experiments | SQLite on EC2 | Low volume, zero cost, simple |
| Universe selection snapshots | S3 JSON | Immutable, versioned, zero cost |
| Schema and contract registry | S3 JSON | Versioned, zero cost |
| Analytical queries | DuckDB on Iceberg Gold | Already in stack |
| Raw and curated data | S3 Parquet and Iceberg | Medallion layers, already decided |
| **Secondary predictions (failover)** | **PostgreSQL on local laptop** | **Already installed; mirrors DynamoDB schema** |
| **Secondary metadata (failover)** | **PostgreSQL on local laptop** | **Consolidates SQLite records into single local DB** |

## DynamoDB Table Design

### predictions table
- Partition key: symbol
- Sort key: prediction_date
- Attributes: horizon, cap_tier, prediction_direction, prediction_return, confidence, model_version, gold_snapshot_id, created_at

### pipeline_audit table
- Partition key: job_type
- Sort key: run_id (timestamp-based)
- Attributes: input_snapshot, output_snapshot, row_count_in, row_count_out, status, duration_seconds, error_message
- TTL: audit_expiry (set to 90 days from run time)

## SQLite Schema Scope
Tables for model metadata store:
- models: model_id, model_type, horizon, cap_tier, gold_snapshot_id, training_date, hyperparameters, status
- experiments: experiment_id, model_id, validation_metric, backtest_sharpe, backtest_drawdown, promoted_flag, created_at

## Consequences

### Positive
- Zero sustained cost: DynamoDB free tier is permanent, not time-limited.
- No RAM contention: DynamoDB is fully managed, SQLite is file-based.
- Access patterns are served correctly: key lookups in DynamoDB, structured metadata in SQLite.
- Analytical queries already covered by DuckDB on Iceberg; no duplication.
- Immutability preserved: audit records are TTL-expired, not deleted or edited.
- Local PostgreSQL on the laptop provides a fully functional secondary store at zero cost; already installed.
- Local PostgreSQL schema is identical to DynamoDB layout, so failover requires only a connection string change.
- When universe grows beyond 200 symbols, migration path to cloud PostgreSQL is straightforward because the local PostgreSQL instance has already been validating the schema in production.

### Negative
- No single unified query interface across all data types.
- DynamoDB does not support complex joins; cross-entity analytics require DuckDB on Gold.
- SQLite has a single writer limit; concurrent pipeline writes require serialization.
- SQLite file must be backed up to S3 after each write to avoid data loss on EC2 restart.

## Guardrails Added by This Decision
- Prediction records must include all mandatory fields before DynamoDB write; incomplete records are rejected.
- Pipeline audit records must be written for every job run; jobs without audit records are flagged as non-compliant.
- SQLite file must be backed up to S3 after every model metadata write.
- No direct console or manual writes to DynamoDB prediction or audit tables; all writes go through the pipeline.
- DynamoDB TTL policy is defined in the governance policy document and must not be disabled.
- Local PostgreSQL schema must stay in sync with DynamoDB attribute definitions; any DynamoDB schema change must be mirrored to the local PostgreSQL tables before the change is deployed to cloud.
- Local PostgreSQL is secondary only; all primary writes go to DynamoDB; local receives data via daily sync, not direct pipeline write during normal operations.

## Revisit Trigger
- Revisit if universe grows beyond 200 symbols and DynamoDB query patterns become complex.
- Revisit if multi-user dashboards require complex relational joins that DynamoDB cannot support.
- Revisit if experiment tracking volume outgrows SQLite single-file practical limits.
- Revisit at end of AWS 12-month free period to confirm DynamoDB free tier usage remains within permanent free limits.

---

## PostgreSQL Migration Path (When Symbol Count Crosses 200)

### Why 200 is the Threshold
Below 200 symbols, DynamoDB key-based lookups and simple scans are fast and within free-tier RCU limits.
Above 200 symbols, analytical access patterns (cross-symbol filtering, cap-tier joins, multi-strategy dashboards) become increasingly expensive and awkward in DynamoDB. A relational engine handles these patterns natively.

### Migration is Designed to Be Easy
The DynamoDB schema is intentionally kept relational-compatible from day one:
- All field names and types are identical to what a PostgreSQL table would use.
- No nested JSON blobs are stored; all attributes are flat scalar values.
- Foreign key relationships are explicit in field naming (e.g., model_version, gold_snapshot_id) even though DynamoDB does not enforce them.
- This means migration is a straight read-from-DynamoDB, write-to-PostgreSQL operation with no data transformation.

### Migration Steps (Architecture Level)
1. Provision PostgreSQL on RDS free tier (available for 12 months) or on EC2 if budget constraint holds.
2. Create PostgreSQL tables using the same schema as DynamoDB attribute definitions.
3. Run a one-time backfill job reading all DynamoDB records and writing to PostgreSQL.
4. Validate row counts and spot-check records across both stores.
5. Switch the API and pipeline connection string from DynamoDB to PostgreSQL.
6. Run both stores in parallel for 5 business days to confirm zero discrepancy.
7. Decommission DynamoDB predictions and audit tables after parallel validation passes.

### Schema Alignment Contract
DynamoDB attributes are designed to map directly to PostgreSQL columns:

predictions table:
- symbol (text, partition key → primary key)
- prediction_date (date, sort key → primary key)
- horizon (text)
- cap_tier (text)
- prediction_direction (integer)
- prediction_return (numeric)
- confidence (numeric)
- model_version (text)
- gold_snapshot_id (text)
- created_at (timestamp)

pipeline_audit table:
- job_type (text)
- run_id (text, timestamp-based)
- input_snapshot (text)
- output_snapshot (text)
- row_count_in (integer)
- row_count_out (integer)
- status (text)
- duration_seconds (numeric)
- error_message (text)

---

## Symbol Count Alert Design

### Alert: Universe Size Warning
- Metric: count of distinct active symbols in the predictions table.
- Warning threshold: 150 symbols — early notice to begin migration planning.
- Critical threshold: 200 symbols — migration must begin within the current architecture cycle.
- Alert channel: CloudWatch alarm to SNS email.
- Cadence: evaluated on every weekly universe selection run.
- Responsible action on warning: begin PostgreSQL migration architecture review.
- Responsible action on critical: freeze universe expansion until migration is complete or approved.

### Alert: DynamoDB RCU Consumption Warning
- Metric: CloudWatch ConsumedReadCapacityUnits on predictions table.
- Warning threshold: 80% of free-tier RCU limit (25 RCU).
- Critical threshold: 95% of free-tier RCU limit.
- Alert channel: CloudWatch alarm to SNS email.
- Responsible action: investigate query pattern inefficiency or trigger migration review.

### Alert: DynamoDB WCU Consumption Warning
- Metric: CloudWatch ConsumedWriteCapacityUnits on predictions table.
- Warning threshold: 80% of free-tier WCU limit (25 WCU).
- Critical threshold: 95% of free-tier WCU limit.
- Alert channel: CloudWatch alarm to SNS email.

## References
- Architecture constraint: docs/architecture/01_scope_and_constraints.md
- Medallion data architecture: docs/architecture/03_data_architecture_medallion.md
- Platform and MLOps: docs/architecture/06_platform_mlops_observability_security.md
- Related ADRs: docs/adr/ADR-001-kafka-decision.md, docs/adr/ADR-002-iceberg-decision.md
