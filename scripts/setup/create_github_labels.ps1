# create_github_labels.ps1
# Creates all 27 PROJECT INTELLIGENT labels on GitHub using gh CLI.
# Run from any directory after: gh auth login
# Usage: .\scripts\setup\create_github_labels.ps1

$repo = "biteberry/project-intelligent"
$gh   = "C:\Program Files\GitHub CLI\gh.exe"

Write-Host "Creating labels for $repo ..." -ForegroundColor Cyan

# ── TYPE LABELS ──────────────────────────────────────────────────────────────
& $gh label create "type:feature"  --color "0052CC" --description "Feature (epic) — groups related stories"           --repo $repo --force
& $gh label create "type:story"    --color "0075CA" --description "User story — vertical slice of a feature"          --repo $repo --force
& $gh label create "type:task"     --color "BFD4F2" --description "Concrete implementation task"                      --repo $repo --force
& $gh label create "type:bug"      --color "D73A4A" --description "Defect found during development or testing"        --repo $repo --force
& $gh label create "type:spike"    --color "E4E669" --description "Research or investigation — no deliverable code"   --repo $repo --force
& $gh label create "type:doc"      --color "EDEDED" --description "Documentation only"                                --repo $repo --force
& $gh label create "type:infra"    --color "006B75" --description "AWS, environment, CI/CD infrastructure"            --repo $repo --force

# ── PHASE LABELS ─────────────────────────────────────────────────────────────
& $gh label create "phase:0-setup"   --color "F9D0C4" --description "Phase 0 - Architecture, PRD, environment provisioning" --repo $repo --force
& $gh label create "phase:1-core"    --color "FBCA04" --description "Phase 1 - Core pipeline implementation"                --repo $repo --force
& $gh label create "phase:2-enhance" --color "0E8A16" --description "Phase 2 - Enhancements (FII/DII, BSE, etc.)"           --repo $repo --force

# ── MEDALLION LAYER LABELS ───────────────────────────────────────────────────
& $gh label create "layer:landing" --color "F4A261" --description "Landing zone - raw files before any processing"         --repo $repo --force
& $gh label create "layer:bronze"  --color "CD7F32" --description "Bronze - raw Parquet, immutable, no transformation"     --repo $repo --force
& $gh label create "layer:silver"  --color "C0C0C0" --description "Silver - cleaned, joined, validated Iceberg tables"     --repo $repo --force
& $gh label create "layer:gold"    --color "FFD700" --description "Gold - ML-ready features, Iceberg, all 10 feature groups" --repo $repo --force

# ── COMPONENT LABELS ─────────────────────────────────────────────────────────
& $gh label create "comp:ingestion"   --color "B60205" --description "J01-J03: Data ingestion jobs"                   --repo $repo --force
& $gh label create "comp:feature-eng" --color "D93F0B" --description "J04: Feature engineering — Gold layer"          --repo $repo --force
& $gh label create "comp:ml-pipeline" --color "E99695" --description "J06: Model training and promotion gate"         --repo $repo --force
& $gh label create "comp:inference"   --color "F9D0C4" --description "J07-J08: Prediction generation and signals"     --repo $repo --force
& $gh label create "comp:universe"    --color "5319E7" --description "J01: Universe selection and opportunity scanner" --repo $repo --force
& $gh label create "comp:monitoring"  --color "1D76DB" --description "J09: CloudWatch, SNS alerts, audit trail"       --repo $repo --force
& $gh label create "comp:infra"       --color "006B75" --description "AWS setup, GitHub Actions, local environment"   --repo $repo --force
& $gh label create "comp:data-store"  --color "0052CC" --description "DynamoDB, S3, PostgreSQL"                       --repo $repo --force
& $gh label create "comp:docs"        --color "EDEDED" --description "Architecture docs, PRD, ADRs"                   --repo $repo --force

# ── PRIORITY LABELS ──────────────────────────────────────────────────────────
& $gh label create "priority:critical" --color "B60205" --description "Blocks all other work"                  --repo $repo --force
& $gh label create "priority:high"     --color "D93F0B" --description "Must complete this milestone"           --repo $repo --force
& $gh label create "priority:medium"   --color "FBCA04" --description "Should complete this milestone"         --repo $repo --force
& $gh label create "priority:low"      --color "C2E0C6" --description "Nice to have — complete if time allows" --repo $repo --force

# ── STATE LABELS ─────────────────────────────────────────────────────────────
& $gh label create "blocked"       --color "B60205" --description "Cannot proceed - waiting on dependency or decision" --repo $repo --force
& $gh label create "needs-review"  --color "FBCA04" --description "Needs platform owner review or decision"           --repo $repo --force
& $gh label create "deferred"      --color "EDEDED" --description "Explicitly moved to a later phase"                 --repo $repo --force
& $gh label create "wontfix"       --color "EDEDED" --description "Decided not to implement"                           --repo $repo --force

Write-Host ""
Write-Host "Done. 31 labels created on $repo." -ForegroundColor Green
Write-Host "Verify at: https://github.com/$repo/labels" -ForegroundColor Cyan
