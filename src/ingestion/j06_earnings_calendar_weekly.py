import os
import sys
import traceback
from datetime import datetime
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert
from src.utils.universe import get_universe
from src.ingestion.earnings_calendar_fetcher import fetch_earnings_calendar
from src.ingestion.earnings_calendar_parser import parse_earnings_calendar
from src.ingestion.bronze_writer import write_dataframe_to_bronze

def process_market(market_context: str, date_str: str) -> dict:
    print(f"Processing Earnings Calendar for {market_context.upper()} market...")
    universe = get_universe(market_context)
    
    # 1. Fetch
    s3_uri = fetch_earnings_calendar(universe, date_str)
    
    # 2. Parse
    records = parse_earnings_calendar(s3_uri, market_context, date_str)
    
    if not records:
        print(f"No upcoming earnings found for {market_context}.")
        return {"passed": len(universe), "failed": 0, "calendars_found": 0}
        
    # 3. Write to Bronze
    df = pd.DataFrame(records)
    df['ingestion_timestamp'] = datetime.utcnow()
    
    s3_bronze_uri = write_dataframe_to_bronze(
        df=df,
        table_name="earnings_calendar",
        partition_cols=['market_context']
    )
    
    print(f"Wrote {len(records)} earnings calendar dates for {market_context} to {s3_bronze_uri}")
    return {"passed": len(universe), "failed": 0, "calendars_found": len(records)}

def main():
    job_id = "J06"
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    run_id = f"{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    print(f"Starting {job_id} Earnings Calendar Pipeline for {date_str}")
    
    metrics = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        india_metrics = process_market("india", date_str)
        metrics["passed"] += india_metrics["passed"]
        metrics["failed"] += india_metrics["failed"]
        
        # Extensible for US context later
        
        write_audit_record(run_id, job_id, "SUCCESS", metrics)
        
    except Exception as e:
        print(f"Failed to process earnings calendar: {e}")
        traceback.print_exc()
        metrics["failed"] += 1
        metrics["errors"].append(str(e))
        
        write_audit_record(run_id, job_id, "FAILED", metrics, str(e))
        publish_sns_alert(
            subject=f"{job_id} Critical Failure",
            message=f"Run {run_id} failed.\nError: {str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
