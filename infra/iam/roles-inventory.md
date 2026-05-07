# IAM Roles Inventory & Core Concepts

> **Reference:** Resolves [Issue #57] (Part of Parent Story [Issue #44])

Welcome to AWS Identity and Access Management (IAM)! 

Before we build the security layer for the `project-intelligent` stock prediction platform, it is crucial to understand two fundamental concepts: **Roles** and **Policies**.

## Theory: Roles vs. Policies

Imagine AWS is a high-security corporate building.
- **A Role** is like a blank ID badge. It identifies *who* you are, but it doesn't grant you access to any rooms by itself. You can hand this badge to an EC2 server, a Lambda function, or an external system like GitHub.
- **A Policy** is the list of room permissions printed on the back of the badge. It explicitly states exactly *what* rooms you can enter and what you can do inside them.

**The Golden Rule: Principle of Least Privilege**
We will never give an ID badge a master key (represented by a wildcard `*`). If an EC2 server only needs to read from the "Bronze" S3 bucket, we explicitly say `s3:GetObject` on `arn:aws:s3:::project-intelligent-bronze/*`. If a hacker compromises the server, they cannot delete the data because the policy does not have the `s3:DeleteObject` permission.

---

## 1. EC2 Instance Role
**Name:** `project-intelligent-ec2-role`
**Assumed By:** The EC2 virtual machine running our batch jobs.
**Purpose:** Needs to read data from S3, run models, write predictions to DynamoDB, and read configurations from Systems Manager (SSM).

**Required AWS Actions (The Policy):**
- **S3:** `s3:GetObject`, `s3:PutObject`, `s3:ListBucket`
  - *Scope:* Only to `project-intelligent-*` buckets.
- **DynamoDB:** `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:Query`
  - *Scope:* Only to `project-intelligent-*` tables.
- **SSM (Systems Manager):** `ssm:GetParameter`, `ssmmessages:CreateControlChannel`, `ssmmessages:CreateDataChannel`, `ssmmessages:OpenControlChannel`, `ssmmessages:OpenDataChannel`
  - *Scope:* Allows us to securely log into the EC2 instance without SSH keys.
- **Secrets Manager:** `secretsmanager:GetSecretValue`
  - *Scope:* Only for project-specific secrets (no wildcards).
- **Glue (Data Catalog):** `glue:GetTable`, `glue:UpdateTable`, `glue:BatchCreatePartition`, `glue:GetDatabase`
  - *Scope:* Only for our Iceberg data tables.

---

## 2. Lambda Execution Role
**Name:** `project-intelligent-lambda-role`
**Assumed By:** The AWS Lambda function that triggers our pipeline.
**Purpose:** Needs to wake up on a schedule (via EventBridge) and tell the EC2 instance to start running the Python pipeline.

**Required AWS Actions (The Policy):**
- **SSM:** `ssm:SendCommand`
  - *Scope:* Strictly limited to the specific ARN of our EC2 instance. The Lambda cannot send commands to any other server.
- **CloudWatch Logs:** `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
  - *Scope:* Strictly limited to `/aws/lambda/project-intelligent-*` so we can debug Lambda errors.

---

## 3. GitHub Actions OIDC Role
**Name:** `project-intelligent-ghactions-role`
**Assumed By:** GitHub Actions (the CI/CD server).
**Purpose:** Traditionally, people put permanent AWS Access Keys in GitHub to deploy code. This is very dangerous if leaked. Instead, we use **OIDC (OpenID Connect)**. GitHub and AWS establish a trust relationship. GitHub says "I am deploying the main branch", and AWS securely issues temporary access for a few minutes.

**Required AWS Actions (The Policy):**
- **S3:** `s3:PutObject`
  - *Scope:* Only uploading deployment artifacts.
- **Lambda:** `lambda:UpdateFunctionCode`
  - *Scope:* Only updating our specific Lambda function.

**Trust Policy Constraint:**
- `StringLike`: `token.actions.githubusercontent.com:sub` = `repo:biteberry/project-intelligent:ref:refs/heads/main`
- *Meaning:* AWS will ONLY issue the temporary badge if the request comes specifically from our repository's `main` branch.
