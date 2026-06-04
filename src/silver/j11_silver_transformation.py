import os
import sys
import traceback
import duckdb
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert
from src.silver.iceberg_manager import write_arrow_to_iceberg

def execute_grand_join() -> 'pyarrow.Table':
    """
    Executes an in-memory DuckDB query to read all Bronze Parquet files,
    join them on symbol and date, and output a PyArrow Table.
    """
    bucket = os.environ.get("BRONZE_BUCKET_NAME", "project-intelligent-bronze-307828758318")
    s3_prefix = f"s3://{bucket}"
    
    con = duckdb.connect()
    
    # Set home directory to /tmp because SSM execution doesn't have $HOME
    con.execute("SET home_directory='/tmp';")
    
    # Load required extensions
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")
    con.execute("INSTALL aws;")
    con.execute("LOAD aws;")
    con.execute("CALL load_aws_credentials();")
    con.execute("SET s3_region='ap-south-1';")
    
    import boto3
    s3 = boto3.client('s3', region_name='ap-south-1')
    
    def has_files(prefix):
        res = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
        return 'Contents' in res and len(res['Contents']) > 0

    has_circuit = has_files('circuit_bands/')
    has_sentiment = has_files('sentiment/')
    has_delivery = has_files('delivery_pct/')
    
    # Base SELECT clauses
    select_clauses = [
        "o.symbol", "o.date", "o.open", "o.high", "o.low", "o.close", "o.volume",
        "o.market_context", "o.ingestion_run_id AS bronze_ohlcv_run_id"
    ]
    
    join_clauses = []
    
    if has_circuit:
        select_clauses.append("COALESCE(c.circuit_band, NULL) AS circuit_band")
        join_clauses.append(f"LEFT JOIN read_parquet('{s3_prefix}/circuit_bands/*/*/*.parquet') c ON o.symbol = c.symbol AND o.date = c.date")
    else:
        select_clauses.append("NULL AS circuit_band")
        
    if has_sentiment:
        select_clauses.extend([
            "COALESCE(s.sentiment_score, 0.0) AS sentiment_score",
            "COALESCE(s.sentiment_direction, 0) AS sentiment_direction",
            "COALESCE(s.news_intensity, 0) AS news_intensity",
            "COALESCE(s.news_coverage_flag, 'low') AS news_coverage_flag"
        ])
        join_clauses.append(f"LEFT JOIN read_parquet('{s3_prefix}/sentiment/*/*/*.parquet') s ON o.symbol = s.symbol AND o.date = s.fetch_date")
    else:
        select_clauses.extend([
            "0.0 AS sentiment_score",
            "0 AS sentiment_direction",
            "0 AS news_intensity",
            "'low' AS news_coverage_flag"
        ])
        
    if has_delivery:
        select_clauses.append("COALESCE(d.delivery_pct, 0.0) AS delivery_pct")
        join_clauses.append(f"LEFT JOIN read_parquet('{s3_prefix}/delivery_pct/*/*/*.parquet') d ON o.symbol = d.symbol AND o.date = d.date")
    else:
        select_clauses.append("0.0 AS delivery_pct")
        
    select_clauses.append("current_timestamp AS silver_ingestion_timestamp")
    
    query = f"SELECT {', '.join(select_clauses)} FROM read_parquet('{s3_prefix}/ohlcv/*/*/*.parquet') o " + " ".join(join_clauses)
    
    print(f"Executing dynamic DuckDB Grand Join...")
    arrow_table = con.execute(query).arrow()
    return arrow_table

def main():
    job_id = "J11"
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    run_id = f"{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    print(f"Starting {job_id} Silver Layer Transformation for {date_str}")
    
    metrics = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    try:
        # 1. Execute Join
        arrow_table = execute_grand_join()
        row_count = arrow_table.num_rows
        print(f"Grand Join completed. Yielded {row_count} rows.")
        
        if row_count == 0:
            print("No data found to process. Exiting gracefully.")
            write_audit_record(run_id, job_id, "SUCCESS", metrics)
            sys.exit(0)
            
        # 2. Append to Iceberg
        table_name = "ohlcv_enriched"
        full_table_name = write_arrow_to_iceberg(table_name, arrow_table)
        print(f"Successfully appended {row_count} rows to Iceberg table {full_table_name}")
        
        metrics["passed"] = row_count
        write_audit_record(run_id, job_id, "SUCCESS", metrics)
        
    except Exception as e:
        print(f"Failed to process Silver transformation: {e}")
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
