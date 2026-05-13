# Story #49 — CloudWatch Alarms and SNS Email Alerts
## Implementation Guide (Step-by-Step)

**Branch:** `feature/issue-49-cloudwatch-sns`  
**Parent Feature:** [#2] Environment Provisioning  
**Region:** `ap-south-1` (Mumbai) — except billing alarm which must be `us-east-1`

---

## Current State (as of 2026-05-13)

| # | Task | Status | Notes |
|---|---|---|---|
| #75 | Create SNS topic + subscribe alert email | ✅ Done | `arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts` + `us-east-1` |
| #76 | Create CloudWatch billing alarm at USD 0.10 | ✅ Done | `project-intelligent-billing-010` in us-east-1, INSUFFICIENT_DATA |
| #77 | Create CloudWatch alarms for EC2 + Lambda health | ✅ Done | 3 alarms in ap-south-1, all INSUFFICIENT_DATA |

---

## Architecture

```
CloudWatch Billing Alarm (us-east-1)  ─┐
CloudWatch EC2 CPU Alarm (ap-south-1) ─┤──► SNS Topic: project-intelligent-alerts ──► Gmail
CloudWatch Lambda Errors Alarm        ─┤
CloudWatch Lambda Duration Alarm      ─┘
```

---

## Pre-flight Checklist

```powershell
# Confirm AWS identity
aws sts get-caller-identity --output table

# Confirm region
aws configure get region
```

---

## STEP 1 — Create SNS Topic (#75)

SNS is the notification hub. All CloudWatch alarms send to this topic, which delivers to your email.

```powershell
aws sns create-topic `
  --name project-intelligent-alerts `
  --region ap-south-1
```

**Expected output:**
```json
{
    "TopicArn": "arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts"
}
```

Save the TopicArn:
```powershell
$snsTopicArn = "arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts"

# Save to file
New-Item -ItemType Directory -Force -Path "infra\monitoring" | Out-Null
Set-Content -Path "infra\monitoring\sns-topic-arn.env" -Value "SNS_TOPIC_ARN=$snsTopicArn"
```

**Actual values (2026-05-13):**
- SNS Topic ARN (ap-south-1): `arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts`
- SNS Topic ARN (us-east-1): `arn:aws:sns:us-east-1:307828758318:project-intelligent-alerts`

---

## STEP 2 — Subscribe Email to SNS Topic (#75)

```powershell
aws sns subscribe `
  --topic-arn arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts `
  --protocol email `
  --notification-endpoint manivannan.marimuthu@gmail.com `
  --region ap-south-1
```

**Expected output:**
```json
{
    "SubscriptionArn": "pending confirmation"
}
```

> ⚠️ **IMPORTANT:** Check your Gmail inbox for an email from **AWS Notifications**.  
> Subject: `AWS Notification - Subscription Confirmation`  
> Click **"Confirm subscription"** — alarms will NOT deliver email until confirmed.

Verify subscription status:
```powershell
aws sns list-subscriptions-by-topic `
  --topic-arn arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts `
  --region ap-south-1
```

Look for `"SubscriptionArn"` — it changes from `"pending confirmation"` to a real ARN after you click the link.

> ✅ **#75 done when:** Subscription shows confirmed ARN (not `pending confirmation`).

---

## STEP 3 — Create Billing Alarm at USD 0.10 (#76)

> ⚠️ **Billing metrics are only available in `us-east-1`** (AWS global requirement).  
> This alarm must be created in `us-east-1` even though everything else is in `ap-south-1`.

> ⚠️ **Prerequisite:** Billing alerts must be enabled in your AWS account.  
> Go to: **AWS Console → Billing → Billing Preferences → Enable CloudWatch billing alerts**  
> (One-time setup — only needed once per account)

```powershell
aws cloudwatch put-metric-alarm `
  --alarm-name "project-intelligent-billing-010" `
  --alarm-description "Alert when AWS charges exceed USD 0.10" `
  --metric-name EstimatedCharges `
  --namespace AWS/Billing `
  --statistic Maximum `
  --period 86400 `
  --threshold 0.10 `
  --comparison-operator GreaterThanOrEqualToThreshold `
  --evaluation-periods 1 `
  --alarm-actions arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts `
  --ok-actions arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts `
  --dimensions Name=Currency,Value=USD `
  --treat-missing-data notBreaching `
  --region us-east-1
```

Verify alarm created:
```powershell
aws cloudwatch describe-alarms `
  --alarm-names "project-intelligent-billing-010" `
  --query "MetricAlarms[0].{Name:AlarmName,State:StateValue,Threshold:Threshold}" `
  --output table `
  --region us-east-1
```

Test by manually setting alarm to ALARM state (optional):
```powershell
aws cloudwatch set-alarm-state `
  --alarm-name "project-intelligent-billing-010" `
  --state-value ALARM `
  --state-reason "Manual test" `
  --region us-east-1

# Check email inbox for alert
# Then reset back to OK
aws cloudwatch set-alarm-state `
  --alarm-name "project-intelligent-billing-010" `
  --state-value OK `
  --state-reason "Manual test reset" `
  --region us-east-1
```

**Actual values (2026-05-13):**
- Alarm name: `project-intelligent-billing-010`
- Threshold: `$0.10 USD`
- Period: `86400s` (24 hours)
- Region: `us-east-1`

> ✅ **#76 done when:** Alarm exists in `us-east-1` and test email received.

---

## STEP 4 — Create EC2 CPU Alarm (#77)

Fires when EC2 CPU exceeds 80% for 2 consecutive 5-minute periods (10 minutes sustained high CPU).

```powershell
aws cloudwatch put-metric-alarm `
  --alarm-name "project-intelligent-ec2-cpu-high" `
  --alarm-description "EC2 CPU utilization above 80% for 10 minutes" `
  --metric-name CPUUtilization `
  --namespace AWS/EC2 `
  --statistic Average `
  --period 300 `
  --threshold 80 `
  --comparison-operator GreaterThanOrEqualToThreshold `
  --evaluation-periods 2 `
  --alarm-actions arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts `
  --ok-actions arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts `
  --dimensions Name=InstanceId,Value=i-004ede57a842280fe `
  --treat-missing-data notBreaching `
  --region ap-south-1
```

**Actual values (2026-05-13):**
- Alarm name: `project-intelligent-ec2-cpu-high`
- Instance: `i-004ede57a842280fe`
- Threshold: `80% CPU`
- Evaluation: `2 × 5 min = 10 minutes`

---

## STEP 5 — Create Lambda Errors Alarm (#77)

Fires when Lambda throws 1 or more errors in any 5-minute window.

```powershell
aws cloudwatch put-metric-alarm `
  --alarm-name "project-intelligent-lambda-errors" `
  --alarm-description "Lambda SSM dispatcher has errors" `
  --metric-name Errors `
  --namespace AWS/Lambda `
  --statistic Sum `
  --period 300 `
  --threshold 1 `
  --comparison-operator GreaterThanOrEqualToThreshold `
  --evaluation-periods 1 `
  --alarm-actions arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts `
  --ok-actions arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts `
  --dimensions Name=FunctionName,Value=project-intelligent-ssm-dispatcher `
  --treat-missing-data notBreaching `
  --region ap-south-1
```

---

## STEP 6 — Create Lambda Duration Alarm (#77)

Fires when Lambda execution time exceeds 25 seconds (near the 30s timeout).

```powershell
aws cloudwatch put-metric-alarm `
  --alarm-name "project-intelligent-lambda-duration" `
  --alarm-description "Lambda SSM dispatcher approaching 30s timeout" `
  --metric-name Duration `
  --namespace AWS/Lambda `
  --statistic Maximum `
  --period 300 `
  --threshold 25000 `
  --comparison-operator GreaterThanOrEqualToThreshold `
  --evaluation-periods 1 `
  --alarm-actions arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts `
  --ok-actions arn:aws:sns:ap-south-1:307828758318:project-intelligent-alerts `
  --dimensions Name=FunctionName,Value=project-intelligent-ssm-dispatcher `
  --treat-missing-data notBreaching `
  --region ap-south-1
```

---

## STEP 7 — Verify All Alarms (#77)

```powershell
# Check all alarms in ap-south-1
aws cloudwatch describe-alarms `
  --alarm-name-prefix "project-intelligent" `
  --query "MetricAlarms[*].{Name:AlarmName,State:StateValue,Metric:MetricName}" `
  --output table `
  --region ap-south-1

# Check billing alarm in us-east-1
aws cloudwatch describe-alarms `
  --alarm-name-prefix "project-intelligent" `
  --query "MetricAlarms[*].{Name:AlarmName,State:StateValue,Metric:MetricName}" `
  --output table `
  --region us-east-1
```

**Expected — all alarms in `OK` or `INSUFFICIENT_DATA` state:**
```
-------------------------------------------------------------------
| Name                                  | State            | Metric         |
|---------------------------------------|------------------|----------------|
| project-intelligent-ec2-cpu-high      | OK               | CPUUtilization |
| project-intelligent-lambda-errors     | OK               | Errors         |
| project-intelligent-lambda-duration   | OK               | Duration       |
-------------------------------------------------------------------
```

> ✅ **#77 done when:** All 3 alarms exist and linked to SNS topic.

---

## STEP 8 — Commit and Push

```powershell
cd C:\Manivannan\Workspace\ANTIGRAVITY\STOCKS\PROJECT_INTELLIGENT

git add infra/monitoring/sns-topic-arn.env
git add docs/implementation/story-49-cloudwatch-sns-implementation-guide.md

git commit -m "feat(monitoring): CloudWatch alarms + SNS email alerts (#49)

- SNS topic project-intelligent-alerts created
- Email subscription: manivannan.marimuthu@gmail.com
- Billing alarm: project-intelligent-billing-010 ($0.10, us-east-1)
- EC2 CPU alarm: > 80% for 10 min
- Lambda errors alarm: >= 1 error per 5 min
- Lambda duration alarm: > 25000ms

Closes #75
Closes #76
Closes #77"

git push origin feature/issue-49-cloudwatch-sns
```

---

## Summary of All Alarms

| Alarm Name | Metric | Threshold | Region |
|---|---|---|---|
| `project-intelligent-billing-010` | EstimatedCharges | >= $0.10 USD | `us-east-1` |
| `project-intelligent-ec2-cpu-high` | CPUUtilization | >= 80% (10 min) | `ap-south-1` |
| `project-intelligent-lambda-errors` | Errors | >= 1 (5 min) | `ap-south-1` |
| `project-intelligent-lambda-duration` | Duration | >= 25000ms | `ap-south-1` |

All alarms → SNS topic `project-intelligent-alerts` → `manivannan.marimuthu@gmail.com`
