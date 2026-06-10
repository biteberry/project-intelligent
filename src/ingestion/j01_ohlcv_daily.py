import os
import sys
import argparse
import pandas as pd
import yfinance as yf
from datetime import datetime
import traceback

# Adjust path for absolute imports when running directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.market_context import get_market_context
from src.ingestion.bronze_writer import write_dataframe_to_bronze
from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert
from src.utils.universe import get_universe

def run_j01(dry_run=False):
    job_id = "J01"
    now = datetime.utcnow()
    run_id = f"{job_id}_{now.strftime('%Y%m%d_%H%M%S')}"
    date_str = now.strftime('%Y-%m-%d')

    print(f"Starting {job_id} run: {run_id}")

    symbols = get_universe()
    metrics = {
        "symbols_processed": len(symbols),
        "symbols_passed": 0,
        "symbols_failed": 0
    }

    try:
        # Fetch all data in bulk
        print(f"Fetching OHLCV data for {len(symbols)} symbols in bulk...")
        # batching might be required if universe exceeds a certain size, but 2400 is fine for yfinance bulk download
        df_raw = yf.download(symbols, period="1d", group_by="ticker", threads=True, progress=False)
        
        if df_raw.empty:
            raise ValueError("yfinance returned an empty dataframe. Is the market open?")
            
        print("Data fetched. Flattening structure...")
        
        # Flatten multi-index
        df_flat = df_raw.stack(level=0, future_stack=True).reset_index()
        # Rename multi-index columns to standard names
        df_flat = df_flat.rename(columns={'Ticker': 'symbol', 'level_1': 'symbol', 'Date': 'date'})
        # Lowercase all standard column names (open, high, low, close, volume)
        df_flat.columns = [str(c).lower() for c in df_flat.columns]
        
        # Filter out rows with completely null OHLCV data
        df_flat = df_flat.dropna(subset=['open', 'high', 'low', 'close', 'volume'], how='all')
        
        if df_flat.empty:
            raise ValueError("All fetched data was empty/null. Exiting gracefully.")
            
        # Enrich metadata
        df_flat["market_context"] = df_flat["symbol"].apply(get_market_context)
        df_flat["ingestion_run_id"] = run_id
        df_flat["ingestion_timestamp"] = pd.Timestamp.utcnow()
        
        metrics["symbols_passed"] = df_flat['symbol'].nunique()
        metrics["symbols_failed"] = len(symbols) - metrics["symbols_passed"]
        
        print(f"Writing {len(df_flat)} rows to Bronze layer...")
        if not dry_run:
            # We partition by market context in case we have a mixed universe
            for ctx, group_df in df_flat.groupby("market_context"):
                s3_path = write_dataframe_to_bronze(group_df, table_name="ohlcv")
                print(f"  -> Written {ctx} context to {s3_path}")
        else:
            print(f"  -> [DRY RUN] Would write {len(df_flat)} rows.")

        print(f"Job completed with status: SUCCESS. Metrics: {metrics}")
        if not dry_run:
            write_audit_record(run_id, job_id, "SUCCESS", metrics)

    except Exception as e:
        print(f"Critical Job Failure: {e}")
        traceback.print_exc()
        if not dry_run:
            write_audit_record(run_id, job_id, "FAILED", {"error": str(e)})
            publish_sns_alert(
                subject="J01 Critical Job Failure",
                message=f"Run {run_id} crashed entirely.\nError: {str(e)}"
            )
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="J01 Daily OHLCV Ingestion")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to S3 or DynamoDB")
    args = parser.parse_args()

    run_j01(dry_run=args.dry_run)
