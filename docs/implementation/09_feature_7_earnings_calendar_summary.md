# Feature #7: Earnings Calendar Ingestion Summary (J06)

The Feature #7 Earnings Calendar pipeline (J06) is complete and fully operational. This resolves Issue #7 and its child stories #217 and #218.

## What Was Built

### 1. Requirements Optimization
- Switched the architecture to use `yfinance.Ticker().calendar` instead of building a fragile web scraper for the NSE corporate filings portal.
- Added `lxml` to `requirements.txt` to enable the underlying pandas HTML parser used by yfinance's earnings API.

### 2. Earnings Calendar Fetcher (`earnings_calendar_fetcher.py`)
- Loops over the active universe.
- Checks `Ticker(symbol).calendar['Earnings Date']` and computes the **nearest upcoming earnings date** (ignoring past dates).
- Saves a compressed JSON payload to the `project-intelligent-landing` S3 bucket.

### 3. Earnings Calendar Parser (`earnings_calendar_parser.py`)
- Reads the raw JSON dictionary from the Landing bucket.
- Flattens the nested structures into a Bronze-ready tabular format:
  - `date`: The execution date.
  - `symbol`: The stock ticker.
  - `market_context`: e.g., 'india'.
  - `next_earnings_date`: The upcoming earnings date as a string (YYYY-MM-DD).

### 4. Pipeline Orchestrator (`j06_earnings_calendar_weekly.py`)
- Triggers the fetcher and parser sequentially.
- Converts the flattened dictionary into a Pandas DataFrame.
- Writes the DataFrame to the Bronze layer in S3 via the shared `write_dataframe_to_bronze` utility.
- Records metrics directly to the DynamoDB audit log.

### 5. Automation & Architecture Updates
- Updated the **PRD** and **Data Ingestion Architecture** docs to officially recognize Yahoo Finance as the data source for earnings calendars.
- Added the `j06_earnings_calendar_weekly.py` script to the EC2 orchestration sequence in `.github/workflows/weekly_batch.yml`. It now runs natively alongside J03, J04, and J05 every Saturday.

## Verification Results

The pipeline successfully executed on the AWS EC2 runner via AWS SSM. The `lxml` dependency installed correctly, the scraper fetched successfully without throwing XML parsing errors, and the audit logs correctly reported back passing metrics to DynamoDB!
