# Implementation Plan: Feature #4 (NSE Delivery Percentage)

This document outlines the architecture and execution steps for **Feature #4**, which involves downloading the daily NSE Bhav Copy, extracting the Delivery Percentage for each stock, and saving it to the Bronze layer.

## User Review Required
> [!IMPORTANT]
> **Landing Layer Usage:** For Feature #3 we skipped the Landing Layer because Yahoo Finance gave us clean DataFrames in memory. For Feature #4, the NSE gives us a raw `.csv` or `.zip` file. As discussed, we will write this raw file directly to the **Landing Layer S3 Bucket** first before parsing it into Parquet for the Bronze layer. 

## Open Questions For You
> [!WARNING]
> Please answer the following before I start coding:
> 1. **NSE Holiday List:** Do you want me to hardcode the 2026 NSE Holiday calendar into the script, or use an external python library (like `holidays`) combined with weekend detection?
> 2. **Job ID:** I will name this orchestration script `j02_delivery_pct_daily.py`. Is J02 the correct ID for this?

## Proposed Changes

### Component 1: Holiday Detection
#### [NEW] `src/utils/holidays.py`
- Implements `is_trading_day(date)` to check for weekends (Saturday/Sunday) and known NSE holidays.
- If it is not a trading day, the J02 script will gracefully exit and log a "SKIPPED_HOLIDAY" status to DynamoDB, avoiding false failure alerts.

### Component 2: Bhav Copy Downloader
#### [NEW] `src/ingestion/bhav_copy_fetcher.py`
- Implements `download_bhav_copy(date)` which constructs the NSE archive URL (`https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_DDMMYYYY.csv`).
- Uses `requests` with standard browser headers (NSE often blocks raw python requests) to download the file.
- Saves the raw file to the `project-intelligent-landing` S3 bucket.

### Component 3: Delivery Percentage Extraction
#### [NEW] `src/ingestion/bhav_copy_parser.py`
- Reads the raw CSV file from Landing S3.
- Filters out non-equity rows (Series != 'EQ').
- Extracts the `SYMBOL` and `DELIV_PER` (Delivery Percentage) columns.

### Component 4: Orchestration
#### [NEW] `src/ingestion/j02_delivery_pct_daily.py`
- The main entrypoint.
- Uses `src/utils/audit.py` to write the start and end records to DynamoDB.
- Uses `src/ingestion/bronze_writer.py` (which we already built!) to convert the parsed Delivery % DataFrame into Parquet and write it to the Bronze S3 bucket partitioned by date.

## Verification Plan
1. **Automated Tests:** Write `tests/ingestion/test_j02_delivery.py` mocking the NSE HTTP requests.
2. **Dry Run:** Run the `j02` script locally on a known past trading day to verify parsing logic.
3. **AWS Deployment:** Once finished, push to `main` so the GitHub Action deploys it to the EC2 instance automatically.
