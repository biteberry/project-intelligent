import os
import sys
import traceback
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert
from src.utils.universe import get_universe
from src.ingestion.circuit_bands_fetcher import download_circuit_bands
from src.ingestion.circuit_bands_parser import parse_circuit_bands
from src.ingestion.bronze_writer import write_dataframe_to_bronze

def main():
    job_id = "J08"
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    run_id = f"{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    print(f"Starting {job_id} NSE Circuit Bands Pipeline for {date_str}")
    
    metrics = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        india_universe = get_universe('india')
        
        # 1. Fetch
        s3_uri = download_circuit_bands(date_str)
        print(f"Downloaded sec_list.csv to {s3_uri}")
        
        # 2. Parse
        df = parse_circuit_bands(s3_uri, date_str)
        
        # 3. Filter to active universe
        df = df[df['symbol'].isin(india_universe)]
        
        # 4. Write to Bronze
        df['ingestion_timestamp'] = datetime.utcnow()
        df['ingestion_run_id'] = run_id
        
        s3_bronze_uri = write_dataframe_to_bronze(
            df=df,
            table_name="circuit_bands",
            partition_cols=['market_context']
        )
        
        print(f"Wrote {len(df)} circuit bands for INDIA to {s3_bronze_uri}")
        
        metrics["passed"] = len(india_universe)
        write_audit_record(run_id, job_id, "SUCCESS", metrics)
        
    except Exception as e:
        print(f"Failed to process circuit bands: {e}")
        traceback.print_exc()
        metrics["failed"] = 1
        metrics["errors"].append(str(e))
        
        write_audit_record(run_id, job_id, "FAILED", metrics, str(e))
        publish_sns_alert(
            subject=f"{job_id} Critical Failure",
            message=f"Run {run_id} failed.\nError: {str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
