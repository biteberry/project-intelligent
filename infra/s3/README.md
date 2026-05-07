# S3 Data Lake Provisioning Plan (Issue #45)

This document outlines the provisioning plan for the `project-intelligent` S3 data lake.

## Naming Convention
All buckets are appended with the AWS Account ID (`307828758318`) to ensure global uniqueness.

## Provisioning Steps

### 1. Create the 5 Buckets (Issue #62)
- `project-intelligent-landing-307828758318`
- `project-intelligent-bronze-307828758318`
- `project-intelligent-silver-307828758318`
- `project-intelligent-gold-307828758318`
- `project-intelligent-artifacts-307828758318`
- *Command:* `aws s3 mb s3://<bucket-name> --region ap-south-1`

### 2. Secure the Buckets (Issue #63)
- **Block Public Access:** `aws s3api put-public-access-block` applied to all 5 buckets to ensure no data is accidentally exposed to the internet.
- **Server-Side Encryption:** `aws s3api put-bucket-encryption` applied to enforce `AES256` (SSE-S3) encryption at rest for all 5 buckets.

### 3. Configure Data Resiliency (Issue #64)
- **Enable Versioning:** `aws s3api put-bucket-versioning` applied to the **Bronze, Silver, Gold, and Artifacts** buckets for point-in-time recovery and Iceberg schema evolution rollbacks. The Landing zone does not get versioning since it only holds temporary raw files.

### 4. Configure Cost Optimization (Issue #65)
- **Lifecycle Rule:** `aws s3api put-bucket-lifecycle-configuration` applied to the **Landing** bucket to automatically delete raw files older than 30 days.
