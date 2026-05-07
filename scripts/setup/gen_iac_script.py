"""
Generates create_iac_stories_tasks.ps1 — all story/task bodies are built
as Python strings (no PowerShell here-string pitfalls), then written
directly into the .ps1 file as safe single-quoted escaped strings.
"""

import os

OUT = os.path.join(os.path.dirname(__file__), "create_iac_stories_tasks.ps1")

# ── helpers ──────────────────────────────────────────────────────────────────

def ps_str(text: str) -> str:
    """Return a PowerShell single-quoted string literal for *text*.
    Single-quoted strings never expand variables, so they are safe for
    multi-line markdown bodies. The only character that needs escaping in
    single-quoted strings is a single-quote itself (doubled: '').
    """
    escaped = text.replace("'", "''")
    return f"@'\n{escaped}\n'@"


def new_issue_call(title: str, labels: str, body: str, var: str) -> str:
    """Emit a New-GhIssue call that stores the issue number in *var*."""
    body_literal = ps_str(body)
    return (
        f"${var} = New-GhIssue \\\n"
        f"    -title {ps_str(title)} \\\n"
        f"    -labels '{labels}' \\\n"
        f"    -body {body_literal}\n"
    ).replace(" \\\n", " `\n")


# ── story bodies ─────────────────────────────────────────────────────────────

S1_BODY = """\
## Summary

Bootstrap the Terraform project: directory structure, AWS provider version pin,
variable definitions, and remote S3 backend for state management.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/06_platform_mlops_observability_security.md (IaC Strategy section)
- docs/architecture/13_github_repository_structure.md (infra/ layout)

## Acceptance Criteria

- [ ] `infra/terraform/` directory created with `providers.tf`, `variables.tf`, `outputs.tf`, `backend.tf`
- [ ] `terraform.tfvars.example` committed with safe placeholder values
- [ ] `terraform.tfvars` added to `.gitignore`
- [ ] Remote state bucket exists in S3 artifacts bucket under `terraform/state/`
- [ ] `terraform init` succeeds with remote backend
- [ ] AWS provider pinned to `~> 5.50`

## Child Tasks

_To be linked once task issues are created._"""

S2_BODY = """\
## Summary

Implement `infra/terraform/modules/iam/` to provision all three IAM roles:
EC2 instance profile, Lambda execution role, and GitHub Actions OIDC role.
No wildcard * permissions anywhere.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/06_platform_mlops_observability_security.md
- docs/adr/ADR-004-backup-and-failover.md

## Acceptance Criteria

- [ ] Module file `infra/terraform/modules/iam/main.tf` created
- [ ] EC2 role: least-privilege for S3, DynamoDB, SSM, Secrets Manager, Glue (scoped to project ARNs)
- [ ] Lambda role: SSM SendCommand + CloudWatch Logs only
- [ ] GitHub Actions OIDC role: trust conditioned on `repo:biteberry/project-intelligent:ref:refs/heads/main`
- [ ] No wildcard `*` in any Resource field
- [ ] `terraform plan` shows 0 errors for this module
- [ ] Module outputs: `ec2_instance_role_arn`, `ec2_instance_profile_name`, `lambda_execution_role_arn`, `github_actions_role_arn`

## Child Tasks

_To be linked once task issues are created._"""

S3_BODY = """\
## Summary

Implement `infra/terraform/modules/s3/` to provision all 5 medallion S3 buckets
with public access block, SSE-S3 encryption, versioning, and landing zone lifecycle.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/03_data_architecture_medallion.md
- docs/architecture/06_platform_mlops_observability_security.md

## Acceptance Criteria

- [ ] Module creates: landing, bronze, silver, gold, artifacts buckets
- [ ] All buckets: public access fully blocked, SSE-S3 encryption enabled
- [ ] Versioning enabled on bronze, silver, gold, artifacts (not landing)
- [ ] Landing zone lifecycle rule: expire all objects after 30 days
- [ ] Bucket names include account ID for global uniqueness
- [ ] Module outputs all 5 bucket names

## Child Tasks

_To be linked once task issues are created._"""

