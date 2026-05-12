# Issue #73 — Lambda SSM Dispatcher Deployment Guide

**Repo:** biteberry/project-intelligent  
**Related Issues:** #48 (parent), #72 (code), #73 (deployment)

---

## Overview
This guide provides step-by-step instructions to package, deploy, and verify the Lambda SSM dispatcher function for the pipeline orchestration architecture. All steps are AWS CLI and IaC safe.

---

## Prerequisites
- Lambda handler implemented in `src/lambda/ssm_dispatcher/handler.py`
- Unit tests passing (see `tests/lambda/test_ssm_dispatcher.py`)
- Lambda execution role created (see issue #44)
- AWS CLI configured for your account/region

---

## Step 1 — Package the Lambda Function

1. Change to the Lambda source directory:
   ```powershell
   cd src/lambda/ssm_dispatcher
   ```
2. Zip the handler for deployment:
   ```powershell
   Compress-Archive -Path handler.py -DestinationPath ssm_dispatcher.zip -Force
   ```

---

## Step 2 — Deploy the Lambda Function

1. Set variables:
   ```powershell
   $functionName = "project-intelligent-ssm-dispatcher"
   $roleArn = "arn:aws:iam::<account-id>:role/project-intelligent-lambda-execution"  # Replace with your role ARN
   $region = "ap-south-1"
   $ec2InstanceId = "i-xxxxxxxxxxxxxxxxx"  # Replace with your EC2 instance ID
   $ssmDocumentName = "MySSMDocument"      # Replace with your SSM document name
   ```
2. Create the Lambda function:
   ```powershell
   aws lambda create-function `
     --function-name $functionName `
     --runtime python3.12 `
     --role $roleArn `
     --handler handler.lambda_handler `
     --zip-file fileb://ssm_dispatcher.zip `
     --memory-size 128 `
     --timeout 30 `
     --region $region `
     --environment Variables={EC2_INSTANCE_ID=$ec2InstanceId,SSM_DOCUMENT_NAME=$ssmDocumentName}
   ```
   - If the function already exists, use `aws lambda update-function-code` and `update-function-configuration` instead.

---

## Step 3 — Verify Lambda Deployment

1. List the function:
   ```powershell
   aws lambda get-function --function-name $functionName --region $region
   ```
2. Test invoke:
   ```powershell
   aws lambda invoke --function-name $functionName --payload '{"detail-type": "Scheduled Event - Daily"}' out.json --region $region
   Get-Content out.json
   ```

---

## Step 4 — Attach Execution Role (if not set)

If you need to update the role:
```powershell
aws lambda update-function-configuration `
  --function-name $functionName `
  --role $roleArn `
  --region $region
```

---

## Step 5 — Update Environment Variables (if needed)

```powershell
aws lambda update-function-configuration `
  --function-name $functionName `
  --environment Variables={EC2_INSTANCE_ID=$ec2InstanceId,SSM_DOCUMENT_NAME=$ssmDocumentName} `
  --region $region
```

---

## Checklist — Acceptance Criteria
- [ ] Lambda function deployed as `project-intelligent-ssm-dispatcher`
- [ ] Python 3.12, 128 MB, 30s timeout
- [ ] Env vars set: EC2_INSTANCE_ID, SSM_DOCUMENT_NAME
- [ ] Execution role attached
- [ ] Lambda invoke test call succeeds

---

## References
- [AWS Lambda CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/lambda/index.html)
- [AWS Lambda Environment Variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [AWS Lambda IAM Roles](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)

---

> Document last updated: 2026-05-12
