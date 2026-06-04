import os
import sys
import traceback
from datetime import datetime
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert
from src.ingestion.macro_fetcher import download_and_land_macro
from src.ingestion.macro_parser import parse_macro
from src.ingestion.bronze_writer import write_dataframe_to_bronze

def main():
    job_id = "J05"
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    run_id = f"{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    print(f"Starting {job_id} India Macro Data Ingestion Pipeline for {date_str}")
    
    metrics = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        # 1. Fetch & Land
        print("Fetching yfinance and RBI macro indicators...")
        s3_uris = download_and_land_macro(date_str)
        
        # 2. Parse
        print("Parsing HTML and JSON payloads...")
        record = parse_macro(date_str, s3_uris)
        record['ingestion_timestamp'] = datetime.utcnow()
        
        print("Extracted Macro Record:")
        print(record)
        
        # Check if critical data is missing
        if record['rbi_repo_rate'] is None or record['nifty50_close'] is None:
            raise ValueError("Critical macro data missing from parsed record.")
            
        metrics["passed"] = 1
        
        # 3. Write to Bronze
        df = pd.DataFrame([record])
        
        s3_bronze_uri = write_dataframe_to_bronze(
            df=df,
            table_name="macro",
            partition_cols=['market_context']
        )
        print(f"Successfully wrote India Macro data to {s3_bronze_uri}")
        
        # 4. Audit Success
        write_audit_record(run_id, job_id, "SUCCESS", metrics)
        
    except Exception as e:
        print(f"Failed to process macro data: {e}")
        traceback.print_exc()
        metrics["failed"] = 1
        metrics["errors"].append(str(e))
        
        write_audit_record(run_id, job_id, "FAILED", metrics, str(e))
        publish_sns_alert(
            subject=f"{job_id} Critical Failure",
            message=f"Run {run_id} failed to fetch India Macro data.\nError: {str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
