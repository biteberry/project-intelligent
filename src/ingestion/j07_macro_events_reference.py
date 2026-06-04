import os
import sys
import yaml
import traceback
from datetime import datetime
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert
from src.ingestion.bronze_writer import write_dataframe_to_bronze

def main():
    job_id = "J07"
    run_id = f"{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    print(f"Starting {job_id} Macro Events Reference Pipeline")
    
    metrics = {
        "events_loaded": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../configs/india_macro_events.yaml'))
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
            
        events = data.get('events', [])
        
        if not events:
            print("No events found in configs/india_macro_events.yaml")
            write_audit_record(run_id, job_id, "SUCCESS", metrics)
            sys.exit(0)
            
        df = pd.DataFrame(events)
        df['ingestion_timestamp'] = datetime.utcnow()
        df['ingestion_run_id'] = run_id
        df['market_context'] = 'india'
        
        s3_bronze_uri = write_dataframe_to_bronze(
            df=df,
            table_name="macro_events_calendar",
            partition_cols=['market_context']
        )
        
        print(f"Successfully wrote {len(events)} macro events to {s3_bronze_uri}")
        
        metrics["events_loaded"] = len(events)
        write_audit_record(run_id, job_id, "SUCCESS", metrics)
        
    except Exception as e:
        print(f"Failed to process macro events calendar: {e}")
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
