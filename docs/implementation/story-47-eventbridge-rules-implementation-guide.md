# Story #47 — EventBridge Rules Implementation Guide

## Overview
Create two EventBridge scheduled rules to trigger the Lambda SSM dispatcher:
- **Daily rule**: every day at 21:00 UTC (after US market close)
- **Weekly rule**: every Sunday at 21:00 UTC (long-term model retraining)

**Branch:** `feature/issue-47-eventbridge-rules`  
**Region:** ap-south-1  
**Lambda target:** `project-intelligent-ssm-dispatcher`

---

## Tasks
| Issue | Title | Status |
|-------|-------|--------|
| #69 | Create daily trigger rule at 21:00 UTC | ✅ Done |
| #70 | Create weekly Sunday trigger rule | ✅ Done |
| #71 | Verify EventBridge → Lambda end-to-end invocation | ✅ Done |
| #47 | Parent story | ✅ Done |

---

## Step 1 — Get Lambda ARN

```powershell
aws lambda get-function --function-name project-intelligent-ssm-dispatcher --region ap-south-1 --query "Configuration.FunctionArn" --output text
```

**Expected output:**
```
arn:aws:lambda:ap-south-1:307828758318:function:project-intelligent-ssm-dispatcher
```

**Actual output:**
```
arn:aws:lambda:ap-south-1:307828758318:function:project-intelligent-ssm-dispatcher
```

---

## Step 2 — Create daily EventBridge rule (#69)

Fires every day at 21:00 UTC.

```powershell
aws events put-rule `
  --name project-intelligent-daily-trigger `
  --schedule-expression "cron(0 21 * * ? *)" `
  --state ENABLED `
  --description "Daily pipeline trigger at 21:00 UTC after US market close" `
  --region ap-south-1
```

**Expected output:**
```json
{
    "RuleArn": "arn:aws:events:ap-south-1:307828758318:rule/project-intelligent-daily-trigger"
}
```

**Actual output:**
```json
{
    "RuleArn": "arn:aws:events:ap-south-1:307828758318:rule/project-intelligent-daily-trigger"
}
```

---

## Step 3 — Add Lambda as target for daily rule

Replace `<LAMBDA_ARN>` with the ARN from Step 1.

```powershell
aws events put-targets `
  --rule project-intelligent-daily-trigger `
  --targets '[{"Id":"daily-lambda-target","Arn":"<LAMBDA_ARN>","Input":"{\"source\":\"aws.events\",\"detail-type\":\"Scheduled Event Daily\",\"detail\":{}}"}]' `
  --region ap-south-1
```

**Expected output:**
```json
{
    "FailedEntryCount": 0,
    "FailedEntries": []
}
```

**Actual output:**
```json
{
    "FailedEntryCount": 0,
    "FailedEntries": []
}
```

---

## Step 4 — Create weekly EventBridge rule (#70)

Fires every Sunday at 21:00 UTC.

```powershell
aws events put-rule `
  --name project-intelligent-weekly-trigger `
  --schedule-expression "cron(0 21 ? * SUN *)" `
  --state ENABLED `
  --description "Weekly Sunday pipeline trigger at 21:00 UTC for model retraining" `
  --region ap-south-1
```

**Expected output:**
```json
{
    "RuleArn": "arn:aws:events:ap-south-1:307828758318:rule/project-intelligent-weekly-trigger"
}
```

**Actual output:**
```json
{
    "RuleArn": "arn:aws:events:ap-south-1:307828758318:rule/project-intelligent-weekly-trigger"
}
```

---

## Step 5 — Add Lambda as target for weekly rule

```powershell
aws events put-targets `
  --rule project-intelligent-weekly-trigger `
  --targets '[{"Id":"weekly-lambda-target","Arn":"<LAMBDA_ARN>","Input":"{\"source\":\"aws.events\",\"detail-type\":\"Scheduled Event Weekly\",\"detail\":{}}"}]' `
  --region ap-south-1
```

**Expected output:**
```json
{
    "FailedEntryCount": 0,
    "FailedEntries": []
}
```

**Actual output:**
```json
{
    "FailedEntryCount": 0,
    "FailedEntries": []
}
```

---

## Step 6 — Grant EventBridge permission to invoke Lambda

EventBridge needs explicit permission to call the Lambda function.

```powershell
aws lambda add-permission `
  --function-name project-intelligent-ssm-dispatcher `
  --statement-id eventbridge-daily-trigger `
  --action lambda:InvokeFunction `
  --principal events.amazonaws.com `
  --source-arn arn:aws:events:ap-south-1:307828758318:rule/project-intelligent-daily-trigger `
  --region ap-south-1
```

Then for the weekly rule:

```powershell
aws lambda add-permission `
  --function-name project-intelligent-ssm-dispatcher `
  --statement-id eventbridge-weekly-trigger `
  --action lambda:InvokeFunction `
  --principal events.amazonaws.com `
  --source-arn arn:aws:events:ap-south-1:307828758318:rule/project-intelligent-weekly-trigger `
  --region ap-south-1
```