S4_BODY = """\
## Summary

Implement `infra/terraform/modules/dynamodb/` for the predictions and audit
tables using on-demand billing and TTL.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/04_model_strategy_and_serving.md
- docs/adr/ADR-003-database-decision.md

## Acceptance Criteria

- [ ] `project-intelligent-predictions` table: PK `symbol_date` (S), SK `horizon_model` (S), TTL on `ttl` attribute
- [ ] `project-intelligent-audit` table: PK `job_date` (S), SK `job_id` (S)
- [ ] Both tables: `PAY_PER_REQUEST` billing mode
- [ ] Module outputs table names and ARNs
- [ ] `terraform plan` shows correct schema

## Child Tasks

_To be linked once task issues are created._"""

S5_BODY = """\
## Summary

Implement `infra/terraform/modules/ec2/` to launch the t2.micro instance with
SSM-only access. No SSH key pair. No port 22.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/06_platform_mlops_observability_security.md (NFR-05 - SSM only)

## Acceptance Criteria

- [ ] EC2 t2.micro with Amazon Linux 2023 AMI (dynamic data source - no hardcoded AMI ID)
- [ ] IAM instance profile attached
- [ ] No SSH key pair associated
- [ ] Security group: zero inbound rules; egress HTTPS 443 only
- [ ] `terraform apply` brings up a reachable instance
- [ ] `aws ssm start-session` opens a shell after apply

## Child Tasks

_To be linked once task issues are created._"""

S6_BODY = """\
## Summary

Implement `infra/terraform/modules/lambda_dispatcher/` and
`infra/terraform/modules/eventbridge/` for the pipeline orchestration chain.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/09_pipeline_orchestration_architecture.md

## Acceptance Criteria

- [ ] Lambda function: Python 3.12, 128 MB, 30s timeout
- [ ] Lambda env vars: `EC2_INSTANCE_ID`, `SSM_DOCUMENT_NAME` (from variables - not hardcoded)
- [ ] EventBridge daily rule: `cron(0 21 * * ? *)` targeting Lambda
- [ ] EventBridge weekly rule: `cron(0 21 ? * SUN *)` targeting Lambda
- [ ] Lambda permission resource allows EventBridge to invoke the function

## Child Tasks

_To be linked once task issues are created._"""

S7_BODY = """\
## Summary

Implement remaining Terraform modules (CloudWatch/SNS, Secrets Manager, Glue Catalog)
and wire all modules together in the root `main.tf`.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/06_platform_mlops_observability_security.md

## Acceptance Criteria

- [ ] SNS topic + email subscription created
- [ ] EC2 CPU alarm, Lambda error alarm, Lambda duration alarm created
- [ ] Billing alarm note: delivered via CloudFormation (us-east-1 constraint)
- [ ] Secrets Manager secrets created with `REPLACE_ME` placeholder; `ignore_changes` on secret_string
- [ ] Glue databases: `project_intelligent_bronze`, `project_intelligent_silver`, `project_intelligent_gold`
- [ ] Root `main.tf` calls all 8 modules with correct inter-module variable passing
- [ ] `terraform validate` and `terraform plan` pass from root with no errors

## Child Tasks

_To be linked once task issues are created._"""

S8_BODY = """\
## Summary

Write CloudFormation/SAM templates for the billing alarm (us-east-1 constraint)
and the Lambda + EventBridge SAM wiring as an alternative learning exercise.

## Parent Feature

Part of #2

## Architecture Reference

- docs/architecture/06_platform_mlops_observability_security.md (CloudFormation section)

## Acceptance Criteria

- [ ] `infra/cloudformation/04-monitoring.yaml` - billing alarm at $0.10 in us-east-1
- [ ] `infra/cloudformation/sam/dispatcher.yaml` - SAM template for Lambda + EventBridge
- [ ] All templates pass `cfn-lint` validation
- [ ] `cfn-lint` added as a CI step in GitHub Actions

## Child Tasks

_To be linked once task issues are created._"""

