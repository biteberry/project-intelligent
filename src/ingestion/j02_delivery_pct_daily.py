import os
import sys
import traceback
from datetime import datetime

# Ensure the src directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.holidays import is_trading_day
from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert
from src.ingestion.bhav_copy_fetcher import download_bhav_copy
from src.ingestion.bhav_copy_parser import parse_delivery_pct
from src.ingestion.bronze_writer import write_dataframe_to_bronze

def main():
    job_id = "J02"
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    run_id = f"{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    print(f"Starting {job_id} Delivery % Ingestion Pipeline for {today_str}")

    # 1. Holiday Check
    if not is_trading_day(today_str, market='BSE'):
        print(f"{today_str} is a market holiday or weekend. Exiting gracefully.")
        write_audit_record(
            run_id=run_id,
            job_id=job_id,
            status="SKIPPED_HOLIDAY",
            metrics={"symbols_processed": 0}
        )
        return

    try:
        # 2. Fetch Raw CSV to Landing Layer
        s3_landing_uri = download_bhav_copy(today_str)

        # 3. Parse and Extract Delivery Percentage
        df = parse_delivery_pct(s3_landing_uri)

        num_symbols = len(df)
        print(f"Successfully extracted Delivery % for {num_symbols} equity symbols.")

        if num_symbols == 0:
            raise ValueError("No equity symbols found in the parsed Bhav Copy.")

        # Add metadata
        df['ingestion_timestamp'] = datetime.utcnow()

        # 4. Write to Bronze Layer
        # Add 'market_context' partition column required by the bronze writer
        df['market_context'] = 'india'

        s3_bronze_uri = write_dataframe_to_bronze(
            df=df,
            table_name="delivery_pct",
            partition_cols=['market_context'] # Date is automatically added by the writer
        )
        print(f"Successfully wrote Delivery % data to {s3_bronze_uri}")

        # 5. Audit Success
        write_audit_record(
            run_id=run_id,
            job_id=job_id,
            status="SUCCESS",
            metrics={
                "symbols_processed": num_symbols,
                "symbols_passed": num_symbols,
                "symbols_failed": 0
            }
        )

    except Exception as e:
        error_msg = f"Pipeline {job_id} failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)

        write_audit_record(
            run_id=run_id,
            job_id=job_id,
            status="FAILED",
            metrics={"symbols_processed": 0},
            error_message=str(e)
        )

        publish_sns_alert(
            subject=f"{job_id} Critical Job Failure",
            message=f"Run {run_id} crashed entirely.\nError: {str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
