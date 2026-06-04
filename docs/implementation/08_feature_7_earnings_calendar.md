# Feature #7: Earnings Calendar Ingestion (J06)

This plan addresses Issue #7 (Earnings Calendar Ingestion), which is critical for computing `days_to_next_earnings` and the `earnings_blackout_flag` serving gates in the downstream Silver layer.

We fetch earnings dates directly from Yahoo Finance without needing to build a complex, fragile web scraper for the NSE board meetings portal.

*(Note: While the issue title says "J03", we previously used J03 for Fundamentals, J04 for Corporate Actions, and J05 for Macro Data. I will name this pipeline **J06** to keep the pipeline numbering clean and sequential).*

## Proposed Changes

### 1. Requirements Update
#### [MODIFY] `requirements.txt`
- Add `lxml` so that the `yfinance` earnings dates parser functions correctly.
- Add `lxml` to `.github/workflows/weekly_batch.yml` install commands.

### 2. Ingestion Fetchers

#### [NEW] `src/ingestion/earnings_calendar_fetcher.py`
We will build a fetcher using `yfinance`. For a given ticker, calling `yfinance.Ticker(symbol).calendar` returns a dictionary containing `'Earnings Date': [datetime.date(...)]`. 
- The fetcher will loop through our active stock universe and extract the next upcoming earnings date.
- It will save the raw JSON payload to the Landing S3 Bucket (`s3://project-intelligent-landing/yfinance/earnings_calendar/`).

### 3. Ingestion Parser

#### [NEW] `src/ingestion/earnings_calendar_parser.py`
A parser that takes the raw `yfinance` calendar dictionary and flattens it into a schema suitable for Parquet storage.
Schema:
- `date`: The ingestion date.
- `symbol`: The stock ticker.
- `market_context`: e.g., 'india'.
- `next_earnings_date`: The upcoming earnings date as a string (YYYY-MM-DD).

### 4. Pipeline Orchestration

#### [NEW] `src/ingestion/j06_earnings_calendar_weekly.py`
The orchestrator script for the Earnings Calendar.
- Loads the universe using `src.utils.universe.get_universe()`.
- Iterates over all tickers to fetch the next earnings date.
- Writes the combined dataset to `s3://project-intelligent-bronze/earnings_calendar/market_context=.../`.

#### [MODIFY] `.github/workflows/weekly_batch.yml`
- We will insert `j06_earnings_calendar_weekly.py` into the weekly batch runner sequence, so it runs right alongside J03, J04, and J05 every Saturday.

## Verification Plan

### Automated Tests
- Explicitly test the `yfinance` calendar fetcher on the EC2 runner.

### Manual Verification
- Execute J06 on the EC2 instance via AWS SSM.
- Verify the output Parquet file in the Bronze S3 Bucket and ensure the schema matches our expectations.
