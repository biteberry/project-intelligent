# Issue #140 — Enable S3 Object Lock COMPLIANCE Mode on Landing Bucket

**Repo:** biteberry/project-intelligent  
**Issue:** [#140](https://github.com/biteberry/project-intelligent/issues/140)  
**Milestone:** M1: Phase 1.1 — Environment Provisioning  
**Priority:** Critical  

---

## What You Will Learn

By completing this task you will understand:

- What S3 Object Lock is and why it exists
- The difference between COMPLIANCE and GOVERNANCE modes
- Why Object Lock must be enabled **at bucket creation time**
- How to safely delete and recreate an S3 bucket
- How to add an explicit IAM Deny statement to harden a bucket

---

## Background — Key Concepts

### What is S3 Versioning?
Every time you overwrite or delete an object in S3, versioning keeps the old copy. You can recover an old version, but a sufficiently privileged IAM user can still permanently delete all versions.

### What is S3 Object Lock?
Object Lock goes further. Once an object is stored, it **cannot be deleted or overwritten** by *anyone* — not even root — until the retention period expires. It is the "write-once, read-many" (WORM) guarantee.

### GOVERNANCE mode vs COMPLIANCE mode

| Mode | Who can bypass? |
|---|---|
| GOVERNANCE | IAM users with `s3:BypassGovernanceRetention` permission can delete |
| **COMPLIANCE** | **Nobody** can delete — not even AWS root — until retention expires |

We need **COMPLIANCE** mode for the Landing bucket because raw ingested market data must be immutable for audit and reprocessing purposes.

### Critical Constraint: Object Lock must be enabled at creation
AWS only allows Object Lock to be enabled when a bucket is **first created**. You **cannot** add it to an existing bucket. Our current landing bucket was created without it. We must:

1. Confirm the bucket is empty (or back up objects)
2. Delete the existing bucket
3. Recreate it with Object Lock enabled
4. Reapply all previous configurations (encryption, public access block, lifecycle)
5. Set the default retention rule

---

## Prerequisites — Verify Before Starting

Open a PowerShell terminal and run these checks.

### 1. Confirm AWS CLI is working and you're in the right account

```powershell
aws sts get-caller-identity
```

Expected output — verify `Account` matches `307828758318`:

```json
{
    "UserId": "...",
    "Account": "307828758318",
    "Arn": "arn:aws:iam::307828758318:..."
}
```

### 2. Set your variables (run these in every new terminal session)

```powershell
$accountId = "307828758318"
$region = "ap-south-1"
$landingBucket = "project-intelligent-landing-$accountId"
```

### 3. Check if Object Lock is already enabled

```powershell
aws s3api get-object-lock-configuration --bucket $landingBucket
```

**If you see:** `An error occurred (ObjectLockConfigurationNotFoundError)` → Object Lock is NOT enabled. Continue with the steps below.  
**If you see:** a JSON response with `"ObjectLockEnabled": "Enabled"` → Object Lock is already on; skip to Step 5.

---

## Step 1 — Confirm the Landing Bucket Is Empty

Before deleting the bucket, make sure there are no objects inside it.

```powershell
aws s3 ls s3://$landingBucket --recursive
```

- **If no output** → bucket is empty. Safe to proceed.
- **If objects are listed** → the bucket has data. List them, note down their names, then delete them:

```powershell
# Delete all objects and versions (required before bucket deletion)
aws s3 rm s3://$landingBucket --recursive
```

> **Note:** At Phase 0/Phase 1.1, the landing bucket should be empty — no real ingestion has happened yet. If it is not empty, confirm with your team before deleting.

---

## Step 2 — Delete the Existing Landing Bucket

S3 requires a bucket to be **completely empty** (including all object versions and delete markers) before it can be deleted.

### 2a. Check for object versions

First check whether any versions exist — PowerShell does **not** support bash-style `$(...)` subcommands inside strings, so we split this into two steps.

```powershell
aws s3api list-object-versions --bucket $landingBucket
```

- **If output shows `"Versions": null` or is empty** → no versions to clean up. Skip to Step 2b.
- **If versions are listed** → save the output to a file and use `file://` to pass it to `delete-objects`:

```powershell
# Save version list to a temp file
aws s3api list-object-versions `
  --bucket $landingBucket `
  --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' `
  --output json | Out-File -FilePath "$env:TEMP\versions.json" -Encoding ASCII

# Delete using the file
aws s3api delete-objects --bucket $landingBucket --delete file://$env:TEMP/versions.json
```

> **Why `file://`?** PowerShell strips double quotes from JSON when passing inline strings to external programs like `aws`. Using a file avoids all quoting issues — the same pattern used for `encryption-config.json` throughout this project.

### 2b. Delete the bucket

```powershell
aws s3api delete-bucket --bucket $landingBucket --region $region
```

**Verify it is gone:**

```powershell
aws s3 ls | Select-String "landing"
```

You should see **no output** — the bucket no longer exists.

---

## Step 3 — Recreate the Landing Bucket WITH Object Lock Enabled

The `--object-lock-enabled-for-bucket` flag is the critical difference from the original creation. This flag:
- Enables Object Lock
- Automatically enables Versioning (required by Object Lock)

```powershell
aws s3api create-bucket `
  --bucket $landingBucket `
  --region $region `
  --create-bucket-configuration LocationConstraint=$region `
  --object-lock-enabled-for-bucket
```

Expected output:

```json
{
    "Location": "http://project-intelligent-landing-307828758318.s3.amazonaws.com/"
}
```

---

## Step 4 — Reapply the Security Baseline

The new bucket is bare. We need to reapply all the configurations that were on the original bucket.

### 4a. Navigate to the infra/s3 folder

```powershell
cd C:\Manivannan\Workspace\ANTIGRAVITY\STOCKS\PROJECT_INTELLIGENT\infra\s3
```

### 4b. Block all public access

```powershell
aws s3api put-public-access-block `
  --bucket $landingBucket `
  --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

No output = success.

### 4c. Apply server-side encryption (SSE-S3 AES-256)

```powershell
aws s3api put-bucket-encryption `
  --bucket $landingBucket `
  --server-side-encryption-configuration file://encryption-config.json
```

No output = success.

### 4d. Apply the lifecycle policy

```powershell
aws s3api put-bucket-lifecycle-configuration `
  --bucket $landingBucket `
  --lifecycle-configuration file://landing-lifecycle.json
```

No output = success.

---

## Step 5 — Set the Default Object Lock Retention Rule

This is the core of this issue. Set COMPLIANCE mode with a 365-day retention period as the **default** for every new object uploaded.

> **PowerShell JSON issue:** Passing multi-line JSON inline to `aws` CLI in PowerShell causes quote-stripping errors. Always use a `file://` approach.

**Step 5a — Create the JSON file:**

```powershell
@'
{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
        "DefaultRetention": {
            "Mode": "COMPLIANCE",
            "Days": 365
        }
    }
}
'@ | Out-File -FilePath "$env:TEMP\object-lock.json" -Encoding ASCII
```

**Step 5b — Apply using the file:**

```powershell
aws s3api put-object-lock-configuration `
  --bucket $landingBucket `
  --object-lock-configuration file://$env:TEMP/object-lock.json
```

No output = success.

---

## Step 6 — Verify Object Lock Configuration

```powershell
aws s3api get-object-lock-configuration --bucket $landingBucket
```

**Expected output:**

```json
{
    "ObjectLockConfiguration": {
        "ObjectLockEnabled": "Enabled",
        "Rule": {
            "DefaultRetention": {
                "Mode": "COMPLIANCE",
                "Days": 365
            }
        }
    }
}
```

If you see this — Object Lock is correctly configured. ✅

---

## Step 7 — Update the IAM Policy: Add Explicit Deny on DeleteObject

Even with Object Lock, best practice is to add an explicit **Deny** on `s3:DeleteObject` in the IAM policy. This prevents the EC2 instance role from even attempting a delete (it will fail at the IAM layer before reaching S3).

Open the file `infra/iam/ec2-instance-policy.json` and add the following new statement **inside the `"Statement"` array**, after the last `}` of the existing `S3ProjectBucketsAccess` statement:

```json
{
    "Sid": "DenyDeleteOnLandingBucket",
    "Effect": "Deny",
    "Action": [
        "s3:DeleteObject",
        "s3:DeleteObjectVersion"
    ],
    "Resource": "arn:aws:s3:::project-intelligent-landing-307828758318/*"
}
```

### Full updated `ec2-instance-policy.json` for reference

After your edit, the `Statement` array should look like this:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3ProjectBucketsAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::project-intelligent-*",
                "arn:aws:s3:::project-intelligent-*/*"
            ]
        },
        {
            "Sid": "DenyDeleteOnLandingBucket",
            "Effect": "Deny",
            "Action": [
                "s3:DeleteObject",
                "s3:DeleteObjectVersion"
            ],
            "Resource": "arn:aws:s3:::project-intelligent-landing-307828758318/*"
        },
        {
            "Sid": "DynamoDBProjectTablesAccess",
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Query"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/project-intelligent-*"
        },
        {
            "Sid": "SSMSessionManagerCore",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:UpdateInstanceInformation",
                "ssmmessages:CreateControlChannel",
                "ssmmessages:CreateDataChannel",
                "ssmmessages:OpenControlChannel",
                "ssmmessages:OpenDataChannel"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SecretsManagerProjectAccess",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:project-intelligent-*"
        },
        {
            "Sid": "GlueCatalogProjectAccess",
            "Effect": "Allow",
            "Action": [
                "glue:GetTable",
                "glue:UpdateTable",
                "glue:BatchCreatePartition",
                "glue:GetDatabase"
            ],
            "Resource": [
                "arn:aws:glue:*:*:catalog",
                "arn:aws:glue:*:*:database/project_intelligent_*",
                "arn:aws:glue:*:*:table/project_intelligent_*/*"
            ]
        }
    ]
}
```

### Apply the updated policy to AWS

**First, check whether the policy already exists in AWS:**

```powershell
aws iam list-policies --scope Local --query "Policies[?PolicyName=='ec2-instance-policy'].Arn" --output text
```

---

**Case A — No output (policy does not exist in AWS yet):**

The JSON file is only local. Create the policy in AWS for the first time:

```powershell
aws iam create-policy `
  --policy-name ec2-instance-policy `
  --policy-document file://C:\Manivannan\Workspace\ANTIGRAVITY\STOCKS\PROJECT_INTELLIGENT\infra\iam\ec2-instance-policy.json
