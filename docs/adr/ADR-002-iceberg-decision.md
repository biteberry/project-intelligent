# ADR-002: Apache Iceberg Table Format Adoption

## Status
Accepted - Silver and Gold layers; Bronze remains plain parquet

## Date
2026-05-07

## Context
The medallion architecture mandates immutability, snapshot-based reproducibility, and strict data quality at every layer. The initial design used date-partitioned parquet files on S3 and enforced these properties through IAM policies, pipeline conventions, and naming standards.

Apache Iceberg was evaluated as a table format to replace or augment plain parquet on S3. Iceberg is not a streaming tool or compute engine; it is an open table format that adds database-grade properties to files stored on object storage.

This decision is directly relevant to the current swing trading phase because:
- Model training requires reproducible, snapshot-referenced Gold datasets.
- Backtests require point-in-time queries to avoid look-ahead bias.
- Feature schema will evolve as new indicators are added.
- Immutability guarantees must be enforced at the storage layer, not just by convention.

## Decision Drivers
- Budget: near-zero, AWS free tier only.
- Immutability: all medallion layers must be immutable by design, not by convention.
- Reproducibility: model training and backtest jobs must reference exact data snapshots.
- Look-ahead safety: point-in-time data access must be reliable for walk-forward validation.
- Schema evolution: Gold feature tables will grow as new analysis types are added.
- Operational simplicity: no heavy compute cluster; must run on t2.micro or Lambda.

## Options Evaluated

### Option 1 - Plain Parquet on S3 with IAM and Naming Convention (Current Baseline)
- No additional library.
- Immutability enforced through IAM object lock and naming conventions.
- Reproducibility achieved through date-partitioned path naming only.
- No native time travel; point-in-time queries require careful path management.
- Schema evolution requires manual versioning and migration scripts.
- Verdict: workable but fragile; immutability is policy-based not storage-based.

### Option 2 - Apache Iceberg with Apache Spark
- Full Iceberg feature set.
- Requires a Spark cluster to write and maintain tables.
- Spark cannot run on t2.micro; minimum useful cluster is 4 GB RAM.
- AWS Glue or EMR both exceed the free-tier budget.
- Verdict: rejected due to compute cost.

### Option 3 - Apache Iceberg with PyIceberg and DuckDB (Selected)
- PyIceberg is a pure Python Iceberg client; no JVM, no Spark required.
- DuckDB is an in-process analytical engine that reads Iceberg tables natively.
- Both run comfortably on t2.micro (1 GB RAM) for the 30-symbol swing universe.
- AWS Glue Catalog provides the Iceberg catalog service within the free-tier limit.
- S3 stores the data files and Iceberg metadata within the free-tier storage limit.
- Full Iceberg feature set available: snapshots, time travel, schema evolution, ACID writes.
- Verdict: selected.

### Option 4 - Delta Lake with delta-rs
- Alternative open table format with similar capabilities to Iceberg.
- delta-rs is a Rust-based Python client; no Spark required.
- Strong ecosystem but Iceberg has broader AWS-native integration (Glue, Athena).
- Iceberg preferred for better alignment with AWS free-tier tooling.
- Verdict: viable alternative but not selected; prefer Iceberg for AWS alignment.

## Decision
Apache Iceberg is adopted for Silver and Gold medallion layers using PyIceberg + DuckDB + S3 + AWS Glue Catalog.

Bronze layer remains plain parquet because:
- Bronze is append-only raw source data with no schema evolution requirement.
- Iceberg overhead is not justified for immutable raw landing files.
- Parquet with IAM object lock is sufficient for Bronze immutability.

## Architecture Impact

### Silver Layer
- Silver OHLCV table becomes an Iceberg table on S3.
- Each daily transformation job appends a new Iceberg snapshot.
- Schema evolution (adding new enrichment columns) handled natively without migration scripts.
- Time travel available for debugging data quality issues across any past snapshot.

### Gold Layer
- Gold swing feature table becomes an Iceberg table on S3.
- Model training jobs reference a specific Iceberg snapshot ID, not a date-path convention.
- Snapshot ID is stored in the model artifact metadata for full reproducibility.
- Backtest jobs use Iceberg time travel to read the exact data state as of any historical date.
- Rollback means repointing a training job to a prior snapshot ID, not copying files.

### Catalog
- AWS Glue Data Catalog acts as the Iceberg catalog.
- Tables registered as: project_intelligent.silver_ohlcv and project_intelligent.gold_swing.
- Glue free tier: 1 million objects per month, sufficient for 30-symbol swing universe.

### Query Engine
- DuckDB used for all analytical queries, schema checks, and feature validation.
- DuckDB reads Iceberg tables directly from S3 with the Glue catalog.
- No persistent cluster required; DuckDB runs in-process within Lambda or EC2.

## Updated Medallion Layer Design

| Layer | Format | Engine | Catalog | Immutability Mechanism |
| --- | --- | --- | --- | --- |
| Bronze | Plain Parquet | Pandas / PyArrow | S3 path convention | IAM object lock |
| Silver | Apache Iceberg | PyIceberg + DuckDB | AWS Glue | Iceberg snapshot ACID + IAM |
| Gold | Apache Iceberg | PyIceberg + DuckDB | AWS Glue | Iceberg snapshot ACID + IAM |

## Consequences

### Positive
- Immutability is now enforced at the storage format level for Silver and Gold, not only by IAM policy.
- Time travel enables reliable point-in-time queries for backtesting and debugging.
- Schema evolution removes the need for manual migration scripts as features grow.
- Model training and backtest jobs reference exact snapshot IDs for full reproducibility.
- Rollback is native: repoint to a prior snapshot ID without file operations.
- No additional infrastructure cost on free tier with the PyIceberg + DuckDB + Glue stack.

### Negative
- PyIceberg adds a new dependency to the platform.
- Glue Catalog requires correct IAM configuration for table registration.
- DuckDB Iceberg integration requires the iceberg extension to be loaded at query time.
- Team must learn Iceberg snapshot and catalog concepts before implementation.
- Bronze and Silver now use different storage formats, requiring clear documentation.

## Guardrails Added by This Decision
- All Silver and Gold writes must go through PyIceberg; direct parquet writes to these layers are rejected.
- Training and backtest jobs must record the Iceberg snapshot ID used, not just a date path.
- Iceberg table schema changes must be backward compatible; breaking changes require an architecture review.
- Glue Catalog table definitions are version-controlled in the infra config; manual console edits are not permitted.

## Revisit Trigger
- Revisit if Glue Catalog free-tier limits are approached.
- Revisit if PyIceberg Iceberg version support falls behind the project's S3 and Glue versions.
- Revisit at intraday phase: evaluate whether Iceberg streaming ingestion (Flink + Iceberg) is warranted.

## References
- Architecture constraint: docs/architecture/01_scope_and_constraints.md
- Medallion data architecture: docs/architecture/03_data_architecture_medallion.md
- Related ADR: docs/adr/ADR-001-kafka-decision.md
