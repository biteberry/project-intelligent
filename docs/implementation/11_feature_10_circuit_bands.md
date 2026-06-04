# Feature #10: NSE Circuit Band Ingestion Summary (J08)

The Feature #10 NSE Circuit Band pipeline (J08) is complete and operational. This resolves Issue #10 and its child stories #204 and #205.

## What Was Built

### 1. Data Source Discovery
Instead of building a complex scraper or searching through disjointed daily archives, we identified that the NSE natively publishes the master active security list (`sec_list.csv`) which contains the `Band` column. This URL (`https://nsearchives.nseindia.com/content/equities/sec_list.csv`) can be accessed securely without rotating user agents or session cookies.

### 2. Circuit Bands Fetcher (`circuit_bands_fetcher.py`)
- Sends a GET request to the NSE archives for `sec_list.csv`.
- Saves the raw CSV file to the `project-intelligent-landing` S3 bucket.

### 3. Circuit Bands Parser (`circuit_bands_parser.py`)
- Reads the raw CSV file from S3 using Pandas.
- Filters out unnecessary columns, keeping only `Symbol` and `Band`.
- Cleans the `Band` values (e.g., "20", "5", "10", "-", "No Band") and converts valid numeric bands to floating-point percentages (e.g., `0.20`, `0.05`).
- Unrestricted stocks ("No Band") are cast to `None`/`NaN`.
- Renames columns to match the standard pipeline schema (`symbol`, `circuit_band`).

### 4. Pipeline Orchestrator (`j08_circuit_bands_weekly.py`)
- Executes the fetch and parse steps.
- **Filters the dataset:** It drops all generic NSE symbols and keeps ONLY the symbols that are currently part of our active `india` universe.
- Appends standard metadata (`ingestion_run_id`, `ingestion_timestamp`, `market_context='india'`).
- Writes the final cleaned DataFrame to the S3 Bronze layer using the standard `write_dataframe_to_bronze()` utility.
- Pushes success metrics to the DynamoDB audit table.

### 5. Automation
- Updated `.github/workflows/weekly_batch.yml` to trigger J08 as the final step in the weekend ingestion batch.

## Verification
The pipeline successfully executed on the AWS EC2 runner via AWS SSM. The `sec_list.csv` file was fetched, parsed successfully, filtered down to the active India universe, and the Parquet data was successfully written to the Bronze S3 Bucket. The audit record `J08_...` was written to DynamoDB.