```

Expected output includes the policy ARN:
```json
{
    "Policy": {
        "PolicyName": "ec2-instance-policy",
        "Arn": "arn:aws:iam::307828758318:policy/ec2-instance-policy",
        ...
    }
}
```

Then attach it to the EC2 role:

```powershell
aws iam attach-role-policy `
  --role-name project-intelligent-ec2-role `
  --policy-arn arn:aws:iam::307828758318:policy/ec2-instance-policy
```

Verify it is attached:

```powershell
aws iam list-attached-role-policies --role-name project-intelligent-ec2-role
```

---

**Case B — ARN is returned (policy already exists in AWS):**

Create a new version of the policy (replace `<POLICY_ARN>` with the ARN from the list command):

```powershell
aws iam create-policy-version `
  --policy-arn <POLICY_ARN> `
  --policy-document file://C:\Manivannan\Workspace\ANTIGRAVITY\STOCKS\PROJECT_INTELLIGENT\infra\iam\ec2-instance-policy.json `
  --set-as-default
```

> **Why `create-policy-version`?** AWS manages IAM policy versions. Instead of overwriting, you create a new version and set it as default. AWS keeps up to 5 versions.

---

## Step 8 — Test: Attempt to Delete a Test Object (Must Be Denied)

This is your acceptance test. Upload a test object, then try to hard-delete a specific locked version. The delete **must fail**.

> **Important:** `aws s3 rm` does NOT test Object Lock. With versioning enabled, `s3 rm` only adds a **delete marker** on top of the object — the locked version remains underneath untouched. You must use `s3api delete-object` with an explicit `--version-id` to trigger the COMPLIANCE check.

### 8a. Upload a test object

```powershell
# Create a small test file (use $env:TEMP — always exists on Windows)
"test-object-for-lock-verification" | Out-File -FilePath "$env:TEMP\test-lock.txt" -Encoding UTF8

