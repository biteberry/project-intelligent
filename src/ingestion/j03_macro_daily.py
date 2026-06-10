import os
import sys
import argparse
import pandas as pd
import yfinance as yf
from datetime import datetime
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.ingestion.bronze_writer import write_dataframe_to_bronze
from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert

def run_j03(dry_run=False):
    job_id = "J03"
    now = datetime.utcnow()
    run_id = f"{job_id}_{now.strftime('%Y%m%d_%H%M%S')}"
    date_str = now.strftime('%Y-%m-%d')

    print(f"Starting {job_id} Macroeconomic Ingestion for {date_str}")

    symbols = ['GC=F', 'CL=F', 'INR=X']
    metrics = {
        "symbols_processed": len(symbols),
        "status": "STARTED"
    }

    try:
        print(f"Fetching macro symbols {symbols}...")
        df_raw = yf.download(symbols, period="1d", group_by="ticker", progress=False)
        
        if df_raw.empty:
            raise ValueError("yfinance returned an empty dataframe. Is the market open?")
            
        # Extract the most recent Close prices
        # We use .iloc[-1] to get the latest available price (handles weekends/holidays gracefully if period > 1d, but for 1d it gets today's)
        try:
            gold_usd = float(df_raw['GC=F']['Close'].iloc[-1])
            crude_usd = float(df_raw['CL=F']['Close'].iloc[-1])
            usd_inr = float(df_raw['INR=X']['Close'].iloc[-1])
        except KeyError as e:
            raise KeyError(f"Failed to extract symbol data from Yahoo Finance response: {e}")
            
        gold_inr = gold_usd * usd_inr
        
        # Create standard schema
        macro_df = pd.DataFrame({
            'date': [pd.to_datetime(date_str)],
            'gold_usd': [gold_usd],
            'crude_oil_usd': [crude_usd],
            'usd_inr': [usd_inr],
            'gold_inr': [gold_inr],
            'market_context': ['global'],
            'ingestion_run_id': [run_id],
            'ingestion_timestamp': [pd.Timestamp.utcnow()]
        })
        
        print("Calculated Macro Metrics:")
        print(macro_df[['date', 'gold_usd', 'crude_oil_usd', 'gold_inr']])
        
        if not dry_run:
            s3_path = write_dataframe_to_bronze(macro_df, table_name="macroeconomics")
            print(f"Successfully wrote macro data to {s3_path}")
        else:
            print(f"[DRY RUN] Would write 1 row to Bronze layer.")

        metrics["status"] = "SUCCESS"
        print(f"Job completed successfully.")
        if not dry_run:
            write_audit_record(run_id, job_id, "SUCCESS", metrics)

    except Exception as e:
        print(f"Critical Job Failure: {e}")
        traceback.print_exc()
        if not dry_run:
            write_audit_record(run_id, job_id, "FAILED", {"error": str(e)})
            publish_sns_alert(
                subject="J03 Critical Job Failure",
                message=f"Run {run_id} crashed entirely.\nError: {str(e)}"
            )
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="J03 Daily Macro Ingestion")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to S3")
    args = parser.parse_args()

    run_j03(dry_run=args.dry_run)
