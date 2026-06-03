import os
import sys
import traceback
from datetime import datetime
import pandas as pd

# Ensure the src directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.universe import get_universe, get_market_context
from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert
from src.ingestion.fundamentals_fetcher import download_and_land_fundamentals
from src.ingestion.fundamentals_parser import parse_fundamentals
from src.ingestion.bronze_writer import write_dataframe_to_bronze

def main():
    job_id = "J03"
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    run_id = f"{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    print(f"Starting {job_id} Fundamentals Ingestion Pipeline for {date_str}")
    
    symbols = get_universe()
    parsed_records = []
    
    metrics = {
        "symbols_processed": len(symbols),
        "symbols_passed": 0,
        "symbols_failed": 0,
        "failed_symbols": []
    }
    
    for symbol in symbols:
        try:
            print(f"Processing {symbol}...")
            # 1. Fetch & Land
            s3_landing_uri = download_and_land_fundamentals(symbol, date_str)
            
            # 2. Parse
            record = parse_fundamentals(s3_landing_uri, symbol)
            
            # Add metadata
            record['market_context'] = get_market_context(symbol)
            record['ingestion_timestamp'] = datetime.utcnow()
            
            parsed_records.append(record)
            metrics["symbols_passed"] += 1
            
        except Exception as e:
            print(f"  -> Failed to process {symbol}: {e}")
            metrics["symbols_failed"] += 1
            metrics["failed_symbols"].append(symbol)
            
    if len(parsed_records) == 0:
        print("No fundamentals were successfully parsed. Exiting.")
        write_audit_record(run_id, job_id, "FAILED", metrics, "No fundamentals fetched")
        sys.exit(1)
        
    df = pd.DataFrame(parsed_records)
    
    # 3. Write to Bronze (Split by market_context to handle the writer correctly)
    for ctx, group_df in df.groupby('market_context'):
        s3_bronze_uri = write_dataframe_to_bronze(
            df=group_df,
            table_name="fundamentals",
            partition_cols=['market_context']
        )
        print(f"Successfully wrote {ctx} Fundamentals data to {s3_bronze_uri}")
        
    # 4. Audit Success
    status = "SUCCESS" if metrics["symbols_failed"] == 0 else "PARTIAL_SUCCESS"
    write_audit_record(run_id, job_id, status, metrics)
    
    if status == "PARTIAL_SUCCESS":
        publish_sns_alert(
            subject=f"{job_id} Partial Success",
            message=f"Run {run_id} completed with {metrics['symbols_failed']} failures.\nFailed: {metrics['failed_symbols']}"
        )

if __name__ == "__main__":
    main()