# Upload it to the landing bucket
aws s3 cp $env:TEMP\test-lock.txt s3://$landingBucket/test/test-lock.txt
```

### 8b. Get the version ID of the uploaded object

```powershell
aws s3api list-object-versions --bucket $landingBucket --prefix test/test-lock.txt
```

Note the `VersionId` value from the `"Versions"` array (e.g. `CdQMKgg0oFiv_wFrSOzVwhrynDIBxtti`). Ignore any `DeleteMarkers` entries.

### 8c. Try to hard-delete the locked version — this should be DENIED

```powershell
aws s3api delete-object `
  --bucket $landingBucket `
  --key test/test-lock.txt `
  --version-id <VERSION_ID>
```

**Expected result:**

```
An error occurred (AccessDenied) when calling the DeleteObject operation:
Access Denied because object protected by object lock.
```

This = ✅ COMPLIANCE mode is working. The object is permanently protected for 365 days.

### 8d. Why `aws s3 rm` appears to succeed (important learning)

`aws s3 rm` without a version ID creates a **delete marker** — a lightweight pointer that hides the object from normal `ls` and `get` operations, making it *look* deleted. The actual locked version remains in place untouched. This is S3 versioning behaviour. The COMPLIANCE guarantee is proven only by attempting to delete the version directly with `--version-id`.

