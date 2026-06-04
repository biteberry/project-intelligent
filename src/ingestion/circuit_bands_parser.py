import pandas as pd
import io
import boto3

def _read_s3_csv(s3_uri: str) -> pd.DataFrame:
    bucket = s3_uri.split('/')[2]
    key = '/'.join(s3_uri.split('/')[3:])
    s3_client = boto3.client('s3', region_name='ap-south-1')
    response = s3_client.get_object(Bucket=bucket, Key=key)
    csv_string = response['Body'].read().decode('utf-8')
    return pd.read_csv(io.StringIO(csv_string))

def parse_circuit_bands(s3_uri: str, date_str: str) -> pd.DataFrame:
    """
    Parses the raw sec_list.csv from S3 into a cleaned Pandas DataFrame.
    Filters by the active universe inside the orchestrator.
    """
    df = _read_s3_csv(s3_uri)
    
    # Strip whitespace from column names just in case
    df.columns = df.columns.str.strip()
    
    # We only care about Symbol and Band
    df = df[['Symbol', 'Band']].copy()
    
    # Convert 'Band' column to actual numeric percentage.
    # NSE values: "2", "5", "10", "20", "No Band", "-"
    def clean_band(val):
        val_str = str(val).strip()
        if val_str.isdigit():
            return float(val_str) / 100.0
        return None  # No Band or invalid
        
    df['circuit_band'] = df['Band'].apply(clean_band)
    
    # Drop the original Band column
    df = df.drop(columns=['Band'])
    
    # Rename Symbol to symbol for consistency and append .NS suffix
    df = df.rename(columns={'Symbol': 'symbol'})
    df['symbol'] = df['symbol'] + '.NS'
    
    # Add metadata
    df['date'] = date_str
    df['market_context'] = 'india'
    df['source'] = 'nse_sec_list'
    
    return df
