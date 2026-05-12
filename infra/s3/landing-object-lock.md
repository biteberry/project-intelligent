# Landing Bucket — S3 Object Lock Configuration

## Bucket

`project-intelligent-landing-307828758318`

## Object Lock Mode

**COMPLIANCE** — cannot be overridden by any principal, including AWS root.

## Default Retention Period

**365 days** from the date of object creation.

## Why COMPLIANCE Mode?

Raw ingested market data in the Landing layer must satisfy write-once, read-many
(WORM) semantics. COMPLIANCE mode ensures data integrity for audit and reprocessing
purposes as documented in `docs/architecture/03_data_architecture_medallion.md`.

GOVERNANCE mode was rejected because it can be bypassed by privileged IAM users.
COMPLIANCE mode provides an absolute guarantee — no deletion is possible until
the retention period expires, regardless of IAM permissions.

## How It Works With Versioning

Object Lock requires versioning to be enabled. When an object is uploaded:

1. S3 creates a new **version** of the object with a unique `VersionId`
2. That version is locked in COMPLIANCE mode for 365 days from upload time
3. Running `aws s3 rm` does **not** delete the locked version — it creates a **delete marker** (a harmless pointer). The locked data remains intact underneath.
4. Only `s3api delete-object --version-id <id>` attempts a true hard delete, and COMPLIANCE mode blocks it with `AccessDenied`.

## IAM Reinforcement

An explicit `Deny` on `s3:DeleteObject` and `s3:DeleteObjectVersion` is added
to `infra/iam/ec2-instance-policy.json` (Sid: `DenyDeleteOnLandingBucket`).
This prevents the EC2/Lambda role from even attempting a delete — the IAM layer
rejects it before it reaches S3.

## Verification Commands

**Check Object Lock configuration:**

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

**Test that a locked version cannot be deleted:**

```bash
# List versions to get a VersionId
aws s3api list-object-versions \
  --bucket project-intelligent-landing-307828758318 \
  --prefix <some-key>

# Attempt hard delete of locked version — must return AccessDenied
aws s3api delete-object \
  --bucket project-intelligent-landing-307828758318 \
  --key <some-key> \
  --version-id <VersionId>
```

Expected error:
```
An error occurred (AccessDenied): Access Denied because object protected by object lock.
```

## Bucket Creation Note

Object Lock **must be enabled at bucket creation time** — it cannot be added to an existing
bucket. The bucket was recreated using:

```bash
aws s3api create-bucket \
  --bucket project-intelligent-landing-307828758318 \
  --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1 \
  --object-lock-enabled-for-bucket
```

## Related

- Issue: [#140](https://github.com/biteberry/project-intelligent/issues/140)
- Parent Story: [#45](https://github.com/biteberry/project-intelligent/issues/45)
- IAM Policy: `infra/iam/ec2-instance-policy.json`
- Architecture: `docs/architecture/03_data_architecture_medallion.md`
