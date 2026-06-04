# Feature #8: Corporate Actions Ingestion (J04)

Stock splits and dividends heavily skew historical pricing charts. To properly adjust historical prices in the Silver layer, we need to ingest this data via the J04 Pipeline (Issues #201, #202).

## Proposed Changes

### 1. Ingestion Fetchers

#### [NEW] `src/ingestion/corporate_actions_fetcher.py`
We will build a fetcher using `yfinance`. For a given ticker, calling `yfinance.Ticker(symbol).actions` returns a DataFrame containing historical **Dividends** and **Stock Splits**. We will fetch the actions for the last week for our entire active stock universe.
- Outputs the raw payload to the Landing S3 Bucket (`s3://project-intelligent-landing/yfinance/actions/`).

### 2. Ingestion Parser

#### [NEW] `src/ingestion/corporate_actions_parser.py`
A parser that takes the raw `yfinance` actions dataframe and flattens it into a strictly typed format suitable for Parquet storage.
Schema:
- `date`
- `symbol`
- `market_context` (india/us)
- `action_type` (either `DIVIDEND` or `SPLIT`)
- `action_value` (the float amount of the dividend or split ratio)

### 3. Pipeline Orchestration

#### [NEW] `src/ingestion/j04_corporate_actions_weekly.py`
The orchestrator script for Corporate Actions.
- Loads the universe using `src.utils.universe.get_universe()`.
- Iterates over all tickers to fetch recent corporate actions.
- Writes the combined, parsed dataset to `s3://project-intelligent-bronze/corporate_actions/market_context=.../`.

#### [MODIFY] `.github/workflows/weekly_batch.yml`
- We will insert `j04_corporate_actions_weekly.py` into the weekly batch runner sequence, so it runs right alongside the Fundamentals (J03) and Macro (J05) pipelines every Saturday.

## Verification Plan

### Automated Tests
- Explicitly run the fetcher against a stock known for heavy dividends/splits (e.g., `TCS.NS` or `RELIANCE.NS`) during our manual AWS SSM testing phase to ensure the parser handles the payload correctly.

### Manual Verification
- Execute J04 on the EC2 instance via AWS SSM.
- Verify the output Parquet file in the Bronze S3 Bucket and ensure the schema matches our expectations.