S9_BODY = """\
## Summary

Execute `terraform apply` to provision the full AWS environment from all
Terraform modules. This is the gate before any pipeline code is written.
All module stories must be complete and `terraform plan` clean before starting.

## Parent Feature

Part of #2

## Acceptance Criteria

- [ ] `terraform plan` shows all expected resources with no errors before apply
- [ ] `terraform apply` completes with exit code 0
- [ ] All 5 S3 buckets exist, encrypted, public access blocked
- [ ] Both DynamoDB tables are in ACTIVE state
- [ ] EC2 instance reachable via `aws ssm start-session`
- [ ] Lambda function deployed and invocable
- [ ] Both EventBridge rules are ENABLED
- [ ] SNS email subscription confirmed
- [ ] Glue Catalog databases visible in AWS console
- [ ] Terraform state stored in S3 remote backend

## Child Tasks

_To be linked once task issues are created._"""

# ── task bodies (use PARENT placeholder replaced at emit time) ────────────────

TASKS = {
    # Story 1 tasks
    "t1_1": {
        "title": "[TASK] Create infra/terraform/ directory structure and provider config",
        "labels": "type:task,comp:infra,phase:0-setup,priority:critical",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create the top-level Terraform directory layout and configure the AWS provider.

Files to create:
- `infra/terraform/providers.tf` - AWS provider, version pin `~> 5.50`, default project tags
- `infra/terraform/variables.tf` - `aws_region`, `environment`, `project_prefix`, `alert_email`, `github_repo`
- `infra/terraform/outputs.tf` - root-level output stubs
- `infra/terraform/terraform.tfvars.example` - safe example values (never commit real values)

## Acceptance Criteria

- [ ] All 4 files created under `infra/terraform/`
- [ ] `terraform validate` passes
- [ ] `terraform.tfvars` entry added to `.gitignore`""",
    },
    "t1_2": {
        "title": "[TASK] Configure Terraform S3 remote backend",
        "labels": "type:task,comp:infra,phase:0-setup,priority:critical",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/terraform/backend.tf` to store Terraform state remotely in the
S3 artifacts bucket. The artifacts bucket must be created first (bootstrap step).

Key config: bucket key `terraform/state/project-intelligent.tfstate`, encrypt = true.

## Acceptance Criteria

- [ ] `backend.tf` committed with correct bucket and key path
- [ ] `terraform init` succeeds connecting to the remote backend
- [ ] State file visible at the correct S3 key path""",
    },
    "t1_3": {
        "title": "[TASK] Add terraform plan CI step to GitHub Actions",
        "labels": "type:task,comp:infra,phase:0-setup,priority:high",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Add a CI job to GitHub Actions that runs `terraform plan` on every PR touching
`infra/terraform/`. Apply is intentionally NOT automated - manual approval only.

Steps: checkout -> configure AWS OIDC credentials -> terraform init -> terraform validate -> terraform plan.
Plan output should be posted as a PR comment.

## Acceptance Criteria

- [ ] CI job triggers on changes to `infra/terraform/**`
- [ ] `terraform apply` is NOT in the CI workflow
- [ ] Plan output visible in PR comments""",
    },
    # Story 2 tasks
    "t2_1": {
        "title": "[TASK] Write Terraform IAM module: EC2 instance profile and policy",
        "labels": "type:task,comp:infra,phase:0-setup,priority:critical",
        "body": """\
## Parent Story
Part of #PARENT

## Description
In `infra/terraform/modules/iam/main.tf`, define:
- `aws_iam_role.ec2` with EC2 trust policy
- `aws_iam_role_policy.ec2_policy` - permissions for S3, DynamoDB, SSM, Secrets Manager, Glue (all scoped to project ARNs)
- `aws_iam_instance_profile.ec2`

## Acceptance Criteria

- [ ] No wildcard `*` in Resource - all ARNs scoped to `project-intelligent-*`
- [ ] `terraform validate` passes
- [ ] `terraform plan` shows correct policy document""",
    },
    "t2_2": {
        "title": "[TASK] Write Terraform IAM module: Lambda execution role and policy",
        "labels": "type:task,comp:infra,phase:0-setup,priority:critical",
        "body": """\
## Parent Story
Part of #PARENT

## Description
In `infra/terraform/modules/iam/main.tf`, define:
- `aws_iam_role.lambda` with Lambda service trust policy
- `aws_iam_role_policy.lambda_policy` - SSM SendCommand scoped to EC2 instance ARN + CloudWatch Logs scoped to `/aws/lambda/project-intelligent-*`

## Acceptance Criteria

- [ ] SSM SendCommand Resource is scoped to specific EC2 instance ARN (not wildcard)
- [ ] `terraform validate` passes""",
    },
    "t2_3": {
        "title": "[TASK] Write Terraform IAM module: GitHub Actions OIDC role",
        "labels": "type:task,comp:infra,phase:0-setup,priority:high",
        "body": """\
## Parent Story
Part of #PARENT

## Description
In `infra/terraform/modules/iam/main.tf`, define:
- `aws_iam_openid_connect_provider.github` for `token.actions.githubusercontent.com`
- `aws_iam_role.github_actions` with OIDC trust conditioned on `repo:biteberry/project-intelligent:ref:refs/heads/main`
- `aws_iam_role_policy.github_actions_policy` - S3 artifact upload + Lambda UpdateFunctionCode only

## Acceptance Criteria

- [ ] OIDC trust uses `StringLike` for the sub claim
- [ ] Permissions scoped to project artifacts bucket and project Lambda ARNs only
- [ ] `terraform plan` shows OIDC provider and role correctly""",
    },
    # Story 3 tasks
    "t3_1": {
        "title": "[TASK] Write Terraform S3 module: bucket creation with security baseline",
        "labels": "type:task,comp:infra,phase:0-setup,priority:critical",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/terraform/modules/s3/main.tf`.
Use `for_each` over a locals map to create all 5 buckets.
Apply `aws_s3_bucket_public_access_block` and
`aws_s3_bucket_server_side_encryption_configuration` to all buckets via `for_each`.

## Acceptance Criteria

- [ ] All 5 buckets defined via `for_each`
- [ ] Public access fully blocked on all 5 (all 4 flags = true)
- [ ] SSE-S3 (AES256) set as default encryption on all 5
- [ ] `terraform plan` shows correct resource count""",
    },
    "t3_2": {
        "title": "[TASK] Write Terraform S3 module: versioning and lifecycle rules",
        "labels": "type:task,comp:infra,phase:0-setup,priority:high",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Add to `infra/terraform/modules/s3/main.tf`:
- `aws_s3_bucket_versioning` applied to bronze, silver, gold, artifacts only (filtered `for_each`)
- `aws_s3_bucket_lifecycle_configuration` on landing bucket: expire all objects after 30 days

## Acceptance Criteria

- [ ] Versioning Enabled on 4 buckets; landing has no versioning resource
- [ ] Lifecycle rule targets all objects in landing bucket (empty filter)
- [ ] `terraform plan` shows correct versioning and lifecycle resources""",
    },
    # Story 4 tasks
    "t4_1": {
        "title": "[TASK] Write Terraform DynamoDB module: predictions and audit tables",
        "labels": "type:task,comp:data-store,phase:0-setup,priority:high",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/terraform/modules/dynamodb/main.tf` with both DynamoDB tables.

predictions table: hash_key `symbol_date` (S), range_key `horizon_model` (S), TTL attribute `ttl`, PAY_PER_REQUEST.
audit table: hash_key `job_date` (S), range_key `job_id` (S), PAY_PER_REQUEST.

## Acceptance Criteria

- [ ] Both tables defined with correct key schema
- [ ] TTL enabled on predictions table only
- [ ] `terraform plan` shows PAY_PER_REQUEST on both tables
- [ ] Module outputs: `predictions_table_name`, `predictions_table_arn`, `audit_table_name`, `audit_table_arn`""",
    },
    # Story 5 tasks
    "t5_1": {
        "title": "[TASK] Write Terraform EC2 module: instance, security group, AMI data source",
        "labels": "type:task,comp:infra,phase:0-setup,priority:critical",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/terraform/modules/ec2/main.tf`.

Resources:
- `data.aws_ami.amazon_linux_2023` - dynamic lookup (filter on AL2023 name pattern, most_recent = true)
- `aws_security_group.ec2` - zero ingress rules; egress port 443 to 0.0.0.0/0 only
- `aws_instance.this` - t2.micro, no key_name, attach IAM instance profile, attach SG

## Acceptance Criteria

- [ ] AMI looked up dynamically - no hardcoded AMI ID anywhere
- [ ] `key_name` is NOT set on the instance
- [ ] Security group has zero ingress blocks
- [ ] Module output: `instance_id`
- [ ] `terraform plan` shows instance with correct attributes""",
    },
    # Story 6 tasks
    "t6_1": {
        "title": "[TASK] Write Terraform Lambda dispatcher module",
        "labels": "type:task,comp:infra,phase:0-setup,priority:high",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/terraform/modules/lambda_dispatcher/main.tf`.

Resources:
- `aws_lambda_function.dispatcher` - runtime python3.12, memory 128 MB, timeout 30s
- Environment variables: `EC2_INSTANCE_ID` and `SSM_DOCUMENT_NAME` passed as module variables (not hardcoded)
- Deployment package: S3 object reference (zip uploaded to artifacts bucket by CI)

## Acceptance Criteria

- [ ] No hardcoded EC2 instance ID - must be passed in as a variable
- [ ] `terraform plan` shows function with correct runtime and config
- [ ] Module outputs: `function_arn`, `function_name`""",
    },
    "t6_2": {
        "title": "[TASK] Write Terraform EventBridge module: daily and weekly schedule rules",
        "labels": "type:task,comp:infra,phase:0-setup,priority:high",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/terraform/modules/eventbridge/main.tf`.

Resources:
- `aws_cloudwatch_event_rule.daily` - schedule `cron(0 21 * * ? *)`, state ENABLED
- `aws_cloudwatch_event_rule.weekly` - schedule `cron(0 21 ? * SUN *)`, state ENABLED
- `aws_cloudwatch_event_target` for both rules pointing to Lambda ARN
- `aws_lambda_permission` for each rule (principal: events.amazonaws.com)

## Acceptance Criteria

- [ ] Both cron expressions are correct (verified against AWS cron docs)
- [ ] Lambda permission principal is `events.amazonaws.com`
- [ ] `terraform plan` shows 6 resources (2 rules + 2 targets + 2 permissions)""",
    },
    # Story 7 tasks
    "t7_1": {
        "title": "[TASK] Write Terraform CloudWatch module: SNS topic and operational alarms",
        "labels": "type:task,comp:monitoring,phase:0-setup,priority:high",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/terraform/modules/cloudwatch/main.tf`.

Resources:
- `aws_sns_topic.alerts` + `aws_sns_topic_subscription.email`
- EC2 CPUUtilization alarm: > 80%, 2 periods of 5 min -> SNS
- Lambda Errors alarm: >= 1 in any 5-min window -> SNS
- Lambda Duration alarm: > 25000ms (near 30s timeout) -> SNS

Note: billing alarm is in `infra/cloudformation/04-monitoring.yaml` (us-east-1 only).

## Acceptance Criteria

- [ ] All 3 alarms created and targeting the SNS topic
- [ ] `terraform plan` shows 5 resources (1 topic + 1 subscription + 3 alarms)
- [ ] Module output: `sns_topic_arn`""",
    },
    "t7_2": {
        "title": "[TASK] Write Terraform Secrets Manager module: API key placeholders",
        "labels": "type:task,comp:infra,phase:0-setup,priority:high",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/terraform/modules/secrets_manager/main.tf`.

Secrets to create (placeholder values - real values set via AWS CLI separately):
- `/project-intelligent/finnhub/api-key`
- `/project-intelligent/alphavantage/api-key`

Critical: use `lifecycle { ignore_changes = [secret_string] }` so Terraform
never overwrites the real API key once it is set.

## Acceptance Criteria

- [ ] Both secrets created with placeholder REPLACE_ME value
- [ ] `ignore_changes` set on `secret_string` for both secrets
- [ ] `terraform plan` after real key is set shows no changes to the secret value
- [ ] `recovery_window_in_days = 0` for easy dev cleanup""",
    },
    "t7_3": {
        "title": "[TASK] Write Terraform Glue Catalog module: bronze/silver/gold databases",
        "labels": "type:task,comp:infra,phase:0-setup,priority:high",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/terraform/modules/glue_catalog/main.tf`.

Resources:
- `aws_glue_catalog_database.bronze` -> name `project_intelligent_bronze`
- `aws_glue_catalog_database.silver` -> name `project_intelligent_silver`
- `aws_glue_catalog_database.gold`   -> name `project_intelligent_gold`

Note: Glue database names use underscores (hyphens not allowed).

## Acceptance Criteria

- [ ] All 3 databases defined with underscore names
- [ ] `terraform plan` shows 3 database resources
- [ ] Module outputs all 3 database names""",
    },
    "t7_4": {
        "title": "[TASK] Wire all Terraform modules in root main.tf",
        "labels": "type:task,comp:infra,phase:0-setup,priority:critical",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/terraform/main.tf` calling all 8 child modules with correct
inter-module variable passing.

Key wiring:
- EC2 instance_id (from ec2 module) -> lambda_dispatcher and cloudwatch modules
- Lambda function_name (from lambda_dispatcher) -> cloudwatch module
- Lambda function_arn (from lambda_dispatcher) -> eventbridge module
- IAM role ARNs (from iam module) -> ec2 and lambda_dispatcher modules

Use `data.aws_caller_identity.current.account_id` - no hardcoded account IDs.

## Acceptance Criteria

- [ ] All 8 modules called from `main.tf`
- [ ] `terraform validate` passes with no errors
- [ ] `terraform plan` from root shows complete infra plan
- [ ] No hardcoded account IDs or region strings - all from variables/data sources""",
    },
    # Story 8 tasks
    "t8_1": {
        "title": "[TASK] Write CloudFormation billing alarm template (us-east-1)",
        "labels": "type:task,comp:monitoring,phase:0-setup,priority:critical",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/cloudformation/04-monitoring.yaml`.

AWS billing metrics are only available in us-east-1, so this template is
deployed separately from the main Terraform stack.

Resources:
- `AWS::CloudWatch::Alarm` - EstimatedCharges > 0.10 USD, period 86400s, SNS action
- `AWS::SNS::Topic` + `AWS::SNS::Subscription` - email alert

Parameters: `AlertEmail`, `BillingThreshold` (default: 0.10)

## Acceptance Criteria

- [ ] Template deploys to us-east-1 via `aws cloudformation deploy`
- [ ] Alarm threshold correctly set to 0.10 USD
- [ ] Template passes `cfn-lint`
- [ ] Email subscription confirmed after deploy""",
    },
    "t8_2": {
        "title": "[TASK] Write SAM template for Lambda SSM dispatcher + EventBridge",
        "labels": "type:task,comp:infra,phase:0-setup,priority:high",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Create `infra/cloudformation/sam/dispatcher.yaml` as a learning exercise
(alternative to the Terraform lambda_dispatcher + eventbridge modules).

Resources:
- `AWS::Serverless::Function` - Python 3.12, 128 MB, 30s, SSM SendCommand permission
- Daily EventBridge event: `cron(0 21 * * ? *)`
- Weekly EventBridge event: `cron(0 21 ? * SUN *)`

## Acceptance Criteria

- [ ] SAM template builds with `sam build`
- [ ] `sam local invoke` executes with a mock EventBridge event
- [ ] Template passes `cfn-lint`""",
    },
    "t8_3": {
        "title": "[TASK] Add cfn-lint CI step to GitHub Actions",
        "labels": "type:task,comp:infra,phase:0-setup,priority:medium",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Add a GitHub Actions CI job that runs `cfn-lint` on all files under
`infra/cloudformation/` on every PR touching that directory.

Install: `pip install cfn-lint`
Command: `cfn-lint infra/cloudformation/**/*.yaml`

## Acceptance Criteria

- [ ] CI job triggers on changes to `infra/cloudformation/**`
- [ ] All templates pass lint before merge to main""",
    },
    # Story 9 tasks
    "t9_1": {
        "title": "[TASK] Run terraform plan and review full infrastructure plan",
        "labels": "type:task,comp:infra,phase:0-setup,priority:critical",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Run `terraform plan` from `infra/terraform/` and review the complete output
before any `terraform apply`. Verify resource count, names, and configurations
match the architecture documents.

## Acceptance Criteria

- [ ] `terraform plan` exits 0 with no errors
- [ ] Resource count matches expected (S3 5+ resources, DynamoDB 2, IAM 3 roles, etc.)
- [ ] No unintended resource deletions in the plan
- [ ] Plan reviewed and approved before proceeding to apply""",
    },
    "t9_2": {
        "title": "[TASK] Run terraform apply and verify all resources provisioned",
        "labels": "type:task,comp:infra,phase:0-setup,priority:critical",
        "body": """\
## Parent Story
Part of #PARENT

## Description
Execute `terraform apply` and run post-apply smoke tests on every resource.

Smoke test checklist:
- `aws s3 ls` shows all 5 buckets
- `aws dynamodb describe-table` shows ACTIVE for both tables
- `aws ssm start-session --target <instance-id>` opens a shell
- `aws lambda invoke` test call succeeds with no errors
- `aws events list-rules` shows both EventBridge rules as ENABLED
- Terraform state file exists in S3 remote backend

## Acceptance Criteria

- [ ] `terraform apply` exits 0
- [ ] All 6 smoke tests pass
- [ ] Terraform state file confirmed in S3 remote backend""",
    },
}

