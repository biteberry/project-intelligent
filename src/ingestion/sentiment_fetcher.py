import os
import sys
import time
import json
import boto3
import requests
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.utils.secrets import get_secret

def fetch_sentiment_for_symbols(symbols: list, date_str: str) -> str:
    """
    Iterates through a list of symbols, calls Finnhub /news-sentiment endpoint,
    respects the 60 calls/minute rate limit, and saves the consolidated JSON 
    to the Landing S3 Bucket.
    """
    api_key = get_secret('/project-intelligent/finnhub/api-key')
    
    results = []
    
    print(f"Fetching Finnhub Sentiment for {len(symbols)} symbols...")
    
    for symbol in symbols:
        # Note: Finnhub primarily uses US tickers without suffixes.
        # But we must support India too. We will pass the exact symbol string.
        # Finnhub handles .NS for Indian stocks.
        url = f"https://finnhub.io/api/v1/news-sentiment?symbol={symbol}&token={api_key}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Attach our symbol back so we know which it belongs to
                data['requested_symbol'] = symbol
                results.append(data)
            else:
                print(f"Warning: Finnhub returned {response.status_code} for {symbol}")
        except Exception as e:
            print(f"Error fetching sentiment for {symbol}: {e}")
            
        # Mandatory rate limiting: 60 calls per min -> 1 second sleep
        time.sleep(1.1)

    # Write the entire consolidated list to Landing Layer in S3
    bucket_name = os.environ.get('S3_LANDING_BUCKET', 'project-intelligent-landing-307828758318')
    s3_key = f"finnhub/sentiment/date={date_str}/sentiment.json"
    
    s3_client = boto3.client('s3', region_name='ap-south-1')
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(results)
    )
    
    s3_uri = f"s3://{bucket_name}/{s3_key}"
    return s3_uri
