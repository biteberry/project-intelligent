# 06 Platform, MLOps, Observability, Security

## AWS Free-Tier Architecture
- S3 for bronze/silver/gold zones and model artifacts
- EventBridge for schedule
- Lambda for orchestration and inference
- API Gateway for prediction API
- DynamoDB for predictions, API cache, and pipeline audit logs (free forever)
- SQLite on EC2 for model metadata and experiment tracking
- S3 JSON snapshots for universe selections and schema registry
- CloudWatch for logs and metrics

## Backup and Failover Architecture
- Primary: AWS cloud (S3, DynamoDB, Lambda, EventBridge, API Gateway, CloudWatch).
- Secondary: local laptop with full daily sync from cloud.
- Daily sync covers: S3 bronze/silver/gold/models, DynamoDB prediction and audit exports, SQLite backup.
- Failover triggers: billing alarm, capacity alarms, account suspension.
- Full failover runs the entire pipeline locally using the same open-source stack.
- See ADR-004 for complete failover steps, sync design, and guardrails.

## Versioning and Traceability
- Code versioning in GitHub
- Data snapshot versioning by date partitions
- Model artifact versioning by model, version, and date
- Experiment metadata retained for reproducibility

## CI/CD Architecture
- Lint and unit tests
- Data contract checks
- Training and backtest smoke validation
- Controlled deployment promotion

## Observability Architecture
Data:
- Missing ratios, stale feeds, outliers

Model:
- Confidence distribution
- Feature and concept drift proxies
- Baseline performance decay tracking

System:
- API latency and error rates
- Job success and failure rates

## Database and Storage Capacity Alerts

### Universe Size Alert
- Warning at 150 active symbols: begin PostgreSQL migration planning.
- Critical at 200 active symbols: freeze universe expansion, migration must begin.
- Metric source: distinct symbol count from weekly universe selection run.
- Alert channel: CloudWatch alarm to SNS email.

### DynamoDB Read Capacity Alert
- Warning at 80% of free-tier RCU limit (25 RCU).
- Critical at 95% of free-tier RCU limit.
- Alert channel: CloudWatch alarm to SNS email.
- Action: investigate query pattern or trigger PostgreSQL migration review.

### DynamoDB Write Capacity Alert
- Warning at 80% of free-tier WCU limit (25 WCU).
- Critical at 95% of free-tier WCU limit.
- Alert channel: CloudWatch alarm to SNS email.

### S3 Storage Alert
- Warning at 80% of free-tier storage limit (5 GB).
- Alert channel: CloudWatch alarm to SNS email.
- Action: review data retention policy and prune eligible old snapshots through pipeline, never manually.

### AWS Billing Hard-Gate Alert
- Billing alarm configured at $0.10 (ten cents).
- This fires before any service limit is reached, giving maximum early warning.
- On alarm: investigate immediately, reduce usage, or activate local failover.
- This is the earliest possible signal that free-tier boundaries are at risk.

## Infrastructure-as-Code (IaC) Strategy

### Guiding Principle
Every AWS resource provisioned for this project must be defined in code —
either Terraform or CloudFormation — so the environment is reproducible,
reviewable, and teachable. Manual console clicks are not acceptable for
persistent resources.

### Tool Split

| Layer | Preferred Tool | Reason |
| --- | --- | --- |
| Core AWS infra (S3, DynamoDB, IAM, EC2, EventBridge, Lambda, CloudWatch, SNS, Secrets Manager, Glue) | **Terraform** | Modular, provider-agnostic, strong community modules, excellent for learning |
| GitHub Actions OIDC trust policy | **Terraform** | Clean IAM resource support |
| CloudFormation baseline stack | **CloudFormation** | AWS-native; good to understand for AWS certifications and service-linked roles |
| Lambda deployment packaging | **CloudFormation SAM** | Simplifies Lambda + EventBridge wiring |

### Terraform Module Structure

```
infra/terraform/
├── main.tf                  <- Root module: calls all child modules
├── variables.tf             <- Input variables (region, project prefix, account ID)
├── outputs.tf               <- Root outputs (bucket names, table ARNs, etc.)
├── backend.tf               <- S3 backend for remote state
├── providers.tf             <- AWS provider version pin
├── terraform.tfvars.example <- Safe example values (no secrets)
└── modules/
    ├── iam/                 <- IAM roles and policies
    ├── s3/                  <- All 5 S3 buckets + encryption + lifecycle
    ├── dynamodb/            <- predictions + audit tables
    ├── ec2/                 <- t2.micro instance + SSM profile
    ├── lambda_dispatcher/   <- Lambda SSM dispatcher function
    ├── eventbridge/         <- Daily + weekly schedule rules
    ├── cloudwatch/          <- Billing alarm + SNS + operational alarms
    ├── secrets_manager/     <- Secret placeholders (values set separately)
    └── glue_catalog/        <- Glue databases for bronze/silver/gold
```