# ── script structure ─────────────────────────────────────────────────────────

def emit_task(key: str, parent_var: str) -> str:
    t = TASKS[key]
    body_with_parent = t["body"].replace("PARENT", f"$${parent_var}")
    return (
        f"${key} = New-GhIssue `\n"
        f"    -title {ps_str(t['title'])} `\n"
        f"    -labels '{t['labels']}' `\n"
        f"    -body {ps_str(body_with_parent)}\n"
    )


HEADER = """\
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Creates GitHub stories and tasks for IaC (Terraform + CloudFormation)
    under epic #2 [FEATURE-002] Environment Provisioning.
    Generated by gen_iac_script.py - do not edit manually.
#>

$ErrorActionPreference = 'Stop'
$GH        = 'C:\\Program Files\\GitHub CLI\\gh.exe'
$REPO      = 'biteberry/project-intelligent'
$MILESTONE = 'M1: Phase 1.1 - Environment Provisioning'
$ASSIGNEE  = 'sentomani'

function New-GhIssue {
    param([string]$title, [string]$body, [string]$labels)
    $tmp = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($tmp, $body, [System.Text.Encoding]::UTF8)
    $url = & $GH issue create --repo $REPO --title $title --body-file $tmp `
        --label $labels --milestone $MILESTONE --assignee $ASSIGNEE 2>&1
    Remove-Item $tmp -ErrorAction SilentlyContinue
    $num = ($url -split '/')[-1].Trim()
    Write-Host "  Created #$num : $title"
    return $num
}

function Add-SubIssue {
    param([string]$parent, [string]$child)
    $id = (& $GH api /repos/$REPO/issues/$child --jq '.id' 2>&1).Trim()
    $result = & $GH api --method POST /repos/$REPO/issues/$parent/sub_issues `
        --field sub_issue_id=$id 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    Linked #$child -> #$parent"
    } elseif ($result -match 'duplicate|one parent') {
        Write-Host "    #$child already linked (skip)"
    } else {
        Write-Host "    ERROR: $result" -ForegroundColor Red
    }
}

function Update-StoryWithTasks {
    param([string]$story, [string[]]$tasks)
    $jsonOut = & $GH issue view $story --repo $REPO --json body 2>&1
    $currentBody = ($jsonOut | ConvertFrom-Json).body
    $taskLines = ($tasks | ForEach-Object { "- [ ] #$_" }) -join "`n"
    $placeholder = '_To be linked once task issues are created._'
    $newBody = $currentBody.Replace($placeholder, $taskLines)
    $tmp = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($tmp, $newBody, [System.Text.Encoding]::UTF8)
    & $GH issue edit $story --repo $REPO --body-file $tmp 2>&1 | Out-Null
    Remove-Item $tmp -ErrorAction SilentlyContinue
    Write-Host "  Updated story #$story with child task links"
}
"""

