import os
import json
import boto3
import requests
import yfinance as yf
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_yfinance_macro() -> dict:
    """
    Fetches latest close price for ^INDIAVIX and ^NSEI.
    """
    data = {}
    for ticker in ['^INDIAVIX', '^NSEI']:
        df = yf.Ticker(ticker).history(period='5d')
        if not df.empty:
            # Get the most recent close
            latest = df.iloc[-1]
            data[ticker] = {
                'close': float(latest['Close']),
                'date': latest.name.strftime('%Y-%m-%d')
            }
        else:
            raise ValueError(f"Failed to fetch data for {ticker}")
            
    return data

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_rbi_macro() -> str:
    """
    Scrapes the raw HTML from the RBI homepage to extract repo rate and bond yields.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get("https://www.rbi.org.in/", headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

def download_and_land_macro(date_str: str) -> dict:
    """
    Fetches yfinance macro and RBI HTML, saves to Landing S3, and returns URIs.
    """
    yf_data = fetch_yfinance_macro()
    rbi_html = fetch_rbi_macro()
    
    bucket_name = os.environ.get('S3_LANDING_BUCKET', 'project-intelligent-landing-307828758318')
    s3_client = boto3.client('s3', region_name='ap-south-1')
    
    # Save yfinance JSON
    yf_s3_key = f"yfinance/macro/date={date_str}/india_yf_macro.json"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=yf_s3_key,
        Body=json.dumps(yf_data).encode('utf-8')
    )
    
    # Save RBI HTML
    rbi_s3_key = f"rbi/macro/date={date_str}/homepage.html"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=rbi_s3_key,
        Body=rbi_html.encode('utf-8')
    )
    
    return {
        'yf_uri': f"s3://{bucket_name}/{yf_s3_key}",
        'rbi_uri': f"s3://{bucket_name}/{rbi_s3_key}"
    }
