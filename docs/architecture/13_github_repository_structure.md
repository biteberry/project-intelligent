# 13 GitHub Repository Structure Architecture

## Purpose
Define the canonical repository layout, directory responsibilities, naming conventions, branch strategy, and file governance rules. This is the reference before Phase 0 implementation begins.

---

## Repository Name
`project-intelligent`

Hosted at: `github.com/{your-username}/project-intelligent`

---

## Top-Level Directory Layout

```
project-intelligent/
├── docs/
│   ├── architecture/          <- All architecture decision documents (this project)
│   ├── analysis/              <- Analysis framework documents
│   └── adr/                   <- Architectural Decision Records
├── configs/
│   ├── trading_horizons.yaml  <- Horizon enable/disable flags
│   ├── label_rules.yaml       <- Label computation configuration
│   ├── universe.example.csv   <- Example universe (not the live universe)
│   └── pipeline.yaml          <- Pipeline schedule and job configuration
├── schemas/
│   ├── bronze_ohlcv.schema.json
│   ├── silver_ohlcv.schema.json
│   └── gold_swing_features.schema.json
├── src/
│   ├── ingestion/             <- Bronze ingestion jobs
│   ├── transformation/        <- Bronze→Silver, Silver→Gold jobs
│   ├── features/              <- Feature engineering logic
│   ├── labels/                <- Label engineering logic
│   ├── training/              <- Model training and evaluation
│   ├── inference/             <- Batch inference
│   ├── universe/              <- Universe selection logic
│   ├── serving/               <- API serving layer
│   ├── sync/                  <- Local backup sync jobs
│   └── utils/                 <- Shared utilities (calendar, schema validators, etc.)
├── tests/
│   ├── unit/                  <- Unit tests per module
│   ├── integration/           <- Integration tests (pipeline stage contracts)
│   └── fixtures/              <- Test data fixtures (small synthetic datasets)
├── notebooks/
│   ├── exploration/           <- Ad-hoc research notebooks (never imported by src/)
│   └── reports/               <- Results and backtest report notebooks
├── infra/
│   ├── terraform/             <- Terraform root module + child modules
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── backend.tf
│   │   ├── providers.tf
│   │   ├── terraform.tfvars.example
│   │   └── modules/
│   │       ├── iam/
│   │       ├── s3/
│   │       ├── dynamodb/
│   │       ├── ec2/
│   │       ├── lambda_dispatcher/
│   │       ├── eventbridge/
│   │       ├── cloudwatch/
│   │       ├── secrets_manager/
│   │       └── glue_catalog/
│   ├── cloudformation/        <- CloudFormation YAML templates
│   │   ├── 01-iam.yaml
│   │   ├── 02-s3.yaml
│   │   ├── 03-dynamodb.yaml
│   │   ├── 04-monitoring.yaml
│   │   └── sam/
│   │       └── dispatcher.yaml
│   └── local/                 <- Local dev environment (Docker Compose)
│       └── docker-compose.yml
├── scripts/
│   ├── setup/                 <- One-time setup scripts (backfill, schema init)
│   └── ops/                   <- Operational scripts (manual sync, health checks)
├── STOCK_MARKET_PREDICTION_ARCHITECTURE.md   <- Root architecture index
├── README.md                  <- Project readme for GitHub
├── .gitignore
├── requirements.txt           <- Python dependencies (pinned versions)
└── pyproject.toml             <- Project metadata and tool configuration
```

---

## Directory Responsibilities

### `docs/`
- Architecture documents only. No code. No notebooks.
- Subdirectory structure mirrors the current document organization.
- Every document must follow the established naming convention: `NN_description.md`.
- ADRs follow the convention: `ADR-NNN-short-title.md`.

### `configs/`
- YAML and CSV configuration files that control pipeline behaviour.
- No secrets or credentials. Secrets are stored in AWS Secrets Manager only.
- Every config file must have a corresponding schema or comment block defining all valid fields.
- `pipeline.yaml` is the primary runtime configuration file (schedules, batch sizes, alert thresholds).

### `schemas/`
- JSON Schema files defining the contract for each data layer.
- Schema files are read by pipeline jobs at validation steps.
- Changes to schema files require a version increment and a note in the relevant architecture doc.