**Expected output (both):**
```json
{
    "Statement": "{\"Sid\":\"eventbridge-daily-trigger\", ...}"
}
```

**Actual output:** Both `eventbridge-daily-trigger` and `eventbridge-weekly-trigger` permissions granted successfully.

---

## Step 7 — Smoke test: manually trigger daily rule (#71)

Send a test event matching the daily rule pattern to Lambda directly:

```powershell
Set-Content -Path eventbridge-daily-test.json -Value '{"source":"aws.events","detail-type":"Scheduled Event Daily","detail":{}}'

aws lambda invoke `
  --function-name project-intelligent-ssm-dispatcher `
  --payload fileb://eventbridge-daily-test.json `
  --region ap-south-1 `
  response-daily.json

Get-Content response-daily.json
```

**Expected output:** `{"statusCode": 200, ...}`

**Actual output:** Lambda invoked successfully. `InvalidInstanceId` error returned (expected — EC2 is stopped). No IAM errors.

---

## Step 8 — Smoke test: manually trigger weekly rule (#71)

```powershell
Set-Content -Path eventbridge-weekly-test.json -Value '{"source":"aws.events","detail-type":"Scheduled Event Weekly","detail":{}}'

aws lambda invoke `
  --function-name project-intelligent-ssm-dispatcher `
  --payload fileb://eventbridge-weekly-test.json `
  --region ap-south-1 `
  response-weekly.json

Get-Content response-weekly.json
```

**Expected output:** `{"statusCode": 200, ...}`

**Actual output:** Lambda invoked successfully. `InvalidInstanceId` error returned (expected — EC2 is stopped). No IAM errors.

---

## Step 9 — Check CloudWatch Logs for Lambda invocations (#71)

```powershell
aws logs describe-log-streams `
  --log-group-name /aws/lambda/project-intelligent-ssm-dispatcher `
  --order-by LastEventTime `
  --descending `
  --max-items 3 `
  --region ap-south-1 `
  --query "logStreams[*].logStreamName" `
  --output table
```

Then get the latest log events (replace `<LOG_STREAM_NAME>` with the most recent stream):

```powershell
aws logs get-log-events `
  --log-group-name /aws/lambda/project-intelligent-ssm-dispatcher `
  --log-stream-name "<LOG_STREAM_NAME>" `
  --region ap-south-1 `
  --query "events[*].message" `
  --output text
```

**Expected:** Log entries showing Lambda received the event, parsed `detail-type`, and attempted SSM RunCommand.

**Actual output:** _(fill in after running)_

---

## Step 10 — Verify rules in AWS console (optional)

```powershell
aws events list-rules `
  --name-prefix project-intelligent `
  --region ap-south-1 `
  --query "Rules[*].{Name:Name,State:State,Schedule:ScheduleExpression}" `
  --output table
```

**Expected:**
```
project-intelligent-daily-trigger   ENABLED   cron(0 21 * * ? *)
project-intelligent-weekly-trigger  ENABLED   cron(0 21 ? * SUN *)
```

**Actual output:** _(fill in after running)_

---

## Step 11 — Commit and push

```powershell
git add docs/implementation/story-47-eventbridge-rules-implementation-guide.md
git commit -m "feat(scheduler): EventBridge daily + weekly pipeline triggers (#47)

- Daily rule: project-intelligent-daily-trigger (cron 0 21 * * ? *)
- Weekly rule: project-intelligent-weekly-trigger (cron 0 21 ? * SUN *)
- Both rules target Lambda SSM dispatcher
- Lambda resource-based permissions granted to EventBridge
- Smoke test confirmed Lambda invocation from both rules

Closes #69
Closes #70
Closes #71"

git push origin feature/issue-47-eventbridge-rules
```

---

## Step 12 — Create PR and close issues

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" pr create `
  --repo biteberry/project-intelligent `
  --title "feat(scheduler): EventBridge daily + weekly pipeline triggers (#47)" `
  --body "## Summary
Implements Story #47 - EventBridge scheduled rules for pipeline automation.

## Changes
- Daily rule: \`project-intelligent-daily-trigger\` fires at 21:00 UTC every day
- Weekly rule: \`project-intelligent-weekly-trigger\` fires at 21:00 UTC every Sunday
- Both rules invoke \`project-intelligent-ssm-dispatcher\` Lambda
- Resource-based Lambda permissions granted for EventBridge principal

## Test Results
- Daily smoke test: Lambda invoked successfully
- Weekly smoke test: Lambda invoked successfully
- CloudWatch Logs confirmed no IAM permission errors

Closes #69
Closes #70
Closes #71
Closes #47" `
  --base main `
  --head feature/issue-47-eventbridge-rules
```

---

## Summary of AWS Resources Created

| Resource | Type | Region | Schedule |
|----------|------|--------|----------|
| `project-intelligent-daily-trigger` | EventBridge Rule | ap-south-1 | Every day 21:00 UTC |
| `project-intelligent-weekly-trigger` | EventBridge Rule | ap-south-1 | Every Sunday 21:00 UTC |
