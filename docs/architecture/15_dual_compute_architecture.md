# 15 Dual-Compute Architecture: Free-Tier + Ephemeral Heavy Compute

This document defines the compute separation strategy. To minimize AWS costs while ensuring sufficient memory/CPU for heavy Machine Learning data transformations, the architecture is split into two distinct compute nodes.

## Node A: The Fetcher (Always-On)
- **Instance Type:** `t2.micro` (Free Tier)
- **Status:** Runs 24/7.
- **Purpose:** Network-bound, lightweight tasks.
- **Jobs Executed Here:**
  - `J01` (OHLCV Yahoo Finance Ingestion)
  - `J02` (NSE Delivery Pct Ingestion)
  - `J03` (Fundamentals Ingestion)
  - `J04` (Corporate Actions)
  - `J05`, `J06`, `J07`, `J08` (Macro, Earnings, Circuit Bands)
  - `J09` (Finnhub News Sentiment)
  - `J10` (Any future API integrations)
- **Why:** Downloading JSON/CSV from external APIs requires very little CPU and RAM. It is purely waiting for network responses. A 1GB RAM instance is perfect for this and costs nothing under the free tier.

## Node B: The Cruncher (Ephemeral / On-Demand)
- **Instance Type:** `t3a.xlarge` (4 vCPU, 16GB RAM)
- **Status:** **STOPPED** 99% of the time. Only runs for a few minutes per day.
- **Purpose:** Heavy, memory-bound analytical data processing and Machine Learning.
- **Jobs Executed Here:**
  - `J11` (Silver Layer Transformation - DuckDB S3 Joins)
  - `J12` (Gold Layer Feature Engineering - MACD, RSI, 52-Week rolling windows via Pandas-TA)
  - `J13` (Market Regime Detection)
  - `J14+` (Model Training and Inference)
- **Why:** DuckDB and PyIceberg require significant memory to decompress Parquet files and execute massive SQL `JOIN`s across millions of rows. Pandas-TA requires RAM to hold arrays for rolling statistics. The `t3a.xlarge` completes these tasks in seconds/minutes. Because it is shut down immediately after use, it costs roughly ~$2-$3 per month instead of $120.

---

## Orchestration & Cost Fail-Safes

### Automated Boot and Shutdown
The GitHub Actions workflow (`daily_ingestion.yml`) acts as the orchestrator:
1. It sends SSM commands to **Node A** to download all daily data to the Bronze S3 bucket.
2. Once complete, it executes an AWS CLI command to `aws ec2 start-instances` on **Node B**.
3. It waits for Node B to boot, then sends SSM commands to execute the Silver and Gold pipelines.
4. Using an `if: always()` block in GitHub Actions, it executes `aws ec2 stop-instances` on Node B, guaranteeing the shutdown command is sent even if the python scripts crash.

### The Ultimate Cost Fail-Safe: CloudWatch Alarm
If GitHub Actions itself crashes or GitHub goes offline before sending the shutdown command, Node B would run indefinitely, incurring high costs.

To prevent this, an **AWS CloudWatch Alarm** is permanently attached to Node B:
- **Condition:** If CPU Utilization drops below `2%` for `15 minutes`.
- **Action:** Issue a hard `Stop Instance` command directly within AWS.

This hardware-level fail-safe guarantees that your accidental cost exposure is capped at pennies.