### `src/`
- All production pipeline code. Organized by pipeline stage.
- No Jupyter notebooks in `src/`.
- Each subdirectory is a Python package (has an `__init__.py`).
- No cross-stage imports except through `utils/`. Example: `ingestion/` must not import from `training/`.

### `src/ingestion/`
- Bronze ingestion jobs: `ingest_ohlcv.py`, `ingest_macro.py`, `backfill.py`.
- Each file is a runnable entry-point with a `main()` function.
- No business logic in `main()`; `main()` calls well-named helper functions.

### `src/transformation/`
- Bronze-to-Silver promotion: `bronze_to_silver.py`.
- Silver-to-Gold promotion: `silver_to_gold.py`.
- Each file is a runnable entry-point.

### `src/features/`
- Feature computation modules, one file per feature group.
- `price_returns.py`, `rolling_stats.py`, `technical_indicators.py`, `volume_features.py`, `volatility_features.py`, `regime_features.py`, `calendar_features.py`.
- A `feature_builder.py` orchestrates all groups in the correct order.

### `src/labels/`
- Label computation: `label_builder.py`.
- Edge case handlers: `label_validation.py`.
- Trading calendar: `trading_calendar.py`.

### `src/training/`
- Model training entry-point: `train.py`.
- Evaluation: `evaluate.py`.
- Walk-forward logic: `walk_forward.py`.
- Model registry write: `register_model.py`.

### `src/inference/`
- Batch inference entry-point: `batch_inference.py`.
- Prediction writer: `prediction_writer.py` (writes to DynamoDB).

### `src/universe/`
- Universe selection: `universe_selector.py`.
- Composite scoring: `composite_scorer.py`.
- Cap-tier allocation: `cap_tier_allocator.py`.

### `src/serving/`
- API application: `app.py` (FastAPI or Flask).
- Prediction reader: `prediction_reader.py` (reads from DynamoDB or local PostgreSQL in failover mode).

### `src/sync/`
- Daily local sync: `local_sync.py`.
- DynamoDB export: `dynamodb_export.py`.
- Integrity check: `sync_integrity_check.py`.

### `src/utils/`
- Shared utilities used across multiple pipeline stages.
- `schema_validator.py`, `audit_writer.py`, `cap_tier_utils.py`, `s3_utils.py`, `dynamodb_utils.py`.
- No business logic; only infrastructure helpers.

### `tests/`
- Unit tests live in `tests/unit/` and mirror the `src/` directory structure.
- Integration tests live in `tests/integration/` and test stage-to-stage contracts.
- Test fixtures are small synthetic datasets stored in `tests/fixtures/`. Never use production data in tests.
- Test file naming: `test_{module_name}.py`.

### `notebooks/`
- Exploration notebooks in `notebooks/exploration/` are disposable research tools.
- Notebooks must never be imported by `src/` code. Copy validated logic into `src/` modules.
- Report notebooks in `notebooks/reports/` document backtest results and are committed.
- Exploration notebooks are committed only if they contain useful reference analysis; otherwise they are gitignored.

### `infra/`
- All infrastructure-as-code. No manual console provisioning for persistent resources.
- `infra/terraform/` is the primary provisioning path. Run `terraform plan` to preview, `terraform apply` to provision.
- `infra/cloudformation/` covers AWS-native templates (IAM OIDC, SAM Lambda). Deployed via `aws cloudformation deploy`.
- `infra/local/` holds Docker Compose for local PostgreSQL and any local dev services.
- `terraform.tfvars` is gitignored. Only `terraform.tfvars.example` is committed.
- Terraform state is stored remotely in the artifacts S3 bucket under `terraform/state/`.
- `terraform plan` is run automatically in CI (GitHub Actions) on every PR touching `infra/terraform/`.

### `scripts/`
- One-time and operational scripts that are not part of the regular pipeline.
- `setup/backfill.sh`: triggers the historical backfill job.
- `ops/manual_sync.sh`: triggers a manual local sync outside the daily schedule.
- `ops/health_check.sh`: verifies pipeline audit records for the last N days.

---

## File Naming Conventions

| Type | Convention | Example |
| --- | --- | --- |
| Python module | snake_case.py | `bronze_to_silver.py` |
| Python test | test_snake_case.py | `test_bronze_to_silver.py` |
| Config file | snake_case.yaml or .json | `pipeline.yaml` |
| Architecture doc | NN_description.md | `08_data_ingestion_architecture.md` |
| ADR | ADR-NNN-short-title.md | `ADR-001-kafka-decision.md` |
| Schema | layer_entity.schema.json | `silver_ohlcv.schema.json` |
| Notebook | YYYYMMDD_short_description.ipynb | `20260507_rsi_exploration.ipynb` |

