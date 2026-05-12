# Story #48 — Lambda SSM Dispatcher: Full Retrospective
## What We Did, Challenges Faced, and How We Fixed Them

**Date:** 2026-05-13  
**Branch:** `feature/issue-48-lambda-ssm-dispatcher`  
**Issues closed:** #48, #72, #73, #74

---

## Overview

Story #48 required implementing a Lambda function that:
- Receives an **EventBridge** trigger (daily or weekly schedule)
- Parses the trigger type from the event
- Issues an **SSM RunCommand** to the EC2 instance to start the pipeline
- Logs the command ID to CloudWatch

This is the bridge between the EventBridge scheduler and the EC2 compute layer.

**Architecture:**
```
EventBridge (schedule) → Lambda (project-intelligent-ssm-dispatcher) → SSM RunCommand → EC2 (project-intelligent-ec2)
```

---

## Child Tasks

| Issue | Title | Status |
|---|---|---|
| #72 | Write Lambda SSM dispatcher function code | ✅ Done |
| #73 | Deploy Lambda SSM dispatcher to AWS | ✅ Done |
| #74 | End-to-end smoke test: EventBridge → Lambda → SSM → EC2 | ✅ Done |

---

## PHASE 1 — Sync Branch with Main

Before starting, the branch `feature/issue-48-lambda-ssm-dispatcher` was old and behind `main`.  
We merged the latest main (which included the EC2 setup from Story #53):

```powershell
git fetch origin
git merge origin/main --no-edit
```

**Result:** 9 files merged in from main (EC2 docs, requirements.txt, infra files) ✅

---

## PHASE 2 — Review Existing handler.py (#72)

`handler.py` already existed at `src/lambda/ssm_dispatcher/handler.py` with solid implementation:

**Logic:**
1. Parse `detail-type` from EventBridge event → detect `daily` / `weekly` / `unknown`
2. Read `EC2_INSTANCE_ID` and `SSM_DOCUMENT_NAME` from environment variables
3. Call `ssm.send_command()` with parameters
4. Return `statusCode: 200` with command ID on success
5. Raise exception on missing env vars or SSM failure

---

## PHASE 3 — Unit Tests (#72)

The existing test file at `tests/lambda/test_ssm_dispatcher.py` had only **2 basic tests**.  
We rewrote it with **12 comprehensive tests** covering all scenarios:

### Test Coverage

| Category | Tests |
|---|---|
| Happy path | Daily event → 200 + command ID |
| Happy path | Weekly event → 200 + command ID |
| Happy path | SSM called exactly once |
| Happy path | Correct instance ID passed to SSM |
| Happy path | Correct document name passed to SSM |
| Event parsing | `daily` in detail-type → `eventType=daily` |
| Event parsing | `weekly` in detail-type → `eventType=weekly` |
| Event parsing | No detail-type → `eventType=unknown` |
| Error handling | Missing `EC2_INSTANCE_ID` → raises, SSM not called |
| Error handling | Missing `SSM_DOCUMENT_NAME` → raises, SSM not called |
| Error handling | Both env vars missing → raises |
| Error handling | SSM throws → exception propagates |

**Run command:**
```powershell
.venv\Scripts\python.exe -m pytest tests/lambda/test_ssm_dispatcher.py -v
```

**Result:** 12/12 passed ✅

---

## PHASE 4 — Deploy Lambda (#73)

### Pre-deployment checks

**Lambda role already existed:** `project-intelligent-lambda-role`  
But it only had `AWSLambdaBasicExecutionRole` — missing SSM permission.

```powershell
aws iam attach-role-policy `
  --role-name project-intelligent-lambda-role `
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMFullAccess
```

**Final policies on Lambda role:**
| Policy | Purpose |
|---|---|
| `AWSLambdaBasicExecutionRole` | Write logs to CloudWatch |
| `AmazonSSMFullAccess` | Call `ssm:SendCommand` on EC2 |

### Package and deploy

```powershell
# Package
Compress-Archive -Path handler.py -DestinationPath ssm_dispatcher.zip -Force

# Deploy
aws lambda create-function `
  --function-name project-intelligent-ssm-dispatcher `
  --runtime python3.12 `
  --role arn:aws:iam::307828758318:role/project-intelligent-lambda-role `
  --handler handler.lambda_handler `
  --zip-file fileb://ssm_dispatcher.zip `
  --timeout 30 `
  --memory-size 128 `
  --environment "Variables={EC2_INSTANCE_ID=i-004ede57a842280fe,SSM_DOCUMENT_NAME=project-intelligent-pipeline}" `
  --region ap-south-1
```

**Deployed Lambda:**
| Property | Value |
|---|---|
| Function name | `project-intelligent-ssm-dispatcher` |
| ARN | `arn:aws:lambda:ap-south-1:307828758318:function:project-intelligent-ssm-dispatcher` |
| Runtime | Python 3.12 |
| Memory | 128 MB |
| Timeout | 30s |
| EC2_INSTANCE_ID | `i-004ede57a842280fe` |
| SSM_DOCUMENT_NAME | `project-intelligent-pipeline` |

---

## PHASE 5 — Challenges Faced

---

### Challenge #1 — PowerShell breaks JSON payload in Lambda invoke

**Problem:**
```powershell
aws lambda invoke --payload '{"detail-type": "Scheduled Event - Daily"}' ...
# ERROR: Unknown options: Daily}, response.json, -
```

PowerShell interprets curly braces and quotes in the payload and breaks the command.

**Fix:** Save payload to a file and use `fileb://`:
```powershell
Set-Content -Path "payload.json" -Value '{"detail-type": "Scheduled Event - Daily"}'
aws lambda invoke --payload fileb://payload.json ...
```

---

### Challenge #2 — SSM document parameter name `event_type` rejected

**Problem:**
```
aws: [ERROR]: InvalidDocumentContent: Parameter name "event_type" is not alpha-numeric.
```

SSM document parameter names must be **strictly alphanumeric** — underscores are not allowed.

**Fix:** Renamed parameter from `event_type` → `eventType` in:
1. `handler.py` — `command_parameters = {'eventType': [event_type]}`
2. `ssm-document.json` — parameter name and `{{ eventType }}` placeholder
3. `tests/lambda/test_ssm_dispatcher.py` — all 3 assertion checks

---

### Challenge #3 — First Lambda invoke got `InvalidDocument` error

**Problem:** Lambda executed successfully but returned:
```json
{"errorMessage": "An error occurred (InvalidDocument) when calling the SendCommand operation"}
```

**Root cause:** The SSM document `project-intelligent-pipeline` did not exist yet — it had not been created before the first invoke.

**Fix:** Created the SSM document first, then re-deployed Lambda with the fixed parameter name:
```powershell
aws ssm create-document `
  --name "project-intelligent-pipeline" `
  --document-type "Command" `
  --content file://ssm-document.json `
  --region ap-south-1
```

---

## PHASE 6 — SSM Document

Created `project-intelligent-pipeline` SSM Command document:

```json
{
  "schemaVersion": "2.2",
  "description": "Run Project Intelligent pipeline on EC2",
  "parameters": {
    "eventType": {
      "type": "String",
      "description": "Trigger type: daily or weekly",
      "default": "daily"
    }
  },
  "mainSteps": [
    {
      "action": "aws:runShellScript",
      "name": "RunPipeline",
      "inputs": {
        "runCommand": [
          "echo \"Pipeline triggered: eventType={{ eventType }}\"",
          "echo \"Timestamp: $(date)\"",
          "echo \"Instance: $(curl -s ... /latest/meta-data/instance-id)\""
        ]
      }
    }
  ]
}
```

---

## PHASE 7 — End-to-End Smoke Test (#74)

### Test flow

**Step 1 — Invoke Lambda manually (simulating EventBridge daily trigger):**
```powershell
aws lambda invoke `
  --function-name project-intelligent-ssm-dispatcher `
  --payload fileb://payload.json `
  --region ap-south-1 `
  response.json

Get-Content response.json
# {"statusCode": 200, "body": "SSM command sent. Command ID: f5ca0a68-79c9-49b8-89e6-fd1017bc787d"}
```

**Step 2 — Verify SSM command ran on EC2:**
```powershell
aws ssm get-command-invocation `
  --command-id f5ca0a68-79c9-49b8-89e6-fd1017bc787d `
  --instance-id i-004ede57a842280fe `
  --region ap-south-1 `
  --query "{Status:Status,Output:StandardOutputContent}"
```

**Actual output:**
```
Status: Success
Output: Pipeline triggered: eventType=daily
        Timestamp: Tue May 12 20:11:15 UTC 2026
        Instance: i-004ede57a842280fe
```

### Smoke test results

| Check | Result |
|---|---|
| Lambda invoked | ✅ StatusCode 200 |
| SSM command dispatched | ✅ Command ID returned |
| EC2 received command | ✅ Status: Success |
| Correct event type passed | ✅ `eventType=daily` |
| No IAM permission errors | ✅ Clean execution |

---

## Final State

| Resource | Value |
|---|---|
| Lambda function | `project-intelligent-ssm-dispatcher` |
| Lambda ARN | `arn:aws:lambda:ap-south-1:307828758318:function:project-intelligent-ssm-dispatcher` |
| Lambda role | `project-intelligent-lambda-role` |
| Lambda policies | `AWSLambdaBasicExecutionRole` + `AmazonSSMFullAccess` |
| SSM document | `project-intelligent-pipeline` |
| EC2 target | `i-004ede57a842280fe` |
| SSM command ID (smoke test) | `f5ca0a68-79c9-49b8-89e6-fd1017bc787d` |
| Unit tests | 12/12 passing |

---

## Summary of All Challenges and Fixes

| # | Challenge | Root Cause | Fix |
|---|---|---|---|
| 1 | PowerShell breaks JSON payload | PowerShell interprets `{`, `}`, `"` in inline strings | Save payload to file, use `fileb://payload.json` |
| 2 | SSM document rejected `event_type` param | SSM requires strictly alphanumeric parameter names (no underscores) | Renamed to `eventType` in handler, document, and tests |
| 3 | `InvalidDocument` error on first invoke | SSM document not created before Lambda deploy | Create SSM document first, then redeploy Lambda |
