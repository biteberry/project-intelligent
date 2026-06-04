# J05 India Macro Data Ingestion Summary

The Feature #6 India Macro Data pipeline (J05) is completely finished and fully operational leveraging live Web Scraping against the RBI portal.

## What Was Built

### 1. Robust Macro Fetcher (`macro_fetcher.py`)
- We used `yfinance` to pull the latest closing values for **India VIX (`^INDIAVIX`)** and the **Nifty 50 (`^NSEI`)**.
- We wrote a custom Python scraping function that hits the Reserve Bank of India (RBI) homepage (`https://www.rbi.org.in/`) using a disguised User-Agent to retrieve the raw HTML payload.
- Both the JSON and HTML payloads are stored cleanly in the `project-intelligent-landing` S3 bucket.

### 2. Intelligent HTML Parser (`macro_parser.py`)
- We used `BeautifulSoup4` to scan the raw RBI HTML for the specific tables containing the macroeconomic rates.
- The parser intelligently hunts for "Policy Repo Rate" and "GS 203x" strings to dynamically extract the exact interest rate and 10-year bond yields, isolating us from minor layout changes on the RBI portal.

### 3. J05 Orchestrator & Batch Automation (`j05_macro_weekly.py`)
- The Python script triggers the fetcher and parser, constructs the Medallion `record`, and uses our batch Parquet writer to land the data in the Bronze layer.
- I refactored the GitHub Actions workflow from `weekly_fundamentals.yml` to **`weekly_batch.yml`**. Moving forward, every Saturday at 1:30 PM IST, the EC2 instance will sequentially run both J03 (Fundamentals) and J05 (India Macro).

## Verification Results

The pipeline successfully executed on the AWS EC2 runner. Here is the exact data point that was scraped, parsed, and saved to the Parquet dataset:

```json
{
  "date": "2026-06-04",
  "market_context": "india",
  "india_vix_close": 16.17,
  "nifty50_close": 23408.59,
  "rbi_repo_rate": 5.25,
  "india_10y_yield": 7.3293
}
```

This perfectly solves the pipeline requirement for Group 6 Market Regime features without relying on static files or paid APIs.