FOOTER = """
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All IaC stories and tasks created!" -ForegroundColor Green
Write-Host "  Stories: #$s1 #$s2 #$s3 #$s4 #$s5 #$s6 #$s7 #$s8 #$s9" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
"""


def story_section(num: int, label: str, story_var: str, story_title: str,
                  story_labels: str, story_body: str,
                  task_keys: list[str]) -> str:
    lines = []
    lines.append(f'\nWrite-Host "\\n=== STORY {num}: {label} ===" -ForegroundColor Cyan')
    lines.append(
        f"${story_var} = New-GhIssue `\n"
        f"    -title {ps_str(story_title)} `\n"
        f"    -labels '{story_labels}' `\n"
        f"    -body {ps_str(story_body)}"
    )
    lines.append(f'\nWrite-Host "  Creating tasks..." -ForegroundColor Yellow')
    for tk in task_keys:
        lines.append(emit_task(tk, story_var))
    # Link tasks
    task_arr = "@(" + ", ".join(f"${k}" for k in task_keys) + ")"
    lines.append(f"foreach ($t in {task_arr}) {{ Add-SubIssue -parent ${story_var} -child $t }}")
    lines.append(f"Update-StoryWithTasks -story ${story_var} -tasks {task_arr}")
    return "\n".join(lines)


