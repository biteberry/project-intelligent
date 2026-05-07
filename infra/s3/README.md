# S3 Data Lake Provisioning (Issue #45)

This document outlines how the `project-intelligent` S3 data lake was provisioned and secured using the AWS CLI.

The provisioning script used to apply these configurations is available in `provision_s3.ps1`.

## Naming Convention
Because AWS S3 bucket names must be unique across the entire world, all buckets are appended with the AWS Account ID (`307828758318`) to ensure global uniqueness.

## Provisioning Steps & Explanations

### Step 1: Bucket Creation (`aws s3 mb`)
```powershell
aws s3 mb s3://project-intelligent-landing-307828758318 --region ap-south-1
```
* **Explanation:** `mb` stands for "Make Bucket". This command contacts AWS and creates the 5 globally unique buckets in the Mumbai (`ap-south-1`) region.

### Step 2: Blocking Public Access (`aws s3api put-public-access-block`)
```powershell
aws s3api put-public-access-block --bucket <name> --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```
* **Explanation:** This applies the strict "Security Baseline". It flips all four AWS public-blocking switches to `true`. This guarantees that even if someone accidentally writes a bad policy later, these buckets can *never* be accessed from the public internet.

### Step 3: Server-Side Encryption (`aws s3api put-bucket-encryption`)
```powershell
aws s3api put-bucket-encryption --bucket <name> --server-side-encryption-configuration file://encryption-config.json
```
* **Explanation:** This tells AWS to intercept any file uploaded to these buckets and scramble (encrypt) it using the `AES256` standard before saving it to the hard drive. The configuration is read from `encryption-config.json`.

### Step 4: Enabling Versioning (`aws s3api put-bucket-versioning`)
```powershell
aws s3api put-bucket-versioning --bucket <name> --versioning-configuration Status=Enabled
```
* **Explanation:** Applied only to the Bronze, Silver, Gold, and Artifacts buckets. If a file is overwritten or deleted, S3 will quietly keep the old version hidden in the background. This is crucial for Apache Iceberg's "Time Travel" feature, allowing you to rollback your database if bad stock data gets ingested. The Landing zone does not get versioning since it only holds temporary raw files.

### Step 5: Cost Optimization Lifecycle (`aws s3api put-bucket-lifecycle-configuration`)
```powershell
aws s3api put-bucket-lifecycle-configuration --bucket project-intelligent-landing-307828758318 --lifecycle-configuration file://landing-lifecycle.json
```
* **Explanation:** The Landing bucket is just a temporary drop-zone for raw CSVs downloaded from Yahoo Finance. This rule tells AWS to act like an automatic janitor—any file sitting in that bucket for exactly 30 days is permanently deleted so you never pay for unnecessary storage. The configuration is read from `landing-lifecycle.json`.