### 8e. Clean up delete markers (optional)

Delete markers are not locked and can be removed at any time. To clean them up:

```powershell
# List delete markers
aws s3api list-object-versions --bucket $landingBucket --prefix test/test-lock.txt --query 'DeleteMarkers[*].{Key:Key,VersionId:VersionId}'

# Delete each marker individually using its VersionId
aws s3api delete-object --bucket $landingBucket --key test/test-lock.txt --version-id <MARKER_VERSION_ID>
```

The actual locked file versions will remain — only the markers are removed.

---

## Step 9 — Create the Documentation File

The issue requires creating `infra/s3/landing-object-lock.md`. Create this file with the following content:

**File path:** `infra/s3/landing-object-lock.md`

```markdown
# Landing Bucket — S3 Object Lock Configuration

## Bucket
`project-intelligent-landing-307828758318`

## Object Lock Mode
COMPLIANCE — cannot be overridden by any principal, including root.

## Default Retention Period
365 days from the date of object creation.

## Why COMPLIANCE Mode?
Raw ingested market data in the Landing layer must satisfy write-once, read-many
(WORM) semantics. COMPLIANCE mode ensures data integrity for audit and
reprocessing purposes as documented in docs/architecture/03_data_architecture_medallion.md.

## IAM Reinforcement
An explicit `Deny` on `s3:DeleteObject` and `s3:DeleteObjectVersion` is added
to `infra/iam/ec2-instance-policy.json` (Sid: DenyDeleteOnLandingBucket).
This prevents the EC2/Lambda role from even attempting a delete.

## Verification Command
```bash
aws s3api get-object-lock-configuration \
  --bucket project-intelligent-landing-307828758318
```

Expected response:
```json
{
    "ObjectLockConfiguration": {
        "ObjectLockEnabled": "Enabled",
        "Rule": {
            "DefaultRetention": {
                "Mode": "COMPLIANCE",
                "Days": 365
            }
        }
    }
}
```

## Related
- Issue: #140
- Parent Story: #45
- Architecture: docs/architecture/03_data_architecture_medallion.md
```

---

## Step 10 — Close the Issue

After all acceptance criteria are met, update the GitHub issue:

```powershell
gh issue comment 140 --repo biteberry/project-intelligent --body "All steps completed:
- Landing bucket recreated with Object Lock in COMPLIANCE mode, 365-day retention
- Verified via get-object-lock-configuration
- IAM ec2-instance-policy updated with DenyDeleteOnLandingBucket statement
- infra/s3/landing-object-lock.md created
- Test object delete attempt denied as expected"

gh issue close 140 --repo biteberry/project-intelligent
```

---

## Checklist — Acceptance Criteria

Go through each item before closing:

- [ ] Object Lock enabled on Landing bucket in COMPLIANCE mode
- [ ] Default retention period set to 365 days
- [ ] `aws s3api get-object-lock-configuration` confirms COMPLIANCE mode
- [ ] IAM policy explicitly denies `s3:DeleteObject` on Landing bucket for all principals
- [ ] EC2 role can `PutObject` (verified — unchanged in policy)
- [ ] `infra/s3/landing-object-lock.md` created
- [ ] `infra/iam/ec2-instance-policy.json` updated with Deny statement
- [ ] Issue #140 closed

---

## Summary of Files Changed

| File | Action |
|---|---|
| `infra/iam/ec2-instance-policy.json` | Add `DenyDeleteOnLandingBucket` statement |
| `infra/s3/landing-object-lock.md` | Create — document Object Lock configuration |

---

## Key Concepts Recap (for your learning)

| Term | Meaning |
|---|---|
| Object Lock | AWS feature to make objects immutable for a set period |
| WORM | Write Once, Read Many — data written once, cannot be changed |
| COMPLIANCE mode | No one (not even root) can delete locked objects before retention expires |
| GOVERNANCE mode | Privileged users CAN bypass the lock |
| Explicit Deny | In IAM, a Deny always overrides an Allow — used for hard guardrails |
| Retention Period | How long the object is protected (we use 365 days) |
