# ADR-004: Backup and Failover Strategy - Cloud Primary, Local Secondary

## Status
Accepted

## Date
2026-05-07

## Context
The platform runs on AWS free tier as its primary infrastructure. The free tier has usage limits that, if exceeded, will incur costs. There is also a risk of account issues, service disruptions, or the free-tier window expiring without a paid upgrade path being available.

A secondary local environment is designed to:
- Mirror all cloud data daily so no data is ever lost if the cloud layer becomes unavailable.
- Serve as a full failover environment that can run the entire pipeline independently.
- Eliminate vendor lock-in risk at the data layer.

## Decision Drivers
- Budget: near-zero, no fallback paid plan available.
- Data safety: all ingested, transformed, and predicted data must survive a cloud outage.
- Continuity: the pipeline must be able to run locally if AWS free tier is breached or the account is disrupted.
- Simplicity: the local environment must require no special infrastructure beyond a personal laptop.

---

## Architecture: Primary Layer (AWS Cloud)

| Component | Service | Role |
| --- | --- | --- |
| Raw data | S3 Bronze (Parquet) | Immutable OHLCV ingestion |
| Clean data | S3 Silver (Iceberg) | Conformed and enriched |
| Features and labels | S3 Gold (Iceberg) | ML-ready datasets |
| Predictions | DynamoDB | API key-value store |
| Pipeline audit | DynamoDB with TTL | Run history |
| Model metadata | SQLite on EC2 | Experiment tracking |
| Model artifacts | S3 | Versioned model files |
| Orchestration | EventBridge + Lambda | Daily schedule |
| API | API Gateway + Lambda | Prediction serving |
| Monitoring | CloudWatch + SNS | Alerts and logs |

---

## Architecture: Secondary Layer (Local Laptop)

### Required Software to Install Once
- Python 3.11 or later
- AWS CLI (for S3 sync commands)
- PyIceberg (Iceberg table read and write)
- DuckDB (analytical queries on Iceberg)
- PostgreSQL (already installed on laptop — used as secondary prediction and metadata store)
- psycopg2 or psycopg3 (Python PostgreSQL client)
- SQLite (built into Python — retained as lightweight fallback only)
- yfinance (data ingestion fallback)
- pandas, pyarrow (data processing)
- Git (code versioning, already linked to GitHub)

All software is free and open source. No license cost.
PostgreSQL is already installed on the local machine; no additional setup required for the DB engine.

### Local Directory Mirror
The local machine maintains a mirror of the cloud data structure:

```
~/project_intelligent_backup/
  data/
    bronze/       <- daily sync from S3 bronze
    silver/       <- daily sync from S3 silver (Iceberg files)
    gold/         <- daily sync from S3 gold (Iceberg files)
    reference/    <- universe selection snapshots
  models/         <- daily sync from S3 model artifacts
  audit/          <- daily export from DynamoDB audit table as JSON
```

Predictions and model metadata are stored directly in the local PostgreSQL instance, not as flat files.

### Daily Sync Design
Every day after the cloud pipeline completes, a local sync job runs:

1. S3 to local sync
   - Pull all new bronze, silver, gold, reference, and model artifact files written today.
   - Use incremental sync: only download files not already present locally.

2. DynamoDB predictions to local PostgreSQL
   - Export today's new prediction records from DynamoDB.
   - Upsert into the local PostgreSQL predictions table using symbol + prediction_date as the unique key.
   - Schema is identical to DynamoDB attribute definitions (see ADR-003 schema alignment contract).

3. DynamoDB audit logs to local PostgreSQL
   - Export today's new pipeline audit records from DynamoDB.
   - Insert into the local PostgreSQL pipeline_audit table.
   - Also write a JSON copy to the local audit/ directory for human readability.

4. Model metadata sync
   - Copy the SQLite model metadata file from EC2 to a local staging path.
   - Migrate any new model and experiment records from SQLite staging into the local PostgreSQL models and experiments tables.
   - Local PostgreSQL becomes the single source of truth for metadata in failover mode.

5. Integrity check
   - Verify file counts match between cloud S3 and local directory after sync.
   - Verify row counts match between DynamoDB exports and local PostgreSQL tables.
   - Log any discrepancy; alert if counts diverge by more than 1%.

---

## Failover Design

### Failover Triggers
Any of the following conditions triggers a move to local-primary mode:

| Trigger | Detection Method |
| --- | --- |
| AWS free-tier cost alarm fires | CloudWatch billing alert |
| DynamoDB RCU or WCU critical alarm fires | CloudWatch capacity alert |
| S3 storage critical alarm fires | CloudWatch storage alert |
| AWS account suspended or inaccessible | Manual detection during daily pipeline check |
| Lambda invocation limit approaching | CloudWatch Lambda metrics |
| API Gateway request limit approaching | CloudWatch API metrics |

