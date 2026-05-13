# Story #52 — AWS Glue Catalog Foundation Implementation Guide

## Overview
Set up AWS Glue Data Catalog for Iceberg table format.  
Creates three databases (bronze/silver/gold), registers Iceberg table schemas,
and grants the EC2 IAM role read/write access to the catalog.

**Branch:** `feature/issue-52-glue-catalog-foundation`  
**Region:** `ap-south-1`  
**Account:** `307828758318`

---

## Tasks
| Issue | Title | Status |
|-------|-------|--------|
| #81 | Enable AWS Glue Data Catalog and create layer databases | ✅ Done |
| #82 | Register Iceberg table schemas in Glue Catalog | ✅ Done |
| #83 | Verify IAM role has Glue Catalog read/write access | ✅ Done |
| #52 | Parent story: AWS Glue Catalog foundation setup | ⬜ Todo |

---

## Step 1 — Create Glue databases (#81)

The Glue Data Catalog is enabled by default in every AWS account/region.
We only need to create the three databases for the medallion layers.

The `file://` workaround is required because PowerShell strips inner quotes
from single-quoted JSON strings passed to the AWS CLI.

### 1a — Create database input files

Files already created at:
- `infra/glue/db-bronze.json`
- `infra/glue/db-silver.json`
- `infra/glue/db-gold.json`

### 1b — Create bronze database

```powershell
aws glue create-database --database-input file://infra/glue/db-bronze.json --region ap-south-1
```

**Expected output:** *(no output on success)*

**Actual output:** *(no output — success)*

### 1c — Create silver database

```powershell
aws glue create-database --database-input file://infra/glue/db-silver.json --region ap-south-1
```

**Actual output:** *(no output — success)*

### 1d — Create gold database

```powershell
aws glue create-database --database-input file://infra/glue/db-gold.json --region ap-south-1
```

**Actual output:** *(no output — success)*

### 1e — Verify all 3 databases exist

```powershell
aws glue get-databases --region ap-south-1 --query 'DatabaseList[?starts_with(Name,`project_intelligent`)].Name'
```

**Expected output:**
```json
[
    "project_intelligent_bronze",
    "project_intelligent_gold",
    "project_intelligent_silver"
]
```

**Actual output:**
```json
[
    "project_intelligent_bronze",
    "project_intelligent_gold",
    "project_intelligent_silver"
]
```

✅ **#81 done**

---

## Step 2 — Register Iceberg table schemas (#82)

Table definition files are at:
- `infra/glue/bronze_ohlcv_table.json`
- `infra/glue/silver_ohlcv_table.json`
- `infra/glue/gold_swing_features_table.json`

Column definitions are derived from the existing schema files in `schemas/`.

### 2a — Register bronze_ohlcv table

```powershell
aws glue create-table --cli-input-json file://infra/glue/bronze_ohlcv_table.json --region ap-south-1
```

**Actual output:** *(no output — success)*

### 2b — Register silver_ohlcv table

```powershell
aws glue create-table --cli-input-json file://infra/glue/silver_ohlcv_table.json --region ap-south-1
```

**Actual output:** *(no output — success)*

### 2c — Register gold_swing_features table

```powershell
aws glue create-table --cli-input-json file://infra/glue/gold_swing_features_table.json --region ap-south-1
```

**Actual output:** *(no output — success)*

### 2d — Verify tables are accessible

```powershell
aws glue get-table --database-name project_intelligent_bronze --name bronze_ohlcv --region ap-south-1 --query 'Table.{Name:Name,Location:StorageDescriptor.Location,Format:Parameters.table_type}'
aws glue get-table --database-name project_intelligent_silver --name silver_ohlcv --region ap-south-1 --query 'Table.{Name:Name,Location:StorageDescriptor.Location,Format:Parameters.table_type}'
aws glue get-table --database-name project_intelligent_gold --name gold_swing_features --region ap-south-1 --query 'Table.{Name:Name,Location:StorageDescriptor.Location,Format:Parameters.table_type}'
```

**Expected output (each):**
```json
{
    "Name": "bronze_ohlcv",
    "Location": "s3://project-intelligent-bronze-307828758318/ohlcv/",
    "Format": "ICEBERG"
}
```

