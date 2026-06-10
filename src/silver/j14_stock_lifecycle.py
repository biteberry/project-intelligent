import os
import sys
import traceback
import duckdb
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.audit import write_audit_record
from src.utils.alerts import publish_sns_alert
from src.utils.iceberg_manager import write_arrow_to_iceberg

def execute_lifecycle_update() -> 'pyarrow.Table':
    """
    Scans the Silver ohlcv_enriched table to find the earliest date
    each symbol was seen. This builds our Slowly Changing Dimension (SCD)
    table for stock lifecycles.
    """
    con = duckdb.connect()
    
    # Set home directory to /tmp because SSM execution doesn't have $HOME
    con.execute("SET home_directory='/tmp';")
    
    # Load required extensions for Iceberg
    con.execute("INSTALL iceberg;")
    con.execute("LOAD iceberg;")
    con.execute("INSTALL aws;")
    con.execute("LOAD aws;")
    con.execute("CALL load_aws_credentials();")
    con.execute("SET s3_region='ap-south-1';")
    
    # Read the Silver table to find the min date per symbol
    query = """
    SELECT 
        symbol,
        MIN(date) AS first_listed_date,
        CAST(current_timestamp AS TIMESTAMP) AS last_updated_timestamp
    FROM iceberg_scan('s3://project-intelligent-silver-307828758318/ohlcv_enriched', allow_moved_paths=true)
    GROUP BY symbol
    """
    
    print("Computing stock lifecycle aggregations from Silver layer...")
    arrow_table = con.execute(query).fetch_arrow_table()
    return arrow_table

def main():
    job_id = "J14"
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    run_id = f"{job_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    print(f"Starting {job_id} Stock Lifecycle tracking for {date_str}")
    
    metrics = {
        "symbols_tracked": 0,
        "failed": 0
    }
    
    try:
        arrow_table = execute_lifecycle_update()
        row_count = arrow_table.num_rows
        print(f"Aggregated lifecycle data. Yielded {row_count} symbols.")
        
        if row_count == 0:
            print("No data found to process. Exiting gracefully.")
            write_audit_record(run_id, job_id, "SUCCESS", metrics)
            sys.exit(0)
            
        # Overwrite the Iceberg table (we recalculate the min date every run to catch historical backfills)
        # We can use our write_arrow_to_iceberg function. Since it appends by default, we'll need to overwrite
        # the iceberg_manager.py or write a custom overwrite logic here.
        # Wait, iceberg_manager currently appends. If we run this daily, we will duplicate records.
        # We must overwrite the table.
        # Let's import pyiceberg directly to overwrite.
        from pyiceberg.catalog import load_catalog
        import pyarrow as pa
        
        catalog = load_catalog(
            "default",
            **{
                "type": "glue",
                "s3.region": "ap-south-1",
                "downcast-ns-timestamp-to-us-on-write": "true"
            }
        )
        
        table_name = "project_intelligent_silver.stock_lifecycle"
        print(f"Overwriting Iceberg table: {table_name}")
        
        try:
            iceberg_table = catalog.load_table(table_name)
            iceberg_table.overwrite(arrow_table)
        except Exception as e:
            if "EntityNotFoundException" in str(e):
                print(f"Table does not exist. Creating {table_name}...")
                iceberg_table = catalog.create_table(
                    table_name,
                    schema=arrow_table.schema,
                    location=f"s3://project-intelligent-silver-307828758318/{table_name.split('.')[1]}"
                )
                iceberg_table.append(arrow_table)
            else:
                raise e

        print(f"Successfully wrote {row_count} rows to Iceberg table {table_name}")
        
        metrics["symbols_tracked"] = row_count
        write_audit_record(run_id, job_id, "SUCCESS", metrics)
        
    except Exception as e:
        print(f"Failed to process Stock Lifecycle: {e}")
        traceback.print_exc()
        metrics["failed"] = 1
        
        write_audit_record(run_id, job_id, "FAILED", metrics, str(e))
        publish_sns_alert(
            subject=f"{job_id} Critical Failure",
            message=f"Run {run_id} failed.\nError: {str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
