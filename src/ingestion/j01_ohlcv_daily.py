import os
import sys
import argparse
from datetime import datetime

# Adjust path for absolute imports when running directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.market_context import get_market_context
from src.ingestion.fetcher import fetch_daily_ohlcv
from src.ingestion.bronze_writer import write_to_bronze
from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert

def get_universe():
    """
    Mock function to return active universe of symbols.
    In a real scenario, this would read from DynamoDB or a static config.
    """
    return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "AAPL", "MSFT"]

def run_j01(dry_run=False):
    job_id = "J01"
    now = datetime.utcnow()
    run_id = f"{job_id}_{now.strftime('%Y%m%d_%H%M%S')}"
    date_str = now.strftime('%Y-%m-%d')
    
    print(f"Starting {job_id} run: {run_id}")
    
    symbols = get_universe()
    metrics = {
        "symbols_processed": 0,
        "symbols_passed": 0,
        "symbols_failed": 0,
        "failed_symbols": []
    }
    
    metrics["symbols_processed"] = len(symbols)
    
    try:
        for symbol in symbols:
            print(f"Processing {symbol}...")
            try:
                # 1. Determine context
                ctx = get_market_context(symbol)
                
                # 2. Fetch data (with retries)
                df = fetch_daily_ohlcv(symbol)
                
                # 3. Write to Bronze
                if not dry_run:
                    s3_path = write_to_bronze(df, symbol, ctx, date_str, run_id)
                    print(f"  -> Written to {s3_path}")
                else:
                    print(f"  -> [DRY RUN] Would write {len(df)} rows for {symbol}")
                
                metrics["symbols_passed"] += 1
                
            except Exception as e:
                print(f"  -> Failed: {e}")
                metrics["symbols_failed"] += 1
                metrics["failed_symbols"].append(symbol)
                # Alert for individual symbol failure
                if not dry_run:
                    publish_sns_alert(
                        subject=f"J01 Symbol Failure: {symbol}",
                        message=f"Run {run_id} failed to fetch OHLCV for {symbol} after all retries.\nError: {str(e)}"
                    )
        
        status = "SUCCESS" if metrics["symbols_failed"] == 0 else "PARTIAL_SUCCESS"
        if metrics["symbols_failed"] == len(symbols):
            status = "FAILED"
            
        print(f"Job completed with status: {status}. Metrics: {metrics}")
        if not dry_run:
            write_audit_record(run_id, job_id, status, metrics)
            
    except Exception as e:
        print(f"Critical Job Failure: {e}")
        if not dry_run:
            write_audit_record(run_id, job_id, "FAILED", {"error": str(e)})
            publish_sns_alert(
                subject=f"J01 Critical Job Failure",
                message=f"Run {run_id} crashed entirely.\nError: {str(e)}"
            )
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="J01 Daily OHLCV Ingestion")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing to S3 or DynamoDB")
    args = parser.parse_args()
    
    run_j01(dry_run=args.dry_run)