### CloudFormation Template Structure

```
infra/cloudformation/
├── 01-iam.yaml              <- IAM roles (GitHub Actions OIDC + service roles)
├── 02-s3.yaml               <- S3 buckets baseline
├── 03-dynamodb.yaml         <- DynamoDB tables
├── 04-monitoring.yaml       <- CloudWatch + SNS
└── sam/
    └── dispatcher.yaml      <- SAM template for Lambda + EventBridge
```

### IaC Conventions

- All resource names use the prefix `project-intelligent-` for easy identification.
- Resource ARNs and names are exported as Terraform outputs / CloudFormation exports for cross-module reference.
- No hardcoded AWS account IDs — use `data.aws_caller_identity.current.account_id`.
- Terraform state stored in `project-intelligent-artifacts-<account_id>` S3 bucket under `terraform/state/`.
- `terraform plan` is run in CI (GitHub Actions) on every PR; `terraform apply` is manual with approval.
- CloudFormation templates are linted with `cfn-lint` in CI.
- `terraform.tfvars` and `.env` files are gitignored; only `.example` files are committed.

### Phase Rollout for IaC

| Phase | IaC Action |
| --- | --- |
| Phase 0 | Terraform modules written and `terraform plan` verified for all infra |
| Phase 0 | CloudFormation IAM + SAM dispatcher templates written |
| Phase 0 | `terraform apply` provisions the actual AWS environment |
| Phase 1+ | All new infra additions go through IaC first — no ad-hoc console creation |

## Security and Governance
- Least-privilege IAM (defined and reviewed in Terraform/CloudFormation — no console-only policies)
- Secret management through AWS Secrets Manager (referenced in IaC; values injected separately)
- Data retention and lifecycle policies (defined in Terraform S3 module)
- Auditability through centralized logs
- IaC drift detection: `terraform plan` in CI will catch any manual console changes

### Secret Naming Convention (NFR-05)

All secrets stored in AWS Secrets Manager follow this convention:

```
/project-intelligent/<service>/<key-type>
```

| Secret Name | Service | Purpose |
|-------------|---------|---------|
| `/project-intelligent/finnhub/api-key` | Finnhub | Stock quotes & fundamentals |
| `/project-intelligent/alphavantage/api-key` | AlphaVantage | Additional stock data |
| `/project-intelligent/postgres/password` | PostgreSQL | Local DB password (future) |

**Rules:**
- Secret names are lowercase with hyphens — no underscores
- Values are never stored in any repository file
- Placeholder value `REPLACE_ME` is used when creating secret slots before keys are available
- Access restricted to EC2 IAM role and Lambda role only — no wildcard resource policies
- Python helper `src/utils/secrets.py` provides `get_secret()` with in-memory cache for runtime retrieval
- detect-secrets pre-commit hook blocks any accidental key exposure (`v1.5.0`, baseline: `.secrets.baseline`)

---

## Guardrails

### G1 - CI/CD Gate
- No deployment proceeds unless all pipeline stages pass: lint, unit tests, schema checks, training smoke test, and backtest smoke test.
- A single failing stage blocks the entire deployment; partial deployments are not permitted.

### G2 - Secret Exposure
- Hard-coded secrets, credentials, or API keys in any repository file automatically block the CI pipeline.
- Secrets must be stored in the managed secret store only and referenced by name, not by value.

### G3 - IAM Least Privilege
- Every service identity is granted only the permissions required for its specific job.
- Overly broad IAM policies (e.g., wildcard resource access) are rejected during architecture review.
- IAM policies are reviewed quarterly and tightened when permissions are found to be unused.

### G4 - Observability Coverage
- A pipeline component is not production-ready unless it emits at minimum: job start, job success or failure, duration, and record count metrics.
- Components without observability instrumentation are blocked from production deployment.

### G5 - Alert Coverage
- Every critical job must have a failure alarm configured before going to production.
- Unalarmed critical jobs are not accepted in architecture sign-off.
- Alert thresholds are documented in the governance policy and reviewed per phase.

### G6 - Retention Policy
- Every storage resource must have a defined data retention and lifecycle policy.
- Data stored without a lifecycle policy is a compliance violation and must be remediated.

### G7 - Dependency Pinning
- All library, package, and infrastructure dependencies must be pinned to specific versions.
- Unpinned or floating dependencies block CI promotion.
- Dependency versions are reviewed and updated on a scheduled cadence, not ad hoc.