---

## Branch Strategy

### Permanent Branches
| Branch | Purpose |
| --- | --- |
| `main` | Production-ready, signed-off code only. Protected branch. |
| `develop` | Integration branch for completed features awaiting release. |

### Temporary Branches
| Branch Prefix | Purpose | Example |
| --- | --- | --- |
| `feature/` | New pipeline components or capabilities | `feature/bronze-ingestion` |
| `fix/` | Bug fixes in existing pipeline code | `fix/duplicate-dedup-logic` |
| `arch/` | Architecture document updates | `arch/add-cost-model-doc` |
| `chore/` | Non-functional changes (config, deps, tooling) | `chore/pin-pyiceberg-version` |

### Branch Lifecycle
1. Create branch from `develop` (not from `main`).
2. All work happens on the feature branch.
3. Open a pull request to `develop` when work is complete.
4. Pull request requires at least one passing CI check (lint + tests).
5. Merge to `develop` after review.
6. At phase gate sign-off, `develop` is merged to `main` via a release pull request.

### Main Branch Protection Rules
- Direct pushes to `main` are not allowed.
- Merges to `main` require a pull request.
- Pull requests to `main` require all CI checks to pass.
- Commit history on `main` is linear (squash or rebase merge only).

---

## What Is Never Committed to the Repository

| Item | Reason | Alternative |
| --- | --- | --- |
| AWS credentials or access keys | Security | AWS Secrets Manager or environment variables |
| API keys (FRED, etc.) | Security | AWS Secrets Manager or local .env file (gitignored) |
| Production data files | Size and sensitivity | S3 |
| Model artifact binaries | Size | S3 |
| The live universe CSV | Changes frequently | S3 JSON snapshot; only example file in repo |
| Local .env files | Credentials | Gitignored; documented in README |
| Jupyter notebook outputs | Size and reproducibility | Clear outputs before committing |

---

## .gitignore Minimum Requirements

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
venv/

# Environment
.env
.env.*
*.local

# Jupyter
.ipynb_checkpoints/

# Data and models (never in repo)
data/
models/
*.parquet
*.db
*.sqlite

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/settings.json
.idea/
```

---

## README.md Minimum Content

The root `README.md` must include:
1. Project purpose (one paragraph).
2. Architecture overview link to `STOCK_MARKET_PREDICTION_ARCHITECTURE.md`.
3. Phase status indicator (current phase and sign-off state).
4. Local development setup steps (clone, install requirements, configure AWS CLI).
5. How to run the pipeline locally.
6. Branch strategy summary.

---

## Guardrails

### G1 - No Production Data in Repository
- No Parquet files, SQLite files, or CSV files containing real market data are committed.
- Only synthetic fixtures in `tests/fixtures/` are allowed.
- A CI check scans for large binary files and blocks commits over 1 MB.

### G2 - No Secrets in Repository
- A pre-commit hook scans for AWS key patterns, API key patterns, and password strings.
- Any commit containing a detected secret is blocked before it reaches GitHub.
- If a secret is accidentally committed, it must be rotated immediately, then removed from git history.

### G3 - Notebooks Cannot Be Imported
- A CI check verifies that no file in `src/` imports from `notebooks/`.
- Validated logic in notebooks must be rewritten as a proper module in `src/` before use in the pipeline.

### G4 - Test Coverage Gate
- Pull requests to `develop` must not reduce overall test coverage below 70%.
- Pull requests to `main` must not reduce overall test coverage below 80%.

### G5 - Architecture Doc Changes Require arch/ Branch
- Changes to any file in `docs/` must use an `arch/` prefixed branch.
- This makes architecture changes visible and distinct from code changes in the pull request history.

### G6 - requirements.txt Uses Pinned Versions
- All Python dependencies must use exact pinned versions in `requirements.txt` (e.g., `pyiceberg==0.7.1`).
- Unpinned or range-pinned dependencies (e.g., `pyiceberg>=0.7`) are rejected at CI.
- This ensures reproducible environments across cloud and local laptop.
