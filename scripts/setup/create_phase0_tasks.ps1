#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Creates task issues for all Phase-0 stories (#44-#56) under epic #2.
    Also updates stories #44-#48 with proper acceptance criteria.
.NOTES
    Repo   : biteberry/project-intelligent
    Epic   : #2  [FEATURE-002] Environment Provisioning
    Stories: #44-#50, #52-#56  (# 51 is closed/duplicate)
#>

$ErrorActionPreference = "Stop"
$GH = "C:\Program Files\GitHub CLI\gh.exe"
$REPO = "biteberry/project-intelligent"
$MILESTONE = "M1: Phase 1.1 - Environment Provisioning"
$ASSIGNEE = "sentomani"

function gh_issue_create {
    param(
        [string]$title,
        [string]$body,
        [string]$labels,
        [string]$milestone = $MILESTONE,
        [string]$assignee = $ASSIGNEE
    )
    $num = & $GH issue create `
        --repo $REPO `
        --title $title `
        --body $body `
        --label $labels `
        --milestone $milestone `
        --assignee $assignee `
        2>&1
    Write-Host "  Created: $num"
    return $num
}

function gh_issue_edit {
    param(
        [int]$number,
        [string]$body,
        [string]$addLabels = ""
    )
    $args_list = @("issue", "edit", $number, "--repo", $REPO, "--body", $body)
    if ($addLabels -ne "") {
        $args_list += @("--add-label", $addLabels)
    }
    & $GH @args_list 2>&1 | Out-Null
    Write-Host "  Updated issue #$number"
}

# ---------------------------------------------------------------------------
# STEP 1 — Update stories #44-#48 with proper acceptance criteria + labels
# ---------------------------------------------------------------------------

Write-Host "`n=== Updating story #44: AWS IAM roles ===" -ForegroundColor Cyan
gh_issue_edit -number 44 -addLabels "comp:infra,phase:0-setup,priority:critical" -body @"
## Summary

Create all IAM roles and least-privilege policies required for the project:
EC2 instance profile, Lambda execution role, and GitHub Actions OIDC role.
No wildcard `*` permissions anywhere.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/12_aws_cost_model.md
- docs/adr/ADR-004-backup-and-failover.md

## Acceptance Criteria

- [ ] IAM role created for EC2 instance profile (S3, DynamoDB, SSM, Secrets Manager, Glue read/write)
- [ ] IAM role created for Lambda execution (SSM SendCommand, CloudWatch Logs write)
- [ ] IAM role created for GitHub Actions OIDC (deployment-scoped only)
- [ ] All policies follow least-privilege — no wildcard `*` permissions
- [ ] Roles successfully assumed from EC2 and Lambda in smoke tests
- [ ] IAM policy JSON documents committed to `infra/iam/` directory

## Child Tasks

_To be linked once task issues are created._
"@

Write-Host "`n=== Updating story #45: AWS S3 buckets ===" -ForegroundColor Cyan
gh_issue_edit -number 45 -addLabels "comp:infra,phase:0-setup,priority:critical" -body @"
## Summary

Create and configure all 5 S3 buckets for the medallion data architecture:
landing, bronze, silver, gold, and artifacts.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/03_data_architecture_medallion.md
- docs/architecture/08_data_ingestion_architecture.md

## Acceptance Criteria

- [ ] 5 S3 buckets created: `landing`, `bronze`, `silver`, `gold`, `artifacts`
- [ ] All buckets block public access
- [ ] Server-side encryption (SSE-S3) enabled on all buckets
- [ ] Bucket versioning enabled on bronze, silver, gold, artifacts
- [ ] Lifecycle policy on landing zone: auto-expire raw files after 30 days
- [ ] EC2 IAM role has read/write access to all 5 buckets

## Child Tasks

_To be linked once task issues are created._
"@

Write-Host "`n=== Updating story #46: AWS DynamoDB tables ===" -ForegroundColor Cyan
gh_issue_edit -number 46 -addLabels "comp:data-store,phase:0-setup,priority:high" -body @"
## Summary

Create DynamoDB tables for storing ML predictions output and job audit trail.
Use on-demand billing to stay within AWS Free Tier.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/04_model_strategy_and_serving.md
- docs/adr/ADR-003-database-decision.md

## Acceptance Criteria

- [ ] `predictions` table created (PK: `symbol#date`, SK: `horizon#model_version`)
- [ ] `audit` table created (PK: `job_date`, SK: `job_id`)
- [ ] Both tables use on-demand (PAY_PER_REQUEST) billing
- [ ] TTL attribute configured on `predictions` table (90-day retention)
- [ ] IAM role has `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:Query` on both tables
- [ ] Table schemas documented in `docs/schemas/`

## Child Tasks

_To be linked once task issues are created._
"@

Write-Host "`n=== Updating story #47: AWS EventBridge rules ===" -ForegroundColor Cyan
gh_issue_edit -number 47 -addLabels "comp:infra,phase:0-setup,priority:high" -body @"
## Summary

Configure EventBridge scheduled rules to trigger the daily and weekly pipeline
runs via the Lambda SSM dispatcher. Depends on story #48 (Lambda).

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/09_pipeline_orchestration_architecture.md

## Acceptance Criteria

- [ ] Daily rule created: `cron(0 21 * * ? *)` (21:00 UTC every weekday)
- [ ] Weekly rule created: `cron(0 21 ? * SUN *)` (21:00 UTC every Sunday)
- [ ] Lambda SSM dispatcher (#48) set as target for both rules
- [ ] Rules successfully invoke Lambda on manual test trigger
- [ ] Rules enabled in correct AWS region

## Child Tasks

_To be linked once task issues are created._
"@

Write-Host "`n=== Updating story #48: AWS Lambda SSM dispatcher ===" -ForegroundColor Cyan
gh_issue_edit -number 48 -addLabels "comp:infra,phase:0-setup,priority:high" -body @"
## Summary

Implement a lightweight Lambda function that receives EventBridge events and
issues an SSM RunCommand to the EC2 instance to start the pipeline. This is
the bridge between the scheduler and the EC2 compute layer.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/09_pipeline_orchestration_architecture.md

## Acceptance Criteria

- [ ] Lambda function written in Python 3.12 and tested locally
- [ ] Lambda deployed with correct execution role (SSM:SendCommand, logs:CreateLogGroup)
- [ ] Lambda reads EC2 instance ID and SSM document name from environment variables
- [ ] Lambda successfully triggers SSM Run Command on EC2 in smoke test
- [ ] End-to-end flow verified: EventBridge → Lambda → SSM → EC2

## Child Tasks

_To be linked once task issues are created._
"@

# ---------------------------------------------------------------------------
# STEP 2 — Create tasks for each story
# ---------------------------------------------------------------------------

Write-Host "`n=== Creating tasks for #44: IAM ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Define IAM roles inventory for EC2, Lambda, GitHub Actions OIDC" `
    -labels "type:task,comp:infra,phase:0-setup,priority:critical" `
    -body @"
## Parent Story
Part of #44

## Description
Document all IAM roles required by the project before provisioning. Define
which AWS services each role needs access to and at what permission scope.

**Roles to define:**
- `project-intelligent-ec2-role` — attached as EC2 instance profile
- `project-intelligent-lambda-role` — Lambda execution role
- `project-intelligent-ghactions-role` — GitHub Actions OIDC federation role

## Acceptance Criteria
- [ ] Roles inventory document created at `infra/iam/roles-inventory.md`
- [ ] Each role lists exact AWS actions needed (no wildcards)
- [ ] Resource ARNs scoped to this project's buckets / tables
"@

gh_issue_create `
    -title "[TASK] Write IAM policy JSON for EC2 instance profile" `
    -labels "type:task,comp:infra,phase:0-setup,priority:critical" `
    -body @"
## Parent Story
Part of #44

## Description
Create a least-privilege IAM policy for the EC2 instance profile.

**Required permissions:**
- `s3:GetObject`, `s3:PutObject` on project buckets
- `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:Query` on project tables
- `ssm:GetParameter`, `ssmmessages:*` (SSM Session Manager)
- `secretsmanager:GetSecretValue` on project secrets only
- `glue:GetTable`, `glue:UpdateTable`, `glue:BatchCreatePartition` on project databases

## Acceptance Criteria
- [ ] Policy JSON saved to `infra/iam/ec2-instance-policy.json`
- [ ] No `*` in Resource field — all ARNs scoped to project prefix
- [ ] Policy passes `aws iam simulate-principal-policy` validation
"@

gh_issue_create `
    -title "[TASK] Write IAM policy JSON for Lambda execution role" `
    -labels "type:task,comp:infra,phase:0-setup,priority:critical" `
    -body @"
## Parent Story
Part of #44

## Description
Create a least-privilege IAM policy for the Lambda SSM dispatcher function.

**Required permissions:**
- `ssm:SendCommand` on the EC2 instance ARN only
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

## Acceptance Criteria
- [ ] Policy JSON saved to `infra/iam/lambda-execution-policy.json`
- [ ] SSM SendCommand scoped to specific EC2 instance ARN
- [ ] CloudWatch Logs scoped to `/aws/lambda/project-intelligent-*`
"@

gh_issue_create `
    -title "[TASK] Write IAM policy JSON for GitHub Actions OIDC role" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #44

## Description
Configure GitHub Actions to authenticate to AWS via OIDC (no long-lived keys).
Create the trust policy and permission policy for the GitHub Actions role.

**Required permissions:**
- Scoped to deployment actions only (S3 artifact upload, Lambda update)
- Trust policy conditioned on `repo:biteberry/project-intelligent:ref:refs/heads/main`

## Acceptance Criteria
- [ ] OIDC identity provider created in AWS IAM for `token.actions.githubusercontent.com`
- [ ] Trust policy JSON saved to `infra/iam/ghactions-trust-policy.json`
- [ ] Permission policy JSON saved to `infra/iam/ghactions-permission-policy.json`
- [ ] GitHub Actions workflow can assume role and list target S3 bucket
"@

gh_issue_create `
    -title "[TASK] Provision all IAM roles via AWS CLI and verify" `
    -labels "type:task,comp:infra,phase:0-setup,priority:critical" `
    -body @"
## Parent Story
Part of #44

## Description
Create all IAM roles and attach policies using AWS CLI commands.
Record all ARNs in a reference file for use by other provisioning tasks.

## Acceptance Criteria
- [ ] All 3 roles created: EC2, Lambda, GitHub Actions OIDC
- [ ] Policies attached to correct roles
- [ ] Role ARNs documented in `infra/iam/role-arns.env` (non-secret)
- [ ] `aws iam get-role` confirms each role exists
- [ ] No wildcard `*` permissions in any attached policy
"@

# ---- #45 S3 ----
Write-Host "`n=== Creating tasks for #45: S3 Buckets ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Create 5 S3 buckets (landing/bronze/silver/gold/artifacts)" `
    -labels "type:task,comp:infra,phase:0-setup,priority:critical" `
    -body @"
## Parent Story
Part of #45

## Description
Create the 5 S3 buckets required by the medallion data architecture.
Use a consistent naming convention that includes the AWS account ID to ensure
global uniqueness: `project-intelligent-<layer>-<account_id>`.

**Buckets:**
- `project-intelligent-landing-<acct>`
- `project-intelligent-bronze-<acct>`
- `project-intelligent-silver-<acct>`
- `project-intelligent-gold-<acct>`
- `project-intelligent-artifacts-<acct>`

## Acceptance Criteria
- [ ] All 5 buckets created in `ap-south-1` (or configured region)
- [ ] Bucket names follow naming convention documented in `infra/s3/bucket-names.env`
- [ ] `aws s3 ls` confirms all 5 buckets exist
"@

gh_issue_create `
    -title "[TASK] Block public access and enable encryption on all S3 buckets" `
    -labels "type:task,comp:infra,phase:0-setup,priority:critical" `
    -body @"
## Parent Story
Part of #45

## Description
Apply security baseline to all 5 buckets: block public access and enable
server-side encryption (SSE-S3).

## Acceptance Criteria
- [ ] Public access blocked on all 5 buckets (all 4 BlockPublicAccess flags = true)
- [ ] SSE-S3 (`AES256`) encryption enabled as default on all 5 buckets
- [ ] `aws s3api get-bucket-encryption` confirms encryption on each bucket
"@

gh_issue_create `
    -title "[TASK] Enable versioning on bronze/silver/gold/artifacts S3 buckets" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #45

## Description
Enable S3 versioning on bronze, silver, gold, and artifacts buckets to support
point-in-time recovery per ADR-004. Landing zone does not need versioning.

## Acceptance Criteria
- [ ] Versioning enabled on bronze, silver, gold, artifacts buckets
- [ ] `aws s3api get-bucket-versioning` returns `Enabled` for each
"@

gh_issue_create `
    -title "[TASK] Configure S3 lifecycle policy on landing zone bucket" `
    -labels "type:task,comp:infra,phase:0-setup,priority:medium" `
    -body @"
## Parent Story
Part of #45

## Description
Add a lifecycle rule to the landing zone bucket to automatically expire raw
ingest files after 30 days, keeping storage costs near zero.

## Acceptance Criteria
- [ ] Lifecycle rule created: expire objects after 30 days
- [ ] Rule applies to all objects in `project-intelligent-landing-*`
- [ ] `aws s3api get-bucket-lifecycle-configuration` confirms the rule
"@

# ---- #46 DynamoDB ----
Write-Host "`n=== Creating tasks for #46: DynamoDB ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Design and document DynamoDB table schemas (predictions + audit)" `
    -labels "type:task,comp:data-store,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #46

## Description
Define the DynamoDB key schema and attribute map for both tables before creation.

**predictions table:**
- PK: `symbol#date` (e.g. `RELIANCE#2026-05-07`)
- SK: `horizon#model_version` (e.g. `swing#v1.2`)
- Attributes: `predicted_direction`, `confidence_score`, `features_hash`, `ttl`

**audit table:**
- PK: `job_date` (e.g. `2026-05-07`)
- SK: `job_id` (e.g. `daily-swing-20260507T2100Z`)
- Attributes: `status`, `records_processed`, `error_message`, `duration_seconds`

## Acceptance Criteria
- [ ] Schemas documented in `docs/schemas/dynamodb_predictions.md`
- [ ] Schemas documented in `docs/schemas/dynamodb_audit.md`
- [ ] GSI design included if needed for query patterns
"@

gh_issue_create `
    -title "[TASK] Create DynamoDB predictions table with on-demand billing" `
    -labels "type:task,comp:data-store,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #46

## Description
Provision the `project-intelligent-predictions` DynamoDB table using the schema
defined in the design task. Use PAY_PER_REQUEST billing to stay within Free Tier.

## Acceptance Criteria
- [ ] Table `project-intelligent-predictions` created
- [ ] Billing mode: `PAY_PER_REQUEST`
- [ ] TTL attribute `ttl` enabled (90-day retention)
- [ ] `aws dynamodb describe-table` confirms table is ACTIVE
"@

gh_issue_create `
    -title "[TASK] Create DynamoDB audit table with on-demand billing" `
    -labels "type:task,comp:data-store,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #46

## Description
Provision the `project-intelligent-audit` DynamoDB table for pipeline job
tracking. Use PAY_PER_REQUEST billing.

## Acceptance Criteria
- [ ] Table `project-intelligent-audit` created
- [ ] Billing mode: `PAY_PER_REQUEST`
- [ ] `aws dynamodb describe-table` confirms table is ACTIVE
- [ ] IAM EC2 role has `dynamodb:PutItem` and `dynamodb:Query` on this table
"@

# ---- #47 EventBridge ----
Write-Host "`n=== Creating tasks for #47: EventBridge ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Create EventBridge rule for daily pipeline trigger at 21:00 UTC" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #47

## Description
Create an EventBridge scheduled rule that fires every day at 21:00 UTC
(after US market close) to trigger the daily swing/intraday pipeline run.

**Cron expression:** `cron(0 21 * * ? *)`

## Acceptance Criteria
- [ ] Rule `project-intelligent-daily-trigger` created and enabled
- [ ] Target set to Lambda SSM dispatcher function (#48)
- [ ] Manual test invocation reaches Lambda successfully
"@

gh_issue_create `
    -title "[TASK] Create EventBridge rule for weekly Sunday pipeline trigger" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #47

## Description
Create an EventBridge scheduled rule that fires every Sunday at 21:00 UTC
to trigger the weekly long-term model retraining pipeline.

**Cron expression:** `cron(0 21 ? * SUN *)`

## Acceptance Criteria
- [ ] Rule `project-intelligent-weekly-trigger` created and enabled
- [ ] Target set to Lambda SSM dispatcher function (#48)
- [ ] Rule passes `aws events test-event-pattern` validation
"@

gh_issue_create `
    -title "[TASK] Verify EventBridge → Lambda end-to-end invocation" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #47

## Description
Perform end-to-end smoke test of both EventBridge rules by manually invoking
them and confirming the Lambda function receives and processes the event.

## Acceptance Criteria
- [ ] Daily rule manual trigger → Lambda invoked (check CloudWatch Logs)
- [ ] Weekly rule manual trigger → Lambda invoked (check CloudWatch Logs)
- [ ] No IAM permission errors in Lambda logs
"@

# ---- #48 Lambda ----
Write-Host "`n=== Creating tasks for #48: Lambda SSM dispatcher ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Write Lambda SSM dispatcher function code" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #48

## Description
Implement the Lambda function that receives an EventBridge event and issues
an SSM `SendCommand` to the EC2 instance to start the pipeline script.

**Runtime:** Python 3.12
**Location:** `src/lambda/ssm_dispatcher/handler.py`

**Logic:**
1. Parse event source (daily vs weekly) from EventBridge event
2. Read `EC2_INSTANCE_ID` and `SSM_DOCUMENT_NAME` from environment variables
3. Call `ssm.send_command()` with the appropriate pipeline arguments
4. Log command ID to CloudWatch

## Acceptance Criteria
- [ ] `handler.py` created under `src/lambda/ssm_dispatcher/`
- [ ] Unit tests written in `tests/lambda/test_ssm_dispatcher.py`
- [ ] Function handles both daily and weekly event types
- [ ] Secrets / instance IDs read from env vars only (no hardcoded values)
"@

gh_issue_create `
    -title "[TASK] Deploy Lambda SSM dispatcher to AWS" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #48

## Description
Package and deploy the Lambda function to AWS. Configure environment variables
and attach the Lambda execution role created in #44.

## Acceptance Criteria
- [ ] Lambda function `project-intelligent-ssm-dispatcher` deployed
- [ ] Runtime: Python 3.12, Memory: 128 MB, Timeout: 30s
- [ ] Environment variables set: `EC2_INSTANCE_ID`, `SSM_DOCUMENT_NAME`
- [ ] Lambda execution role (from #44) attached
- [ ] `aws lambda invoke` test call succeeds
"@

gh_issue_create `
    -title "[TASK] End-to-end smoke test: EventBridge → Lambda → SSM → EC2" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #48

## Description
Perform a full end-to-end smoke test to verify the entire orchestration chain
works before writing any pipeline code.

**Test flow:**
1. Manually trigger daily EventBridge rule
2. Confirm Lambda invoked in CloudWatch Logs
3. Confirm SSM SendCommand dispatched to EC2
4. Confirm EC2 receives and runs a test echo command

## Acceptance Criteria
- [ ] EventBridge → Lambda invocation confirmed in CW Logs
- [ ] Lambda → SSM SendCommand confirmed (check SSM Run Command history)
- [ ] SSM → EC2 echo command output visible in SSM command output
- [ ] No IAM permission errors anywhere in the chain
"@

# ---- #49 CloudWatch ----
Write-Host "`n=== Creating tasks for #49: CloudWatch ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Create SNS topic and subscribe alert email" `
    -labels "type:task,comp:monitoring,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #49

## Description
Create an SNS topic for all project alerts and subscribe the operator email
address. This topic will be used as the action for all CloudWatch alarms.

## Acceptance Criteria
- [ ] SNS topic `project-intelligent-alerts` created
- [ ] Email subscription confirmed (check inbox for confirmation email)
- [ ] Topic ARN saved to `infra/monitoring/sns-topic-arn.env`
"@

gh_issue_create `
    -title "[TASK] Create CloudWatch billing alarm at USD 0.10 threshold" `
    -labels "type:task,comp:monitoring,phase:0-setup,priority:critical" `
    -body @"
## Parent Story
Part of #49

## Description
Create a CloudWatch billing alarm that fires when estimated AWS charges exceed
USD 0.10. This is the primary cost guard for the free-tier project.

Note: Billing metrics are only available in `us-east-1`.

## Acceptance Criteria
- [ ] Billing alarm `project-intelligent-billing-010` created in `us-east-1`
- [ ] Threshold: USD 0.10, statistic: Maximum, period: 86400s
- [ ] Alarm action: SNS topic `project-intelligent-alerts`
- [ ] Test: manually set alarm state to ALARM and confirm email received
"@

gh_issue_create `
    -title "[TASK] Create CloudWatch alarms for EC2 and Lambda health" `
    -labels "type:task,comp:monitoring,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #49

## Description
Create operational CloudWatch alarms for the two compute resources.

**Alarms to create:**
- EC2 `CPUUtilization` > 80% for 2 consecutive 5-min periods
- Lambda `Errors` >= 1 in any 5-min window
- Lambda `Duration` > 25000ms (near 30s timeout)

## Acceptance Criteria
- [ ] EC2 CPU alarm created and linked to SNS topic
- [ ] Lambda errors alarm created and linked to SNS topic
- [ ] Lambda duration alarm created and linked to SNS topic
- [ ] All alarms in OK state after initial setup
"@

# ---- #50 Secrets Manager ----
Write-Host "`n=== Creating tasks for #50: Secrets Manager ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Define and document secret naming convention" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #50

## Description
Establish a consistent naming convention for all AWS Secrets Manager secrets
before any secrets are created.

**Convention:** `/project-intelligent/<service>/<key-type>`

**Examples:**
- `/project-intelligent/finnhub/api-key`
- `/project-intelligent/alphavantage/api-key`
- `/project-intelligent/postgres/password`

## Acceptance Criteria
- [ ] Naming convention documented in `docs/architecture/06_platform_mlops_observability_security.md`
- [ ] Convention reviewed against NFR-05 (Security)
"@

gh_issue_create `
    -title "[TASK] Create Secrets Manager secret placeholders for all external APIs" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #50

## Description
Pre-create all secret entries in AWS Secrets Manager with placeholder values.
Actual keys will be populated before pipeline runs.

**Secrets to create:**
- `/project-intelligent/finnhub/api-key` → placeholder `REPLACE_ME`
- `/project-intelligent/alphavantage/api-key` → placeholder `REPLACE_ME`

## Acceptance Criteria
- [ ] All secret entries created (placeholder values)
- [ ] `aws secretsmanager list-secrets` shows all expected secrets
- [ ] IAM policy restricts access to specific secret ARNs (no wildcard resource)
"@

gh_issue_create `
    -title "[TASK] Scan codebase to verify zero API keys in committed files" `
    -labels "type:task,comp:infra,phase:0-setup,priority:critical" `
    -body @"
## Parent Story
Part of #50

## Description
Run automated secret detection to verify no API keys, passwords, or tokens
are present in any committed file. Block future commits via pre-commit hook.

**Tools:** `git-secrets` or `trufflehog` or `detect-secrets`

## Acceptance Criteria
- [ ] Secret scan passes with zero findings
- [ ] `.gitignore` includes all `.env` files and credential files
- [ ] Pre-commit hook or CI step added to block future secret commits
- [ ] `detect-secrets` baseline file committed to repo
"@

# ---- #52 Glue Catalog ----
Write-Host "`n=== Creating tasks for #52: Glue Catalog ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Enable AWS Glue Data Catalog and create layer databases" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #52

## Description
Enable the AWS Glue Data Catalog in the project region and create three
databases corresponding to the medallion architecture layers.

**Databases to create:**
- `project_intelligent_bronze`
- `project_intelligent_silver`
- `project_intelligent_gold`

## Acceptance Criteria
- [ ] Glue Data Catalog enabled in target region
- [ ] All 3 databases created
- [ ] `aws glue get-databases` lists all 3
"@

gh_issue_create `
    -title "[TASK] Register Iceberg table schemas in Glue Catalog" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #52

## Description
Register initial Iceberg table schemas for the bronze OHLCV table in the
Glue Catalog. Other tables will be registered as their schemas are finalised.

**Schema references:**
- `schemas/bronze_ohlcv.schema.json`
- `schemas/silver_ohlcv.schema.json`
- `schemas/gold_swing_features.schema.json`

## Acceptance Criteria
- [ ] Bronze OHLCV Iceberg table registered in `project_intelligent_bronze` database
- [ ] Silver OHLCV Iceberg table registered in `project_intelligent_silver` database
- [ ] Gold swing features table registered in `project_intelligent_gold` database
- [ ] Table metadata accessible via `aws glue get-table`
"@

gh_issue_create `
    -title "[TASK] Verify IAM role has Glue Catalog read/write access" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #52

## Description
Confirm the EC2 instance role has the necessary Glue permissions to read and
update table metadata when writing Iceberg data.

**Required Glue permissions:**
- `glue:GetDatabase`, `glue:GetTable`, `glue:GetTables`
- `glue:CreateTable`, `glue:UpdateTable`, `glue:BatchCreatePartition`

## Acceptance Criteria
- [ ] EC2 IAM role policy includes all required Glue permissions
- [ ] `aws iam simulate-principal-policy` confirms access
- [ ] Test script from EC2 can call `aws glue get-databases` successfully
"@

# ---- #53 EC2 ----
Write-Host "`n=== Creating tasks for #53: EC2 Python environment ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Launch EC2 t2.micro with Amazon Linux 2 and IAM instance profile" `
    -labels "type:task,comp:infra,phase:0-setup,priority:critical" `
    -body @"
## Parent Story
Part of #53

## Description
Launch the project EC2 instance with the correct AMI, instance type, and IAM
instance profile. No SSH key pair — access via SSM Session Manager only.

## Acceptance Criteria
- [ ] EC2 t2.micro launched with Amazon Linux 2023 AMI
- [ ] IAM instance profile `project-intelligent-ec2-role` attached (from #44)
- [ ] No SSH key pair associated with the instance
- [ ] Security group has no inbound rules (outbound only for SSM/HTTPS)
- [ ] Instance ID saved to `infra/ec2/instance-id.env`
"@

gh_issue_create `
    -title "[TASK] Install Python 3.12 and project dependencies on EC2 via SSM" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #53

## Description
Install Python 3.12 and all required Python packages on the EC2 instance
using SSM Run Command (not SSH). Create a virtualenv for the project.

**Packages (minimum):** `boto3`, `pandas`, `pyarrow`, `pyiceberg`, `scikit-learn`,
`finnhub-python`, `pytest`, `ruff`

## Acceptance Criteria
- [ ] Python 3.12 installed and available at `/usr/local/bin/python3.12`
- [ ] Virtual environment created at `/home/ec2-user/project-intelligent/venv`
- [ ] All packages installed in venv
- [ ] `python --version` returns 3.12.x via SSM Run Command
"@

gh_issue_create `
    -title "[TASK] Verify EC2 accessible via SSM Session Manager only" `
    -labels "type:task,comp:infra,phase:0-setup,priority:critical" `
    -body @"
## Parent Story
Part of #53

## Description
Confirm that the EC2 instance is reachable exclusively via SSM Session Manager
and that no direct SSH access is possible (per NFR-05).

## Acceptance Criteria
- [ ] `aws ssm start-session --target <instance-id>` opens a shell successfully
- [ ] Port 22 is not accessible (security group has no inbound rule for port 22)
- [ ] SSM Agent is running on the instance: `systemctl status amazon-ssm-agent`
- [ ] EC2 instance passes SSM Fleet Manager health check
"@

# ---- #54 PostgreSQL ----
Write-Host "`n=== Creating tasks for #54: PostgreSQL ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Set up local PostgreSQL via Docker Compose" `
    -labels "type:task,comp:data-store,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #54

## Description
Create a Docker Compose file to run PostgreSQL locally for development and
backtesting workloads as defined in ADR-003.

**Configuration:**
- Image: `postgres:16`
- Port: `5432` (localhost only)
- Volume: `./data/postgres` for persistence
- Credentials: read from `.env` file (not committed)

## Acceptance Criteria
- [ ] `docker-compose.yml` created at project root (or `infra/local/`)
- [ ] `docker compose up -d` starts PostgreSQL successfully
- [ ] `.env.example` created with placeholder credential keys
- [ ] `.env` added to `.gitignore`
"@

gh_issue_create `
    -title "[TASK] Write SQL migration scripts per ADR-003 schema" `
    -labels "type:task,comp:data-store,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #54

## Description
Write SQL DDL migration scripts for all tables defined in ADR-003.

**Tables to create (minimum):**
- `universe` — tracked symbols with tier and metadata
- `backtest_results` — backtesting run output per model/horizon
- `signal_log` — generated signals with timestamps

## Acceptance Criteria
- [ ] Migration scripts created at `infra/postgres/migrations/`
- [ ] Script `001_create_universe.sql` creates `universe` table
- [ ] Script `002_create_backtest_results.sql` created
- [ ] Script `003_create_signal_log.sql` created
- [ ] All migrations run successfully: `psql < 001_*.sql` etc.
- [ ] Schema matches ADR-003 design
"@

gh_issue_create `
    -title "[TASK] Verify PostgreSQL schema and document connection config" `
    -labels "type:task,comp:data-store,phase:0-setup,priority:medium" `
    -body @"
## Parent Story
Part of #54

## Description
Run all migrations, verify the schema is correct, and document how to connect
for local development (without committing passwords).

## Acceptance Criteria
- [ ] All tables exist and pass `\d <table>` inspection in psql
- [ ] Connection config documented in `docs/local-dev-setup.md`
- [ ] `psql` connection string uses env vars only (no hardcoded passwords)
- [ ] Schema matches ADR-003 ERD
"@

# ---- #55 GitHub Actions CI ----
Write-Host "`n=== Creating tasks for #55: GitHub Actions CI ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Create .github/workflows/ci.yml with lint and test steps" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #55

## Description
Create the GitHub Actions CI workflow that runs on every push and pull request
to the `main` branch.

**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install dependencies from `requirements-dev.txt`
4. Run `ruff check .` (lint)
5. Run `pytest tests/` (unit tests)

## Acceptance Criteria
- [ ] `.github/workflows/ci.yml` created
- [ ] Workflow triggers on `push` and `pull_request` to `main`
- [ ] Lint step uses `ruff` (not flake8)
- [ ] Test step uses `pytest` with `--tb=short` output
- [ ] Workflow passes on a clean commit with empty test suite
"@

gh_issue_create `
    -title "[TASK] Add requirements-dev.txt and verify CI passes" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #55

## Description
Create the `requirements-dev.txt` file with all development dependencies
needed for the CI lint and test steps, and push a commit to verify CI passes.

**Minimum contents:**
- `ruff`
- `pytest`
- `pytest-cov`
- `boto3` (for unit test mocks)
- `moto[s3,dynamodb,secretsmanager]` (AWS mock library)

## Acceptance Criteria
- [ ] `requirements-dev.txt` committed to repo root
- [ ] CI workflow runs successfully on push (green badge)
- [ ] Both lint and test steps pass
- [ ] Coverage report generated (even at 0% initially)
"@

# ---- #56 Finnhub API key ----
Write-Host "`n=== Creating tasks for #56: Finnhub API key ===" -ForegroundColor Yellow

gh_issue_create `
    -title "[TASK] Register Finnhub account and obtain API key" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #56

## Description
Sign up for a Finnhub account at https://finnhub.io and obtain the free-tier
API key. Verify the key works against the sandbox endpoint.

## Acceptance Criteria
- [ ] Finnhub account created
- [ ] API key obtained (free tier)
- [ ] Test call `GET /api/v1/quote?symbol=AAPL` returns valid data
- [ ] Key is NOT stored in any file — only in AWS Secrets Manager
"@

gh_issue_create `
    -title "[TASK] Store Finnhub API key in AWS Secrets Manager" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #56

## Description
Create the AWS Secrets Manager secret for the Finnhub API key and update the
placeholder value created in story #50.

**Secret name:** `/project-intelligent/finnhub/api-key`

## Acceptance Criteria
- [ ] Secret value updated from `REPLACE_ME` to actual API key
- [ ] `aws secretsmanager get-secret-value` retrieves the key successfully from EC2
- [ ] Access restricted to EC2 IAM role and Lambda role only
- [ ] Key is not present in any repository file (verify with secret scan)
"@

gh_issue_create `
    -title "[TASK] Write Python helper to retrieve secrets at runtime" `
    -labels "type:task,comp:infra,phase:0-setup,priority:high" `
    -body @"
## Parent Story
Part of #56

## Description
Implement a reusable Python utility function that retrieves secrets from
AWS Secrets Manager at runtime. All pipeline code must use this helper —
no hardcoded credentials anywhere.

**Location:** `src/utils/secrets.py`

```python
def get_secret(secret_name: str) -> str:
    \"\"\"Retrieve a secret value from AWS Secrets Manager.\"\"\"
    ...
```

## Acceptance Criteria
- [ ] `src/utils/secrets.py` created with `get_secret()` function
- [ ] Function caches secret in memory for the process lifetime (avoid repeated API calls)
- [ ] Unit test in `tests/utils/test_secrets.py` using `moto` mock
- [ ] Used in Finnhub client initialisation as proof of integration
"@

Write-Host "`n=== All done! ===" -ForegroundColor Green
Write-Host "Updated stories: #44, #45, #46, #47, #48" -ForegroundColor Green
Write-Host "Created tasks for stories: #44, #45, #46, #47, #48, #49, #50, #52, #53, #54, #55, #56" -ForegroundColor Green
