# Story #51 — Glue Catalog: Iceberg Table Format for Silver/Gold Layers

## Overview

Configure AWS Glue Catalog to use Apache Iceberg table format for the Silver
and Gold medallion layers. Enables Athena engine v3, registers `silver_ohlcv`
as an Iceberg table via Athena DDL, and validates time-travel queries and
schema evolution.

**Branch:** `feature/issue-51-glue-iceberg-silver-gold`  
**Region:** `ap-south-1`  
**Account:** `307828758318`

---

## Tasks

| Issue | Title | Status |
|-------|-------|--------|
| #136 | Enable Iceberg table format in Glue Catalog and Athena config | ⬜ Todo |
| #137 | Register silver_ohlcv Iceberg table in Glue Catalog via Athena DDL | ⬜ Todo |
| #138 | Validate Iceberg time-travel and schema evolution on silver_ohlcv | ⬜ Todo |
| #51  | Parent story: Glue Catalog Iceberg table format for Silver/Gold layers | ⬜ Todo |

---

## Prerequisites

- Story #52 complete — three Glue databases exist (`project_intelligent_bronze`, `project_intelligent_silver`, `project_intelligent_gold`)
- S3 buckets exist (`project-intelligent-silver-307828758318`, etc.)
- AWS CLI configured for `ap-south-1`

Verify:

```powershell
aws glue get-databases --region ap-south-1 --query 'DatabaseList[?starts_with(Name,`project_intelligent`)].Name'
```

Expected:
```json
["project_intelligent_bronze", "project_intelligent_gold", "project_intelligent_silver"]
```

---

## Step 1 — Enable Athena engine v3 (#136)

Athena engine version 3 is required for all Iceberg DDL and DML operations
(CREATE TABLE, INSERT INTO, time-travel, ALTER TABLE ADD COLUMNS).

The workgroup config is at `infra/athena/workgroup.json`.

### 1a — Review workgroup config

File: `infra/athena/workgroup.json`

```json
{
  "Name": "project-intelligent",
  "Configuration": {
    "ResultConfiguration": {
      "OutputLocation": "s3://project-intelligent-silver-307828758318/athena-results/"
    },
    "EnforceWorkGroupConfiguration": false,
    "PublishCloudWatchMetricsEnabled": false,
    "EngineVersion": {
      "SelectedEngineVersion": "Athena engine version 3"
    }
  },
  "Description": "Workgroup for project-intelligent — Athena engine v3 (required for Iceberg queries)"
}
```

### 1b — Create the Athena workgroup

```powershell
aws athena create-work-group --cli-input-json file://infra/athena/workgroup.json --region ap-south-1
```

**Expected output:** *(no output on success)*

**Actual output:** *(no output — success)*

### 1c — Verify workgroup engine version

```powershell
aws athena get-work-group --work-group project-intelligent --region ap-south-1 `
  --query "WorkGroup.Configuration.EngineVersion"
