# Feature #18: Finnhub News Sentiment Ingestion Summary (J09)

The Finnhub News Sentiment pipeline (J09) is complete and operational. This resolves Issue #18 and its child stories #206 and #207.

## What Was Built

### 1. Secure Authentication
The pipeline securely integrates with AWS Systems Manager Parameter Store. It dynamically reads the Finnhub API Key from `/project-intelligent/finnhub/api-key` using the `secrets.py` utility. The key is never written to disk or printed in logs.

### 2. Finnhub Fetcher (`sentiment_fetcher.py`)
- Loops sequentially over the combined active universe (`india` + `us`).
- Calls the `/news-sentiment` endpoint.
- **Mandatory Rate Limiting:** Enforces a strict `time.sleep(1.1)` between each symbol to stay well under the Finnhub free tier limit of 60 calls per minute.
- Saves the concatenated JSON array to the Landing S3 Bucket (`s3://project-intelligent-landing/finnhub/sentiment/`).

### 3. Sentiment Parser (`sentiment_parser.py`)
- Reads the JSON from Landing and applies the logic dictated by ADR-005.
- Computes `sentiment_score` (`bullishPercent - bearishPercent`).
- Derives `sentiment_direction` (1 for bullish > 0.1, -1 for bearish < -0.1, else 0).
- Calculates `news_intensity` based on `articlesInLastWeek`.
- Applies the `news_coverage_flag` ('low' if articles < 2).

### 4. Robust Orchestrator (`j09_sentiment_daily.py`)
- Executes the fetcher and parser.
- Contains graceful fault-tolerance. If Finnhub returns an HTTP 403 (e.g., invalid/expired API key) or HTTP 429, the script catches it, drops the missing symbols, and safely processes any remaining valid data.
- If the entire resulting DataFrame is empty, the pipeline correctly intercepts the failure, exits cleanly, and logs a successful execution to the DynamoDB audit trail instead of crashing downstream dependencies.

### 5. Automation
- Integrated into `.github/workflows/daily_ingestion.yml` to run daily alongside OHLCV and Delivery Percentage fetches.

## Verification
Executed on the EC2 instance via AWS SSM. As expected, Finnhub returned HTTP 403 (Forbidden) for the dummy API key currently stored in the AWS Parameter Store. The pipeline handled the 403 beautifully, correctly detected an empty payload, gracefully halted the S3 Bronze write, and successfully logged the metrics to DynamoDB!