### Failover Steps (Architecture Level)
1. Confirm local sync is current (last sync within 24 hours).
2. Confirm local PostgreSQL is running and prediction + metadata tables are populated.
3. Switch ingestion source: yfinance runs locally instead of Lambda.
4. Switch pipeline execution: run bronze, silver, gold pipeline scripts locally.
5. Switch model training: run training scripts locally using local Gold Iceberg tables.
6. Switch prediction writes: pipeline writes predictions to local PostgreSQL instead of DynamoDB.
7. Switch metadata writes: pipeline writes model metadata to local PostgreSQL instead of EC2 SQLite.
8. Switch prediction serving: run local API script (FastAPI or Flask) reading from local PostgreSQL.
9. Notify via local log that failover mode is active; document date and trigger reason.

### Recovery to Cloud (When Cloud Becomes Available Again)
1. Confirm cloud environment is healthy and within free-tier limits.
2. Sync all locally produced S3 data back to cloud (bronze, silver, gold, models).
3. Replay any missing DynamoDB prediction writes from local PostgreSQL using a backfill job.
4. Replay any missing DynamoDB audit writes from local PostgreSQL or local JSON copies.
5. Sync any new model metadata records from local PostgreSQL back to EC2 SQLite.
6. Re-enable EventBridge schedule and Lambda orchestration.
7. Run one full pipeline cycle in cloud to confirm end-to-end health.
8. Document the failover window: start date, end date, trigger, and resolution.

---

## Guardrails

### G1 - Daily Sync Must Complete
- The local sync job must run and complete successfully every day after the cloud pipeline.
- A sync failure triggers a local alert (log entry and optional desktop notification).
- Two consecutive sync failures trigger a manual investigation before the next pipeline run.

### G2 - Sync Lag Limit
- Local data must never be more than 2 calendar days behind the cloud state.
- If sync lag exceeds 2 days, local environment is considered unsafe for failover until re-synced.

### G3 - Failover Readiness Check
- Once per week, verify that the local environment can run the full pipeline end-to-end on local data.
- A failed readiness check is logged and must be resolved within 3 days.

### G4 - No Divergence Between Primary and Secondary
- After each sync, row counts in local predictions and audit stores must match cloud exports within 1%.
- Divergence above 1% triggers an investigation and halts the next sync until resolved.

### G5 - Failover Documentation
- Every failover event must be documented with: trigger, start date, end date, data gap (if any), and resolution.
- Undocumented failover events are treated as governance violations.

### G6 - Cloud Billing Alert (Hard Gate)
- A CloudWatch billing alert is configured at $0.10 (ten cents) to provide maximum early warning before any real cost is incurred.
- Billing alert fires before any service limit is hit, giving time to either reduce usage or switch to local.

---

## Local PostgreSQL Schema (Secondary Store)
The local PostgreSQL instance mirrors the DynamoDB schema exactly per the ADR-003 alignment contract.

Database name: project_intelligent_local

Tables:
- predictions: symbol, prediction_date, horizon, cap_tier, prediction_direction, prediction_return, confidence, model_version, gold_snapshot_id, created_at
- pipeline_audit: job_type, run_id, input_snapshot, output_snapshot, row_count_in, row_count_out, status, duration_seconds, error_message, created_at
- models: model_id, model_type, horizon, cap_tier, gold_snapshot_id, training_date, hyperparameters, status, created_at
- experiments: experiment_id, model_id, validation_metric, backtest_sharpe, backtest_drawdown, promoted_flag, created_at

This schema is identical to the cloud schema, so switching between primary and secondary requires only a connection string change.

---

## Cost of Local Environment
- Hardware: existing personal laptop, no additional cost.
- Software: all open source, no license cost. PostgreSQL already installed.
- Network: standard home internet for daily sync, no additional cost.
- Storage: approximately 500 MB to 2 GB per year for a 30-symbol swing universe.

---

## Consequences

### Positive
- Complete data safety: no data loss if cloud becomes unavailable.
- Zero additional cost for the secondary environment.
- No vendor lock-in: the entire pipeline can run on commodity hardware.
- Immediate failover capability with no provisioning delay.

### Negative
- Daily sync job must be maintained and monitored.
- Local compute is slower than cloud Lambda for large training jobs.
- Local API is not publicly accessible without additional networking setup.
- Manual process required to re-sync local data back to cloud after recovery.

## References
- Architecture constraint: docs/architecture/01_scope_and_constraints.md
- Platform and MLOps: docs/architecture/06_platform_mlops_observability_security.md
- Database decision: docs/adr/ADR-003-database-decision.md
- Medallion architecture: docs/architecture/03_data_architecture_medallion.md