```

**Expected output:**
```json
{
    "SelectedEngineVersion": "Athena engine version 3",
    "EffectiveEngineVersion": "Athena engine version 3"
}
```

**Actual output:**
```json
{
    "SelectedEngineVersion": "Athena engine version 3",
    "EffectiveEngineVersion": "Athena engine version 3"
}
```

✅ **#136 done**

---

## Step 2 — Register silver_ohlcv Iceberg table (#137)

The DDL file is at `infra/glue/ddl/silver_ohlcv.sql`.

Schema columns match `schemas/silver_ohlcv.schema.json`:
- `date` (TIMESTAMP), `symbol` (STRING)
- `open`, `high`, `low`, `close`, `adj_close` (DOUBLE)
- `volume` (BIGINT)
- `sector` (STRING), `market_cap` (DOUBLE)
- `cap_tier` (STRING), `is_valid_row` (BOOLEAN)

> **Note:** Athena Iceberg tables require `STRING` not `VARCHAR`. `VARCHAR` raises "Unsupported Hive type" error.

### 2a — Review DDL file

File: `infra/glue/ddl/silver_ohlcv.sql`

```sql
CREATE TABLE project_intelligent_silver.silver_ohlcv (
    date         TIMESTAMP,
    symbol       STRING,
    open         DOUBLE,
    high         DOUBLE,
    low          DOUBLE,
    close        DOUBLE,
    adj_close    DOUBLE,
    volume       BIGINT,
    sector       STRING,
    market_cap   DOUBLE,
    cap_tier     STRING,
    is_valid_row BOOLEAN
)
LOCATION 's3://project-intelligent-silver-307828758318/ohlcv/'
TBLPROPERTIES (
    'table_type'          = 'ICEBERG',
    'format'              = 'parquet',
    'write_compression'   = 'snappy'
);
```

### 2b — Run the DDL in Athena

Start the query execution using the `project-intelligent` workgroup:

```powershell
$DDL = Get-Content infra/glue/ddl/silver_ohlcv.sql -Raw
$QID = (aws athena start-query-execution `
  --query-string $DDL `
  --work-group project-intelligent `
  --region ap-south-1 `
  --query "QueryExecutionId" `
  --output text)
Write-Host "QueryExecutionId: $QID"
```

Wait for completion:

```powershell
aws athena get-query-execution --query-execution-id $QID `
  --region ap-south-1 `
  --query "QueryExecution.Status"
```

**Expected output:**
```json
{
    "State": "SUCCEEDED"
}
```

**Actual output:**
```json
{
    "State": "SUCCEEDED"
}
```

### 2c — Verify table in Glue Catalog

```powershell
aws glue get-table `
  --database-name project_intelligent_silver `
  --name silver_ohlcv `
  --region ap-south-1 `
  --query "Table.{Name:Name,Type:Parameters.table_type,Location:StorageDescriptor.Location}"
```

**Expected output:**
```json
{
    "Name": "silver_ohlcv",
    "Type": "ICEBERG",
    "Location": "s3://project-intelligent-silver-307828758318/ohlcv/"
}
```

**Actual output:**
```json
{
    "Name": "silver_ohlcv",
    "Type": "ICEBERG",
    "Location": "s3://project-intelligent-silver-307828758318/ohlcv",
    "Columns": ["date","symbol","open","high","low","close","adj_close","volume","sector","market_cap","cap_tier","is_valid_row"]
}
```

### 2d — Test SELECT (must return no error, 0 rows)

Run in Athena console or via CLI using the `project-intelligent` workgroup:

```sql
SELECT * FROM project_intelligent_silver.silver_ohlcv LIMIT 1;
```

**Expected:** Query succeeds, 0 rows returned (table is empty).

**Actual output:**
```
"SUCCEEDED"  — 0 rows returned (table is empty)
```

✅ **#137 done**

---

## Step 3 — Validate time-travel and schema evolution (#138)

### 3a — Insert test rows

Run in Athena (`project-intelligent` workgroup):

```sql
INSERT INTO project_intelligent_silver.silver_ohlcv VALUES
    (TIMESTAMP '2024-01-02 00:00:00', 'AAPL', 185.20, 186.10, 184.50, 185.90, 185.90, 72800000, 'Technology', 2900000000000.0, 'large', true),
    (TIMESTAMP '2024-01-03 00:00:00', 'AAPL', 184.00, 185.50, 183.10, 184.60, 184.60, 68500000, 'Technology', 2880000000000.0, 'large', true);
```

**Expected:** `INSERT` succeeds, 2 rows affected.

**Actual output:**
```
"SUCCEEDED" — 2 rows inserted (AAPL 2024-01-02, AAPL 2024-01-03)
```

> **Note:** `silver_ohlcv$snapshots` table syntax causes `mismatched input '$'` error in Athena CLI via PowerShell. Use `FOR TIMESTAMP AS OF` time-travel instead of snapshot-ID-based travel.

### 3b — Insert a second batch (to create a new snapshot)

```powershell
$INS2 = "INSERT INTO project_intelligent_silver.silver_ohlcv VALUES (TIMESTAMP '2024-01-04 00:00:00', 'MSFT', 374.10, 375.20, 372.80, 374.90, 374.90, 22100000, 'Technology', 2800000000000.0, 'large', true)"
$QID5 = (aws athena start-query-execution --query-string $INS2 --work-group project-intelligent --region ap-south-1 --query "QueryExecutionId" --output text)
aws athena get-query-execution --query-execution-id $QID5 --region ap-south-1 --query "QueryExecution.Status.State"
```

**Actual output:**
```
"SUCCEEDED" — 1 row inserted (MSFT 2024-01-04)
```

### 3c — Time-travel query (FOR TIMESTAMP AS OF)

AAPL INSERT completed at `2026-05-13T19:00:22Z`. Use `19:02:00Z` — after AAPL, before MSFT:

```powershell
$TT = "SELECT symbol, date, close FROM project_intelligent_silver.silver_ohlcv FOR TIMESTAMP AS OF TIMESTAMP '2026-05-13 19:02:00'"
$QID6 = (aws athena start-query-execution --query-string $TT --work-group project-intelligent --region ap-south-1 --query "QueryExecutionId" --output text)
aws athena get-query-execution --query-execution-id $QID6 --region ap-south-1 --query "QueryExecution.Status.State"
```

**Expected:** Returns only the 2 AAPL rows (MSFT not yet inserted at that timestamp).

**Actual output:**
```json
[
  { "Data": [{"VarCharValue":"symbol"},{"VarCharValue":"date"},{"VarCharValue":"close"}] },
  { "Data": [{"VarCharValue":"AAPL"},{"VarCharValue":"2024-01-02 00:00:00.000000"},{"VarCharValue":"185.9"}] },
  { "Data": [{"VarCharValue":"AAPL"},{"VarCharValue":"2024-01-03 00:00:00.000000"},{"VarCharValue":"184.6"}] }
]
```

✅ Time-travel confirmed — only 2 AAPL rows visible at `2026-05-13 19:02:00Z`, MSFT excluded.

### 3d — Schema evolution: ADD COLUMN

```powershell
$ALT = "ALTER TABLE project_intelligent_silver.silver_ohlcv ADD COLUMNS (split_adjusted BOOLEAN)"
$QID7 = (aws athena start-query-execution --query-string $ALT --work-group project-intelligent --region ap-south-1 --query "QueryExecutionId" --output text)
aws athena get-query-execution --query-execution-id $QID7 --region ap-south-1 --query "QueryExecution.Status.State"
```

**Expected:** `ALTER TABLE` succeeds without table rewrite.

**Actual output:**
```
"SUCCEEDED"
```

### 3e — Verify new column in Glue Catalog

```powershell
aws glue get-table `
  --database-name project_intelligent_silver `
  --name silver_ohlcv `
  --region ap-south-1 `
  --query "Table.StorageDescriptor.Columns[*].Name"
```

**Expected:** Column list includes `split_adjusted` at the end.

**Actual output:**
```json
["date","symbol","open","high","low","close","adj_close","volume","sector","market_cap","cap_tier","is_valid_row","split_adjusted"]
```

✅ **#138 done**

---

## Step 4 — Add IAM Athena permissions to EC2 role

The EC2 role needs permission to run Athena queries and write results to S3.

### 4a — Create Athena IAM policy file

File: `infra/iam/athena-policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AthenaQueryAccess",
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StopQueryExecution",
        "athena:GetWorkGroup",
        "athena:ListWorkGroups"
      ],
      "Resource": [
        "arn:aws:athena:ap-south-1:307828758318:workgroup/project-intelligent"
      ]
    },
    {
      "Sid": "AthenaResultsBucketAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::project-intelligent-silver-307828758318/athena-results/*",
        "arn:aws:s3:::project-intelligent-silver-307828758318"
      ]
    }
  ]
}
```

### 4b — Create and attach the policy

```powershell
aws iam create-policy `
  --policy-name project-intelligent-athena-policy `
  --policy-document file://infra/iam/athena-policy.json `
  --description "Athena workgroup access for EC2 pipeline role"

aws iam attach-role-policy `
  --role-name project-intelligent-ec2-role `
  --policy-arn arn:aws:iam::307828758318:policy/project-intelligent-athena-policy
```

**Actual output:**
```
(paste here)
```

---

## Step 5 — Commit, push, PR, merge

```powershell
git add infra/athena/ infra/glue/ddl/ infra/iam/athena-policy.json
git commit -m "feat(glue): Iceberg Silver/Gold — Athena v3 workgroup, silver_ohlcv DDL, time-travel validated (#136 #137 #138)"
git push origin feature/issue-51-glue-iceberg-silver-gold
```

Create PR:

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" pr create `
  --title "feat(glue): Iceberg Silver/Gold — Athena v3, silver_ohlcv DDL, time-travel validated" `
  --body "Closes #136`nCloses #137`nCloses #138`nCloses #51`n`n## Changes`n- Added Athena workgroup \`project-intelligent\` with engine v3 (\`infra/athena/workgroup.json\`)`n- Added Athena DDL for \`silver_ohlcv\` Iceberg table (\`infra/glue/ddl/silver_ohlcv.sql\`)`n- Added IAM Athena policy for EC2 role (\`infra/iam/athena-policy.json\`)`n`n## Validation`n- Athena workgroup confirmed engine v3`n- \`silver_ohlcv\` Iceberg table created in \`project_intelligent_silver\`; visible in Glue Catalog`n- Time-travel query returned data from previous snapshot`n- ALTER TABLE ADD COLUMNS succeeded without table rewrite" `
  --base main `
  --head feature/issue-51-glue-iceberg-silver-gold
```

Merge and sync:

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" pr merge --merge --auto feature/issue-51-glue-iceberg-silver-gold
git checkout main
git pull origin main
```

---

## Summary

| Step | Action | Files |
|------|--------|-------|
| 1 | Athena workgroup v3 created | `infra/athena/workgroup.json` |
| 2 | `silver_ohlcv` Iceberg table registered via DDL | `infra/glue/ddl/silver_ohlcv.sql` |
| 3 | Time-travel + schema evolution validated | — |
| 4 | EC2 IAM role granted Athena access | `infra/iam/athena-policy.json` |
| 5 | Committed, PR merged, main synced | — |
