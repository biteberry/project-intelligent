# Cost Optimization: Migrating from AWS Secrets Manager to SSM Parameter Store

## Context & Motivation
During the initial project setup, API keys (Finnhub, AlphaVantage) were stored in **AWS Secrets Manager**. While Secrets Manager provides excellent security and rotation capabilities, it incurs a flat fee of **$0.40 per secret per month**. 

To strictly adhere to the project's goal of staying within the **AWS Free Tier**, we migrated all secrets to **AWS Systems Manager (SSM) Parameter Store** using the `SecureString` parameter type. SSM `SecureString` uses the exact same AWS KMS encryption as Secrets Manager, but standard-tier parameters are **100% free**.

This document outlines the step-by-step process used to perform this migration, update the IAM policies, and permanently delete the Secrets Manager entries to halt billing.

---

## Step-by-Step Migration Guide

### Step 1: Create the Secrets in SSM Parameter Store
We recreated the secrets in SSM Parameter Store. Using the AWS CLI, we created `SecureString` parameters.

```bash
# Create AlphaVantage API Key in SSM
aws ssm put-parameter \
    --name "/project-intelligent/alphavantage/api-key" \
    --value "YOUR_ALPHAVANTAGE_KEY" \
    --type "SecureString" \
    --tier Standard \
    --region ap-south-1

# Create Finnhub API Key in SSM
aws ssm put-parameter \
    --name "/project-intelligent/finnhub/api-key" \
    --value "YOUR_FINNHUB_KEY" \
    --type "SecureString" \
    --tier Standard \
    --region ap-south-1
```

### Step 2: Refactor Python Code to use SSM
We modified `src/utils/secrets.py` to transparently fetch from SSM instead of Secrets Manager. By keeping the `get_secret()` function signature identical, none of the ingestion scripts needed to change.

**Old Code (Secrets Manager):**
```python
client = boto3.client("secretsmanager", region_name=region_name)
response = client.get_secret_value(SecretId=secret_name)
secret_value = response["SecretString"]
```

**New Code (SSM Parameter Store):**
```python
client = boto3.client("ssm", region_name=region_name)
response = client.get_parameter(Name=secret_name, WithDecryption=True)
secret_value = response["Parameter"]["Value"]
```

### Step 3: Update IAM Policies
The EC2 Instance Profile (and any Lambda execution roles) previously had permission to call `secretsmanager:GetSecretValue`. We removed this and replaced it with `ssm:GetParameter`.

**Modified `infra/iam/ec2-instance-policy.json`:**
```json
{
    "Sid": "SSMParameterStoreProjectAccess",
    "Effect": "Allow",
    "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParameterHistory",
        "ssm:GetParametersByPath"
    ],
    "Resource": "arn:aws:ssm:*:*:parameter/project-intelligent/*"
}
```

**Applying the Policy Update:**
To apply the updated policy to the live AWS environment, we created a new policy version and set it as the default:
```bash
aws iam create-policy-version \
    --policy-arn "arn:aws:iam::307828758318:policy/ec2-instance-policy" \
    --policy-document file://infra/iam/ec2-instance-policy.json \
    --set-as-default
```

### Step 4: Verify the New Configuration
We executed a test script on the EC2 instance via AWS SSM to verify the IAM policy and Python code changes worked:

```bash
# Example test script executed on EC2
python3 -c "from src.utils.secrets import get_secret; print(get_secret('/project-intelligent/finnhub/api-key'))"
```

### Step 5: Delete AWS Secrets Manager Secrets (Stop Billing)
Once the migration was verified, we permanently deleted the secrets from AWS Secrets Manager. Note the `--force-delete-without-recovery` flag; without this, AWS puts the secret into a 7-30 day recovery window where it **continues to incur charges**.

```bash
# Force delete Finnhub secret
aws secretsmanager delete-secret \
    --secret-id "/project-intelligent/finnhub/api-key" \
    --force-delete-without-recovery \
    --region ap-south-1

# Force delete AlphaVantage secret
aws secretsmanager delete-secret \
    --secret-id "/project-intelligent/alphavantage/api-key" \
    --force-delete-without-recovery \
    --region ap-south-1
```

Finally, we verified the secrets were gone:
```bash
aws secretsmanager list-secrets --region ap-south-1
# Output should show an empty "SecretList": []
```

## How to Manage Secrets Moving Forward
If you need to view or update these API keys in the future:
1. Log into the AWS Console -> **Systems Manager**.
2. Click **Parameter Store** on the left menu.
3. Click on the parameter name (e.g., `/project-intelligent/finnhub/api-key`).
4. Click **Show** next to the Value to view it, or click **Edit** at the top right to change it.
