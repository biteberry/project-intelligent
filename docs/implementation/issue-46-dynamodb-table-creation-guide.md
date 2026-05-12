# Issue #46 — DynamoDB Table Creation Guide (predictions + audit)

**Repo:** biteberry/project-intelligent  
**Issue:** [#46](https://github.com/biteberry/project-intelligent/issues/46)  
**Milestone:** M1: Phase 1.1 — Environment Provisioning  
**Priority:** High  

---

## What You Will Learn
- How to create DynamoDB tables using AWS CLI
- How to configure on-demand (PAY_PER_REQUEST) billing
- How to enable TTL for automatic expiry
- How to verify table creation and status
- How to update IAM policies for DynamoDB access

---

## Prerequisites
- AWS CLI installed and configured
- IAM user/role with `dynamodb:*` permissions for table creation
- Table schemas documented in [docs/schemas/dynamodb_predictions.md](../schemas/dynamodb_predictions.md) and [docs/schemas/dynamodb_audit.md](../schemas/dynamodb_audit.md)

---

## Step 1 — Set Variables

```powershell
$region = "ap-south-1"
$predictionsTable = "project-intelligent-predictions"
$auditTable = "project-intelligent-audit"
```

---

## Step 2 — Create the Predictions Table

```powershell
aws dynamodb create-table `
  --table-name $predictionsTable `
  --attribute-definitions AttributeName=symbol#date,AttributeType=S AttributeName=horizon#model_version,AttributeType=S `
  --key-schema AttributeName=symbol#date,KeyType=HASH AttributeName=horizon#model_version,KeyType=RANGE `
  --billing-mode PAY_PER_REQUEST `
  --region $region
```

- **PK:** symbol#date (String)
- **SK:** horizon#model_version (String)
- **Billing:** PAY_PER_REQUEST (on-demand, Free Tier eligible)

---

## Step 3 — Enable TTL on Predictions Table

TTL (Time To Live) automatically deletes items after a set time. We'll use the `ttl` attribute (Unix epoch seconds, 90 days from insert).

```powershell
aws dynamodb update-time-to-live `
  --table-name $predictionsTable `
  --time-to-live-specification "Enabled=true,AttributeName=ttl" `
  --region $region
```

---

## Step 4 — Create the Audit Table

```powershell
aws dynamodb create-table `
  --table-name $auditTable `
  --attribute-definitions AttributeName=job_date,AttributeType=S AttributeName=job_id,AttributeType=S `
  --key-schema AttributeName=job_date,KeyType=HASH AttributeName=job_id,KeyType=RANGE `
  --billing-mode PAY_PER_REQUEST `
  --region $region
```

- **PK:** job_date (String)
- **SK:** job_id (String)
- **Billing:** PAY_PER_REQUEST

---

## Step 5 — Verify Table Creation

Check table status:

```powershell
aws dynamodb describe-table --table-name $predictionsTable --region $region
aws dynamodb describe-table --table-name $auditTable --region $region
```

Status should be `ACTIVE` for both tables.

---

## Step 6 — Update IAM Policy for EC2/Lambda

Add these actions to your EC2/Lambda role policy for both tables:

```json
{
    "Effect": "Allow",
    "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query"
    ],
    "Resource": [
        "arn:aws:dynamodb:ap-south-1:<account-id>:table/project-intelligent-predictions",
        "arn:aws:dynamodb:ap-south-1:<account-id>:table/project-intelligent-audit"
    ]
}
```

- Replace `<account-id>` with your AWS account number (e.g., 307828758318)
- Add this statement to `infra/iam/ec2-instance-policy.json`

---

## Step 7 — Test Table Access (Optional)

Insert a test item:

```powershell
aws dynamodb put-item `
  --table-name $predictionsTable `
  --item '{"symbol#date": {"S": "RELIANCE#2026-05-07"}, "horizon#model_version": {"S": "swing#v1.2"}, "predicted_direction": {"S": "UP"}, "confidence_score": {"N": "0.87"}, "features_hash": {"S": "9f8a7c..."}, "ttl": {"N": "1788888888"}}' `
  --region $region
```

Query the item:

```powershell
aws dynamodb get-item `
  --table-name $predictionsTable `
  --key '{"symbol#date": {"S": "RELIANCE#2026-05-07"}, "horizon#model_version": {"S": "swing#v1.2"}}' `
  --region $region
```

---

## Step 8 — Commit and Push

```powershell
cd C:\Manivannan\Workspace\ANTIGRAVITY\STOCKS\PROJECT_INTELLIGENT

git add docs/implementation/issue-46-dynamodb-table-creation-guide.md

git commit -m "docs(dynamodb): add table creation guide for predictions and audit (#46)"
git push
```

---

## Checklist — Acceptance Criteria

- [ ] predictions table created (PK: symbol#date, SK: horizon#model_version)
- [ ] audit table created (PK: job_date, SK: job_id)
- [ ] Both tables use on-demand (PAY_PER_REQUEST) billing
- [ ] TTL attribute configured on predictions table (90-day retention)
- [ ] IAM role has dynamodb:GetItem, dynamodb:PutItem, dynamodb:Query on both tables
- [ ] Table schemas documented in docs/schemas/

---

## Key Concepts Recap
| Term | Meaning |
|---|---|
| PAY_PER_REQUEST | On-demand billing, no capacity planning, Free Tier eligible |
| TTL | Time To Live — auto-delete items after expiry |
| PK/SK | Partition Key / Sort Key |
| Describe-table | Shows table status and schema |
