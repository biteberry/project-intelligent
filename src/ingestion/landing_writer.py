import os
import io
import boto3
import pandas as pd
from datetime import datetime

def write_raw_csv_to_landing(df: pd.DataFrame, table_name: str, file_name: str = "raw_payload.csv") -> str:
    """
    Writes a pandas DataFrame as a raw CSV file to the Landing S3 bucket.
    Partitioning: s3://<bucket>/<table_name>/date=<YYYY-MM-DD>/<file_name>
    """
    bucket_name = os.environ.get("LANDING_BUCKET_NAME", "project-intelligent-landing-307828758318")
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Write CSV to in-memory buffer
    buffer = io.StringIO()
    df.to_csv(buffer)
    
    # Upload to S3
    s3_key = f"{table_name}/date={date_str}/{file_name}"
    
    s3 = boto3.client('s3', region_name='ap-south-1')
    s3.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=buffer.getvalue()
    )
    
    return f"s3://{bucket_name}/{s3_key}"

def write_raw_json_to_landing(json_data: str, table_name: str, file_name: str = "raw_payload.json") -> str:
    """
    Writes a raw JSON string to the Landing S3 bucket.
    Partitioning: s3://<bucket>/<table_name>/date=<YYYY-MM-DD>/<file_name>
    """
    bucket_name = os.environ.get("LANDING_BUCKET_NAME", "project-intelligent-landing-307828758318")
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    
    s3_key = f"{table_name}/date={date_str}/{file_name}"
    
    s3 = boto3.client('s3', region_name='ap-south-1')
    s3.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json_data
    )
    
    return f"s3://{bucket_name}/{s3_key}"