# ── assemble ─────────────────────────────────────────────────────────────────

sections = [
    story_section(1, "Terraform project setup", "s1",
                  "[STORY] Terraform: project setup, providers, and remote state backend",
                  "type:story,comp:infra,phase:0-setup,priority:critical",
                  S1_BODY, ["t1_1", "t1_2", "t1_3"]),
    story_section(2, "Terraform IAM module", "s2",
                  "[STORY] Terraform module: IAM roles and policies",
                  "type:story,comp:infra,phase:0-setup,priority:critical",
                  S2_BODY, ["t2_1", "t2_2", "t2_3"]),
    story_section(3, "Terraform S3 module", "s3",
                  "[STORY] Terraform module: S3 buckets (medallion layers)",
                  "type:story,comp:infra,phase:0-setup,priority:critical",
                  S3_BODY, ["t3_1", "t3_2"]),
    story_section(4, "Terraform DynamoDB module", "s4",
                  "[STORY] Terraform module: DynamoDB tables (predictions + audit)",
                  "type:story,comp:data-store,phase:0-setup,priority:high",
                  S4_BODY, ["t4_1"]),
    story_section(5, "Terraform EC2 module", "s5",
                  "[STORY] Terraform module: EC2 t2.micro with SSM-only access",
                  "type:story,comp:infra,phase:0-setup,priority:critical",
                  S5_BODY, ["t5_1"]),
    story_section(6, "Terraform Lambda + EventBridge", "s6",
                  "[STORY] Terraform modules: Lambda SSM dispatcher and EventBridge rules",
                  "type:story,comp:infra,phase:0-setup,priority:high",
                  S6_BODY, ["t6_1", "t6_2"]),
    story_section(7, "Terraform monitoring + secrets + Glue + root wiring", "s7",
                  "[STORY] Terraform modules: CloudWatch, Secrets Manager, Glue, root wiring",
                  "type:story,comp:infra,phase:0-setup,priority:high",
                  S7_BODY, ["t7_1", "t7_2", "t7_3", "t7_4"]),
    story_section(8, "CloudFormation templates", "s8",
                  "[STORY] CloudFormation templates: billing alarm and SAM dispatcher",
                  "type:story,comp:infra,phase:0-setup,priority:high",
                  S8_BODY, ["t8_1", "t8_2", "t8_3"]),
    story_section(9, "terraform apply", "s9",
                  "[STORY] Run terraform apply to provision the full AWS environment",
                  "type:story,comp:infra,phase:0-setup,priority:critical",
                  S9_BODY, ["t9_1", "t9_2"]),
]

script = HEADER + "\n".join(sections) + FOOTER

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(script)

print(f"Written {len(script)} chars to {OUT}")
