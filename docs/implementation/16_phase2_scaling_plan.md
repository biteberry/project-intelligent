# Phase 2: Scaling & Enhancements

This plan outlines the technical steps to achieve the 3 new goals you outlined for Phase 2: scaling the universe to the full NSE market, appending sector metadata, and tracking newly listed stocks.

## User Review Required

> [!IMPORTANT]
> **Batch Size:** When fetching 2,400 stocks from Yahoo Finance, doing them all at exactly the same second can cause memory spikes. I propose fetching them in batches of 500 symbols at a time.
>
> **Sector Data Source:** Fetching "sector" metadata for 2,400 stocks from Yahoo Finance `info` is extremely slow. Instead, I propose creating a static CSV (`sectors_master.csv`) that maps the major domains, and loading it into the Silver layer for the join. We can manually populate the top 50, and everything else will default to `Others` as you requested. Let me know if you prefer a different source!

## Proposed Changes

### 1. Scale Universe (Bronze Layer)
Currently, `j01_ohlcv_daily.py` fetches symbols sequentially. We will refactor this to use multi-threaded bulk downloading.

#### [MODIFY] `src/utils/universe.py`
- Modify `get_universe()` to dynamically download the official `EQUITY_L.csv` from the NSE Archives (which contains all actively traded equities).
- Parse the `SYMBOL` column and append `.NS` to create the full Yahoo Finance ticker list (~2,400 symbols).

#### [MODIFY] `src/ingestion/j01_ohlcv_daily.py`
- Replace the sequential `for symbol in symbols:` loop with `yf.download(batch, group_by="ticker")`.
- Stack the multi-index dataframe to flatten it into our standard `(date, symbol, open, high, low, close, volume)` format.
- Write the entire flattened DataFrame to the Bronze layer in a single efficient operation.

### 2. Map Sector Metadata (Silver Layer)
We need to append `sector` and `industry` columns to the daily data so you can perform sector rotation strategies.

#### [NEW] `data/sectors_master.csv`
- A master reference file mapping `symbol` -> `sector`. (e.g., `TCS.NS` -> `IT`, `RELIANCE.NS` -> `Others`).

#### [MODIFY] `src/silver/j11_silver_transformation.py`
- Load the `sectors_master.csv` into a temporary DuckDB table.
- Perform a `LEFT JOIN` on the `ohlcv_enriched` table to append the `sector` column.
- Wrap the sector column in `COALESCE(sector, 'Others')` to ensure any unmapped stocks fallback to the default "Others" bucket.

### 3. Track Stock Lifecycle & New Listings (Gold Layer)
We need to flag any stock that has been listed within the last 30 days.

#### [NEW] `src/silver/j14_stock_lifecycle.py`
- Create a new Silver-level Slowly Changing Dimension (SCD) table called `stock_lifecycle`.
- Every day, it will scan the incoming Bronze data. If a symbol is completely new, it will record its `first_listed_date`.

#### [MODIFY] `src/gold/j12_feature_engineering.py`
- When generating features, `LEFT JOIN` the `stock_lifecycle` table.
- Calculate a new feature: `days_since_listed = (current_date - first_listed_date)`.
- Create the boolean flag: `is_new_listing = days_since_listed <= 30`.

## Verification Plan
### Automated Tests
1. Run a dry-run of `j01_ohlcv_daily.py` to ensure it successfully fetches 2,400 symbols from Yahoo Finance without crashing or timing out.
2. Run `j11_silver_transformation.py` and verify via DuckDB that unmapped stocks correctly have `sector = 'Others'`.
3. Run `j12_feature_engineering.py` and verify the `is_new_listing` flag correctly toggles to `True` for artificially inserted "new" symbols.
