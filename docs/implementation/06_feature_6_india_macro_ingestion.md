# Feature #6: India Macro Data Ingestion (J05)

This document outlines the implementation plan for the J05 Macro Pipeline, which fetches critical macroeconomic indicators that drive the "Market Regime" features in the downstream Gold ML layer (Issues #214, #215, #216).

## Missing Data Sources (Open Questions)

> [!WARNING]  
> **Missing Data Sources for RBI & Bond Yields**
> A quick test using `yfinance` to check data availability revealed:
> - `^INDIAVIX` (India VIX) and `^NSEI` (Nifty 50) work perfectly.
> - **India 10Y/2Y Bond Yields and the RBI Repo Rate are NOT available in `yfinance`, Finnhub, or AlphaVantage.**
> 
> How should we handle the Bond Yields and RBI Repo Rate? 
> **Option A:** Temporarily drop them from the Bronze schema until we can find a reliable free API.
> **Option B:** Maintain a static `india_macro_static.csv` file in S3 that we update manually when the RBI changes rates.
> **Option C:** Use a specific API (like Quandl/Nasdaq Data Link) or a web-scraping script for the RBI portal.

## Proposed Changes

### 1. Ingestion Fetchers

#### [NEW] `src/ingestion/macro_fetcher.py`
We will create a generalized macro fetcher.
- It will use `yfinance.Ticker('^INDIAVIX').history()` to fetch the VIX.
- It will use `yfinance.Ticker('^NSEI').history()` to fetch the Nifty 50.
- It will save the raw payload to the S3 Landing Bucket under `s3://project-intelligent-landing/yfinance/macro/`.

### 2. Ingestion Parser

#### [NEW] `src/ingestion/macro_parser.py`
A parser that takes the raw macro data and flattens it into a daily time-series schema.
Schema:
- `date`
- `market_context` (e.g., `india`)
- `india_vix_close`
- `nifty50_close`
- *(Pending feedback on Repo Rate & Bond Yields)*

### 3. Pipeline Orchestration

#### [NEW] `src/ingestion/j05_macro_weekly.py`
The orchestrator script.
- Since macro indicators (like repo rate and general market trend) change slowly, we will run this weekly.
- It will use our `write_dataframe_to_bronze` batch writer to write the output to `s3://project-intelligent-bronze/macro/market_context=india/`.

#### [MODIFY] `.github/workflows/weekly_batch.yml`
- We will add the `j05_macro_weekly.py` execution step alongside the J03 and J04 jobs in our Saturday weekly batch runner.

## Verification Plan

### Automated Tests
- Structural checks using `pandas` and `tenacity` retries.

### Manual Verification
- We will manually trigger J05 via AWS SSM on the EC2 instance.
- We will inspect the resulting Parquet file in the Bronze S3 Bucket to ensure VIX and Nifty 50 data points are accurately captured and not stale.