**Actual output:** *(all 3 tables returned Name, Location and Format: ICEBERG — success)*

✅ **#82 done**

---

## Step 3 — Add Glue IAM permissions to EC2 role (#83)

The policy file is at `infra/iam/glue-policy.json`.

Required permissions:
- `glue:GetDatabase`, `glue:GetDatabases`
- `glue:GetTable`, `glue:GetTables`
- `glue:CreateTable`, `glue:UpdateTable`
- `glue:BatchCreatePartition`, `glue:GetPartition`, `glue:GetPartitions`, `glue:BatchGetPartition`

### 3a — Create the IAM policy

```powershell
aws iam create-policy `
  --policy-name project-intelligent-glue-policy `
  --policy-document file://infra/iam/glue-policy.json `
  --description "Glue Catalog read/write access for EC2 pipeline role"
```

**Expected output:**
```json
{
    "Policy": {
        "PolicyName": "project-intelligent-glue-policy",
        "Arn": "arn:aws:iam::307828758318:policy/project-intelligent-glue-policy",
        ...
    }
}
```

**Actual output:**
```
(paste here)
```

### 3b — Attach policy to EC2 role

```powershell
aws iam attach-role-policy `
  --role-name project-intelligent-ec2-role `
  --policy-arn arn:aws:iam::307828758318:policy/project-intelligent-glue-policy
```

**Actual output:** *(no output — success)*

### 3c — Simulate to confirm access

```powershell
aws iam simulate-principal-policy `
  --policy-source-arn arn:aws:iam::307828758318:role/project-intelligent-ec2-role `
  --action-names glue:GetDatabase glue:GetTable glue:CreateTable glue:UpdateTable `
  --resource-arns "arn:aws:glue:ap-south-1:307828758318:catalog" "arn:aws:glue:ap-south-1:307828758318:database/project_intelligent_bronze" "arn:aws:glue:ap-south-1:307828758318:table/project_intelligent_bronze/*" `
  --query 'EvaluationResults[].{Action:EvalActionName,Decision:EvalDecision}'
```

**Expected output:** All actions show `"Decision": "allowed"`

**Actual output:** *(all actions returned allowed — success)*

### 3d — Live test from EC2 via SSM Session Manager

```bash
aws ssm start-session --target i-004ede57a842280fe --region ap-south-1
# inside EC2:
aws glue get-databases --region ap-south-1 --query 'DatabaseList[?starts_with(Name,`project_intelligent`)].Name'
```

**Actual output:**
```json
[
    "project_intelligent_bronze",
    "project_intelligent_gold",
    "project_intelligent_silver"
]
```

✅ **#83 done**

---

## Step 4 — Commit and push

```powershell
git add infra/glue/ infra/iam/glue-policy.json
git commit -m "feat(glue): Glue Catalog foundation — databases, Iceberg tables, IAM (#81 #82 #83)"
git push origin feature/issue-52-glue-catalog-foundation
```

---

## Step 5 — Create and merge PR

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" pr create `
  --title "feat(glue): Glue Catalog foundation — databases, Iceberg tables, IAM" `
  --body "Closes #81`nCloses #82`nCloses #83`nCloses #52`n`n## Changes`n- Created 3 Glue databases (bronze/silver/gold)`n- Registered Iceberg table schemas for all 3 layers`n- Added Glue IAM policy to EC2 role" `
  --base main `
  --head feature/issue-52-glue-catalog-foundation
```

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" pr merge feature/issue-52-glue-catalog-foundation --squash --delete-branch
```

---

## Files Created

| File | Purpose |
|------|---------|
| `infra/glue/db-bronze.json` | Glue database input for bronze layer |
| `infra/glue/db-silver.json` | Glue database input for silver layer |
| `infra/glue/db-gold.json` | Glue database input for gold layer |
| `infra/glue/bronze_ohlcv_table.json` | Iceberg table definition for bronze OHLCV |
| `infra/glue/silver_ohlcv_table.json` | Iceberg table definition for silver OHLCV |
| `infra/glue/gold_swing_features_table.json` | Iceberg table definition for gold swing features |
| `infra/iam/glue-policy.json` | IAM policy granting EC2 role Glue read/write |
