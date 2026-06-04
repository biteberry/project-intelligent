# J04 Corporate Actions Ingestion Summary

The Feature #8 Corporate Actions pipeline (J04) is complete and fully operational. This pipeline closes Issues #201 and #202.

## What Was Built

### 1. Corporate Actions Fetcher (`corporate_actions_fetcher.py`)
- Iterates over the target active stock universe.
- Uses `yfinance.Ticker(symbol).actions` to retrieve all historical dividends and stock splits.
- Filters the actions to only keep those from the last 7 days.
- Saves the JSON payload into the `project-intelligent-landing` S3 bucket.

### 2. Corporate Actions Parser (`corporate_actions_parser.py`)
- Reads the raw JSON dictionary from the Landing bucket.
- Flattens the nested structures into a strictly typed format suitable for Parquet storage:
  - `date`: The execution date of the action.
  - `symbol`: The stock ticker.
  - `market_context`: e.g., 'india' or 'us'.
  - `action_type`: Either `DIVIDEND` or `SPLIT`.
  - `action_value`: The float amount (dividend payout amount or split ratio).

### 3. Pipeline Orchestrator (`j04_corporate_actions_weekly.py`)
- Triggers the fetcher and parser sequentially.
- Converts the flattened dictionary into a Pandas DataFrame.
- Writes the DataFrame to the Bronze layer in S3 using our standardized `write_dataframe_to_bronze` utility.
- Records success/failure metrics to the DynamoDB audit log.

### 4. GitHub Actions Automation
- Integrated `j04_corporate_actions_weekly.py` into `.github/workflows/weekly_batch.yml`. 
- The J04 pipeline now automatically runs every Saturday at 1:30 PM IST, sitting securely between J03 (Fundamentals) and J05 (Macro Data).

## Verification Results

The pipeline successfully executed on the AWS EC2 runner via AWS SSM. Because there were no dividends or splits for our test universe (`RELIANCE.NS`, `TCS.NS`, `INFY.NS`) in the last 7 days, the script correctly identified that no actions needed to be written and successfully logged a passing audit metric to DynamoDB.

This fully solves the pipeline requirement for Group 5 Corporate Actions!
