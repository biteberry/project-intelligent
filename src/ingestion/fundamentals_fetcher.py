import os
import json
import boto3
import yfinance as yf
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_raw_fundamentals(symbol: str) -> dict:
    """
    Fetches raw fundamentals dictionary from yfinance using the .info property.
    Uses tenacity for exponential backoff retries.
    """
    ticker = yf.Ticker(symbol)
    info = ticker.info
    
    if not info or len(info) <= 5: # yfinance sometimes returns an almost empty dict on failure
        raise ValueError(f"Empty or incomplete fundamentals returned for symbol {symbol}")
        
    return info

def download_and_land_fundamentals(symbol: str, date_str: str) -> str:
    """
    Downloads fundamentals for the symbol and saves the raw JSON to the Landing S3 bucket.
    Returns the S3 URI.
    """
    info = fetch_raw_fundamentals(symbol)
    
    # Serialize to JSON string safely (some yfinance objects might need coercion, though .info is usually flat)
    raw_json = json.dumps(info, default=str)
    
    # Write to Landing Layer in S3
    bucket_name = os.environ.get('S3_LANDING_BUCKET', 'project-intelligent-landing-307828758318')
    s3_key = f"yfinance/fundamentals/date={date_str}/{symbol}.json"
    
    s3_client = boto3.client('s3', region_name='ap-south-1')
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=raw_json.encode('utf-8')
    )
    
    s3_uri = f"s3://{bucket_name}/{s3_key}"
    return s3_uri
