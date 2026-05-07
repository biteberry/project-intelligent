# 07 Phased Rollout

## Phase 0 - Foundation
- Finalize data contracts and labels.
- Finalize cap-tier and horizon dictionaries.
- Finalize pre-landing universe rules.
- Write Terraform modules for all AWS resources (IAM, S3, DynamoDB, EC2, Lambda, EventBridge, CloudWatch, Secrets Manager, Glue Catalog).
- Write CloudFormation templates for IAM OIDC role and SAM Lambda dispatcher.
- Run `terraform plan` to validate all modules before any `terraform apply`.
- Provision the full environment via `terraform apply` — no manual console clicks for persistent resources.

## Phase 1 - Swing Baseline
- Build swing feature and label architecture.
- Define baseline model family and evaluation contracts.
- Finalize backtest assumptions and acceptance thresholds.

## Phase 2 - Product Skeleton
- Define batch inference interface.
- Define API contracts and prediction response schema.
- Define dashboard KPI contracts.

## Phase 3 - Reliability and Monitoring
- Define drift and alert policies.
- Define retraining triggers and governance approvals.
- Define runbooks for incidents and model rollback.

## Milestone Exit Criteria
- Each phase exits only when documentation sign-off is complete.
- No implementation starts without architecture approval for current phase.

---

## Guardrails

### G1 - Phase Entry
- No phase begins before the previous phase exit criteria are fully documented and signed off.
- Partial or informal approval does not satisfy the entry requirement.

### G2 - Scope Creep
- Any feature or component not listed in the current phase architecture must go through a formal change request before inclusion.
- Undocumented additions are removed until the change request is reviewed and approved.

### G3 - Architecture Drift
- If implementation deviates from the architecture, the deviation must be reviewed immediately.
- Either the architecture is updated to reflect a justified design change, or the implementation is corrected.
- Unresolved drift blocks phase exit.

### G4 - Rollback Plan
- Every phase must have a documented rollback plan before implementation starts.
- Phases without a rollback plan do not receive implementation approval.

### G5 - No Partial Sign-Off
- Phase exit requires complete documentation review across all areas: data, model, validation, operations, and governance.
- Sign-off on only a subset of areas is not accepted as a phase exit.

### G6 - Phase Gate Audit
- Every phase gate decision (enter, exit, block, escalate) is recorded with date, decision, and approver.
- Unrecorded phase transitions are treated as invalid.
