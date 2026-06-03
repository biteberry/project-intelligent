import pandas as pd
import io
import boto3

def parse_delivery_pct(s3_uri: str) -> pd.DataFrame:
    """
    Reads the raw Bhav Copy CSV from Landing S3.
    Filters for Series == 'EQ' (Equity).
    Extracts the 'SYMBOL' and 'DELIV_PER' columns.
    Returns a cleaned Pandas DataFrame.
    """
    # Parse bucket and key from s3://bucket/key
    bucket = s3_uri.split('/')[2]
    key = '/'.join(s3_uri.split('/')[3:])

    s3_client = boto3.client('s3', region_name='ap-south-1')
    response = s3_client.get_object(Bucket=bucket, Key=key)
    csv_content = response['Body'].read()

    # Read CSV into DataFrame
    # Note: NSE CSVs often have trailing spaces in column names
    df = pd.read_csv(io.BytesIO(csv_content), skipinitialspace=True)

    # Clean column names (strip whitespace)
    df.columns = df.columns.str.strip()

    # Filter for Equity series only
    if 'SERIES' in df.columns:
        df = df[df['SERIES'] == 'EQ']

    # Check for delivery percentage column (it can be named 'DELIV_PER' or 'DELIV_QTY' depending on format)
    deliv_col = 'DELIV_PER'
    if deliv_col not in df.columns:
        if 'DELIV_QTY' in df.columns:
            # We would need total traded quantity to calculate it, but let's assume standard format for now
            raise ValueError(f"Could not find '{deliv_col}' in columns: {df.columns}")
        else:
            raise ValueError(f"Could not find Delivery Data in columns: {df.columns}")

    # Extract only needed columns
    result_df = df[['SYMBOL', deliv_col]].copy()

    # Rename columns to standard schema
    result_df.rename(columns={
        'SYMBOL': 'symbol',
        deliv_col: 'delivery_pct'
    }, inplace=True)

    # Clean data types
    result_df['delivery_pct'] = pd.to_numeric(result_df['delivery_pct'], errors='coerce')

    # Append .NS for Yahoo Finance compatibility downstream if needed, or leave as is
    result_df['symbol'] = result_df['symbol'] + '.NS'

    return result_df
