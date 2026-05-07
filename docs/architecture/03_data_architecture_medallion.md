# 03 Data Architecture - Medallion

## Principle
Use bronze, silver, and gold zones to separate raw ingestion, conformed data, and analytics/ML-ready assets.

## Table Format Decision
- Bronze: plain Parquet on S3. Append-only, immutable via IAM object lock.
- Silver: Apache Iceberg on S3 via PyIceberg + DuckDB + AWS Glue Catalog.
- Gold: Apache Iceberg on S3 via PyIceberg + DuckDB + AWS Glue Catalog.

Iceberg gives Silver and Gold storage-enforced immutability, native time travel for point-in-time backtest queries, schema evolution as features grow, and snapshot ID references for reproducible model training. See ADR-002 for the full decision record.

## Immutability Mandate (All Layers)
Every layer in the medallion architecture is strictly immutable.
- No manual edits are permitted on any file or record in any layer.
- Data can only enter a layer through a controlled, versioned pipeline job.
- Any correction must be reprocessed through the pipeline as a new snapshot, never by editing existing data in place.
- All write access to storage is restricted to pipeline service identities only.
- Human users have read-only access at all times across all layers.
- Immutability is enforced at the storage level through access policies and bucket/object lock configurations.

---

## Bronze
- Raw OHLCV and source payloads.
- Append-only immutable ingestion snapshots.
- Partitioning by source, symbol, ingestion date.

### Bronze Immutability Rules
- Object lock enabled on S3 bucket: write-once, read-many.
- No delete or overwrite permissions granted to any human IAM identity.
- Pipeline job identity is the only write principal with a scoped, time-limited role.
- Corrections are handled by re-ingesting as a new partition with a new ingestion date, not by modifying existing files.
- Audit log records every write event including job ID, timestamp, and record count.

---

## Silver
- Standardized schema and timezone handling.
- Deduplication, null management, adjusted prices.
- Enrichment with cap tier metadata and validation flags.

### Silver Immutability Rules
- Silver outputs are snapshot-versioned by processing date.
- Existing snapshot files are never overwritten or deleted.
- A new snapshot is created each time the transformation job runs.
- Only the pipeline transformation job identity has write access to the silver zone.
- If a data quality issue is found, the source bronze data is corrected through re-ingestion, which then triggers a new silver snapshot.
- Silver zone IAM policy denies all PutObject and DeleteObject calls from human principals.

---

## Gold
- Feature sets and labels by trading horizon.
- Backtest-ready and training-ready datasets.
- Aggregated tables for dashboards and APIs.

### Gold Immutability Rules
- Gold datasets are snapshot-versioned by build date.
- Model training and backtests must reference a specific gold snapshot version, never a mutable latest pointer.
- Gold files are never edited after creation.
- Only the pipeline feature-build job identity has write access to the gold zone.
- Rollback means referencing an earlier gold snapshot, not modifying the current one.
- Gold zone IAM policy denies all PutObject and DeleteObject calls from human principals.

---

## Quality Gates
- Bronze to silver: schema and freshness checks.
- Silver to gold: completeness and feature readiness checks.
- Failed gates stop promotion to next layer.
- Gate failures are logged with a structured error record; they never result in partial or corrupted writes.

---

## Access Control Summary

| Layer | Pipeline Write | Human Write | Human Read | Delete Allowed |
| --- | --- | --- | --- | --- |
| Bronze | Allowed (scoped job identity) | Denied | Allowed | Never |
| Silver | Allowed (scoped job identity) | Denied | Allowed | Never |
| Gold | Allowed (scoped job identity) | Denied | Allowed | Never |

---

## Correction and Reprocessing Policy
- Errors found in bronze: re-ingest from source as a new partition.
- Errors found in silver: fix the transformation rule and rebuild silver snapshot.
- Errors found in gold: fix the feature rule and rebuild gold snapshot.
- Never patch, edit, or delete existing data in any layer.
- Every reprocessing event must be logged with reason, approver, job ID, and timestamp.

---

## Guardrails

### G1 - Ingestion Guardrails (Bronze Entry)
- Reject any payload where mandatory fields are missing (symbol, date, open, high, low, close, volume).
- Reject records with negative price or negative volume.
- Reject records where high < low.
- Reject records with a future date beyond today plus one business day tolerance.
- Reject entire batch if symbol not found in the approved universe list.
- Maximum allowed missing-field ratio per batch is 5%; breach triggers pipeline halt and alert.
- Duplicate detection on symbol + date combination; duplicates are rejected with a logged warning, never silently dropped.

### G2 - Promotion Guardrails (Bronze to Silver)
- Silver promotion is blocked if bronze freshness lag exceeds 2 business days.
- Silver promotion is blocked if any mandatory field has null rate above 2% for a symbol.
- Adjusted price must be present; if missing, promotion halts and alerts.
- Cap tier enrichment must succeed for every symbol; unknown cap tier blocks promotion.
- Schema must match the registered silver contract exactly; any mismatch halts promotion.
- All validation flags must be computed before write; partial silver records are rejected.

### G3 - Promotion Guardrails (Silver to Gold)
- Gold promotion is blocked if feature completeness is below 95% for any symbol in the universe.
- Gold promotion is blocked if target label generation produces nulls above 5% for swing horizon.
- Look-ahead bias check must pass before promotion; any forward-looking feature index triggers halt.
- Minimum symbol history check must pass; symbols with fewer than 60 trading days are excluded from gold.
- Feature value range checks must pass; extreme outlier ratios beyond configured z-score thresholds halt promotion.
- Gold snapshot is only written after all checks pass; there is no partial gold write.

### G4 - Runtime Guardrails (Training and Inference)
- Training job must reference a specific, named gold snapshot; no reference to a floating latest pointer.
- Training is blocked if gold snapshot age exceeds 7 days.
- Inference is blocked if the referenced model was trained on a gold snapshot more than 30 days old.
- Model output confidence below the configured threshold is flagged and excluded from the prediction store.
- Prediction records must carry: symbol, date, snapshot_version, model_version, horizon, cap_tier, confidence.

### G5 - Operational Guardrails (Access and Audit)
- Any failed IAM access attempt on bronze, silver, or gold zones triggers an immediate CloudWatch alert.
- All pipeline job runs are logged with: job ID, job type, input snapshot, output snapshot, row counts, pass/fail, duration.
- Reprocessing events require a structured change record with: reason, approver, impacted snapshot IDs, and timestamp.
- No emergency overrides or hotfixes are permitted directly on stored data files; all fixes go through the pipeline.
- Guardrail policy versions are tracked in the architecture governance doc and must be reviewed quarterly.

### G6 - Guardrail Breach Response
| Guardrail | Breach Action |
| --- | --- |
| Missing mandatory field | Reject batch, alert, log |
| Duplicate record | Reject record, warn, log |
| Schema mismatch | Halt promotion, alert |
| Freshness lag breach | Halt promotion, alert |
| Look-ahead bias detected | Halt gold build, alert |
| Human write attempt | Deny, alert, audit log |
| Model snapshot too old | Block inference, alert |
| Feature completeness below threshold | Halt gold build, alert |

---

## Design Outcomes
- Reproducibility: snapshot-based experiments with locked references.
- Traceability: raw-to-feature lineage with full audit trail.
- Operability: clear fault isolation by layer.
- Trust: no silent data mutations possible at any layer.
- Safety: every data transition is governed by explicit, versioned guardrails.
