# Feature 12, 13, 14: The Gold Layer (Feature Engineering & Regime Detection)

This document outlines the implementation plan for **Issues 12, 13, and 14**. This phase represents the final data engineering transformation, converting the unified Silver timeline into a strictly validated, look-ahead-bias-free, Machine Learning ready dataset.

Because of the heavy compute required (rolling window calculations, MACD, RSI, candlestick patterns, and regime analysis), we will split the work into two dedicated jobs:
- **J13 (Market Regime Detection)**: Calculates the broad market trend (bull/bear/sideways) and volatility state to dictate ML strategy.
- **J12 (Feature Groups 1-10)**: Calculates all price, volume, volatility, technical, and risk features per symbol.

## Proposed Architecture & Tools

1. **Feature Engineering Library:** We will use **`pandas-ta`**. Building MACD, RSI, ATR, and Bollinger Bands from scratch in pure Python is error-prone. `pandas-ta` is an industry-standard library that integrates directly with Pandas DataFrames and computes these indicators robustly.
2. **Read/Write Engine:** We will use **DuckDB** to read the Silver data into a Pandas DataFrame, execute the feature engineering, and use **PyIceberg** to write the final dataset to `s3://project-intelligent-gold/features`.

## Implementation Steps

### 1. Dependency Updates
- Add `pandas-ta` to `requirements.txt` for technical analysis indicator generation.

### 2. Market Regime Detection (J13)
- **Create `src/gold/j13_market_regime.py`**:
  - Reads `india_vix`, `Nifty 50` (or `S&P 500`) from the Bronze/Silver tables.
  - Computes the 50-day SMA of the index and the 21-day average of the VIX.
  - Applies the 3-day stability buffer to assign one of 4 regimes: `bull_trend`, `bear_trend`, `sideways`, `high_vol`.
  - Writes the daily regime state to DynamoDB and to a Gold Regime Iceberg table.

### 3. Core Feature Engineering (J12)
- **Create `src/gold/j12_feature_engineering.py`**:
  - The master orchestrator for Groups 1-10.
  - Reads the entire `project_intelligent_silver.ohlcv_enriched` table via DuckDB into Pandas.
  - Groups the data by `symbol` and computes features sequentially to prevent data leakage.
  - **Group 1-2:** Compute 1d, 5d, 10d, 21d, 63d returns and rolling statistics (mean, std, skew).
  - **Group 3-5:** Use `pandas-ta` to compute RSI, MACD, Bollinger Bands, ATR, OBV, and MFI.
  - **Group 6-7:** Attach the regime label (from J13) and earnings/macro calendar variables.
  - **Group 8:** Implement custom logic to detect candlestick patterns (Hammers, Dojis, Engulfing) based on the PRD geometry rules.
  - **Group 9-10:** Forward-fill quarterly institutional ownership and Indian Regulatory Risk flags (circuit breakers, pledging).

### 4. Gold Iceberg Metastore Updates
- **Rename `src/silver/iceberg_manager.py` to `src/utils/iceberg_manager.py`**:
  - Since the Gold Layer also uses Apache Iceberg and the AWS Glue Catalog, we will move the `iceberg_manager.py` to `utils` so both Silver and Gold pipelines can share the same Glue Catalog creation logic, pointing the Gold data to `project_intelligent_gold`.

## Hardware Constraint Warning
The EC2 instance size (`t2.micro`) will struggle significantly with computing rolling MACD/RSI across millions of rows for 3000+ stocks in Pandas. 

**Recommendation:** For the initial "Historical Backfill", we should run this script locally on a developer machine, and push the completed Iceberg snapshot directly to AWS S3. Future daily incremental updates will be much smaller and can safely run on the EC2 instance.
