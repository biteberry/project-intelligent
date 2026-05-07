# create_github_milestones.ps1
# Creates all 8 PROJECT INTELLIGENT milestones on GitHub using gh CLI.
# Run from any directory after: gh auth login
# Usage: .\scripts\setup\create_github_milestones.ps1

$repo = "biteberry/project-intelligent"
$gh   = "C:\Program Files\GitHub CLI\gh.exe"

Write-Host "Creating milestones for $repo ..." -ForegroundColor Cyan

& $gh api repos/$repo/milestones --method POST -f title="M0: Phase 0 - Architecture and Sign-Off"    -f due_on="2026-05-15T00:00:00Z" -f description="Close architecture phase, PRD sign-off, Phase 0 gate, push all docs to GitHub"
& $gh api repos/$repo/milestones --method POST -f title="M1: Phase 1.1 - Environment Provisioning"  -f due_on="2026-05-31T00:00:00Z" -f description="AWS infra (S3, DynamoDB, EC2, EventBridge, Lambda, CloudWatch, Secrets Manager), PostgreSQL schema, GitHub Actions CI, Finnhub key"
& $gh api repos/$repo/milestones --method POST -f title="M2: Phase 1.2 - Data Ingestion Layer"      -f due_on="2026-06-30T00:00:00Z" -f description="J01-J03: OHLCV, NSE delivery %, fundamentals, earnings calendar, corporate actions, India macro, circuit bands. Bronze and Silver layers."
& $gh api repos/$repo/milestones --method POST -f title="M3: Phase 1.3 - Feature Engineering Layer" -f due_on="2026-07-31T00:00:00Z" -f description="J04-J05: All 10 feature groups in Gold layer (Iceberg). Market regime detection. Look-ahead bias audit."
& $gh api repos/$repo/milestones --method POST -f title="M4: Phase 1.4 - ML Training Pipeline"      -f due_on="2026-08-31T00:00:00Z" -f description="J06: XGBoost/LightGBM trainer, walk-forward validation, model promotion gate (>=2% accuracy improvement), MLflow tracking, S3 model artifacts."
& $gh api repos/$repo/milestones --method POST -f title="M5: Phase 1.5 - Inference and Signals"     -f due_on="2026-09-30T00:00:00Z" -f description="J07-J08: Batch predictions, all 5 serving gates (earnings blackout, circuit, macro, confidence, staleness), trade signals (entry/stop/target/size), Finnhub sentiment."
& $gh api repos/$repo/milestones --method POST -f title="M6: Phase 1.6 - Monitoring and Operations" -f due_on="2026-10-31T00:00:00Z" -f description="J09: CloudWatch alarms, SNS email alerts, DynamoDB audit trail, local PostgreSQL sync, failover runbook."
& $gh api repos/$repo/milestones --method POST -f title="M7: Phase 1.7 - Acceptance Testing and Go-Live" -f due_on="2026-11-30T00:00:00Z" -f description="End-to-end validation. All 10 Definition of Done checklist items from PRD v1.0 must pass before go-live."

Write-Host ""
Write-Host "Done. 8 milestones created on $repo." -ForegroundColor Green
Write-Host "Verify at: https://github.com/$repo/milestones" -ForegroundColor Cyan
