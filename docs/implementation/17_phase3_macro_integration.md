# Phase 3: Macroeconomic Indicator Integration

This plan outlines the architecture for bringing Gold and Crude Oil metrics into your Gold Layer to help the AI model contextualize the Indian stock market against global macroeconomic factors.

## Proposed Changes

### 1. New Bronze Ingestion (Node A)
We will create a new lightweight scraper to pull the global macroeconomic indicators daily.

#### [NEW] `src/ingestion/j03_macro_daily.py`
- Download the following symbols via Yahoo Finance:
  - `GC=F` (Gold Futures, USD)
  - `CL=F` (Crude Oil WTI Futures, USD)
  - `INR=X` (USD to INR Exchange Rate)
- Calculate `gold_inr` = `gold_usd_price * usd_inr_rate`.
- Write the flattened dataframe to a new Bronze partitioned path: `s3://.../macroeconomics/date=YYYY-MM-DD/data.parquet`.

#### [MODIFY] `.github/workflows/daily_ingestion.yml`
- Add a new GitHub Actions step to run `j03_macro_daily.py` on Node A right after `j02_delivery_pct_daily.py`.

### 2. Integrate into Silver Grand Join (Node B)
The macroeconomic data needs to be merged with the individual stock data so every stock row has the market's macro context for that specific day.

#### [MODIFY] `src/silver/j11_silver_transformation.py`
- Update the `execute_grand_join()` function to look for the `macroeconomics` Bronze data.
- Perform a `LEFT JOIN` on `o.date = m.date` (Note: since macro data is not symbol-specific, we join *only* on the date, meaning the same macro values will broadcast to every stock for that day).

### 3. Feature Engineering (Gold Layer)
The macro indicators need to be passed down into the final AI training table.

#### [MODIFY] `src/gold/j12_feature_engineering.py`
- Update the Silver Iceberg query to select the new macro columns (`gold_usd`, `gold_inr`, `crude_oil_usd`).
- Create 1-day percentage change metrics for the macro indicators (e.g., `gold_inr_return_1d`, `crude_return_1d`) so the ML model can detect macro velocity.

## Verification Plan
1. Run `j03_macro_daily.py` in dry-run mode to verify the math for `gold_inr`.
2. Run `j11` and assert that the macro columns broadcast correctly across all symbols for the day.
