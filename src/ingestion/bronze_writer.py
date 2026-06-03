import os
import io
import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

def write_to_bronze(df: pd.DataFrame, symbol: str, market_context: str, date_str: str, run_id: str) -> str:
    """
    Converts the pandas DataFrame to Parquet and writes it to the Bronze S3 bucket.
    Partitioning: s3://<bucket>/ohlcv/market_context=<ctx>/date=<date>/<symbol>.parquet
    """
    bucket_name = os.environ.get("BRONZE_BUCKET_NAME", "project-intelligent-bronze-307828758318")

    # Enrich the dataframe with context and run_id before writing
    df = df.copy()
    df["symbol"] = symbol
    df["market_context"] = market_context
    df["ingestion_run_id"] = run_id
    df["ingestion_timestamp"] = pd.Timestamp.utcnow()

    # Convert to PyArrow Table
    table = pa.Table.from_pandas(df)

    # Write Parquet to in-memory buffer
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression='SNAPPY')

    # Upload to S3
    s3_key = f"ohlcv/market_context={market_context}/date={date_str}/{symbol}.parquet"

    s3 = boto3.client('s3', region_name='ap-south-1')
    s3.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=buffer.getvalue()
    )

    return f"s3://{bucket_name}/{s3_key}"

def write_dataframe_to_bronze(df: pd.DataFrame, table_name: str, partition_cols: list = None) -> str:
    """
    Writes an entire dataframe to a single Parquet file in the Bronze S3 bucket.
    Currently hardcoded to extract market_context and append current UTC date to the S3 path.
    """
    bucket_name = os.environ.get("BRONZE_BUCKET_NAME", "project-intelligent-bronze-307828758318")
    date_str = pd.Timestamp.utcnow().strftime('%Y-%m-%d')
    
    ctx = df['market_context'].iloc[0] if 'market_context' in df.columns else 'default'
    s3_key = f"{table_name}/market_context={ctx}/date={date_str}/data.parquet"
    
    table = pa.Table.from_pandas(df)
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression='SNAPPY')
    
    s3 = boto3.client('s3', region_name='ap-south-1')
    s3.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=buffer.getvalue()
    )
    
    return f"s3://{bucket_name}/{s3_key}"
