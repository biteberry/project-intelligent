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

## Security and Governance
- Least-privilege IAM
- Secret management through managed store
- Data retention and lifecycle policies
- Auditability through centralized logs

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
