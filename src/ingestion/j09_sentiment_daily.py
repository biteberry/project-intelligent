import os
import sys
import traceback
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert
from src.utils.universe import get_universe, get_market_context
from src.ingestion.sentiment_fetcher import fetch_sentiment_for_symbols
from src.ingestion.sentiment_parser import parse_sentiment
from src.ingestion.bronze_writer import write_dataframe_to_bronze

def main():
    job_id = "J09"
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    run_id = f"{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    print(f"Starting {job_id} Finnhub Sentiment Pipeline for {date_str}")
    
    metrics = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        india_universe = get_universe('india')
        us_universe = get_universe('us')
        combined_universe = india_universe + us_universe
        
        if not combined_universe:
            print("No symbols found in active universe.")
            write_audit_record(run_id, job_id, "SUCCESS", metrics)
            sys.exit(0)
        
        # 1. Fetch
        s3_uri = fetch_sentiment_for_symbols(combined_universe, date_str)
        print(f"Downloaded Finnhub sentiment to {s3_uri}")
        
        # 2. Parse
        df = parse_sentiment(s3_uri)
        
        # 3. Add context and write
        df['fetch_date'] = date_str
        df['ingestion_timestamp'] = datetime.utcnow()
        df['ingestion_run_id'] = run_id
        df['market_context'] = df['symbol'].apply(get_market_context)
        
        if len(df) > 0:
            s3_bronze_uri = write_dataframe_to_bronze(
                df=df,
                table_name="sentiment",
                partition_cols=['market_context']
            )
            print(f"Wrote {len(df)} sentiment records to {s3_bronze_uri}")
        
        metrics["passed"] = len(df)
        write_audit_record(run_id, job_id, "SUCCESS", metrics)
        
    except Exception as e:
        print(f"Failed to process sentiment data: {e}")
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
