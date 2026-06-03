import os
import io
import boto3
import requests
from datetime import datetime

def download_bhav_copy(date_str: str) -> str:
    """
    Downloads the full bhav copy CSV from NSE for the given date.
    Writes the raw CSV directly to the Landing S3 bucket.
    
    Returns the S3 URI of the landed file.
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    date_formatted = dt.strftime("%d%m%Y")
    
    url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{date_formatted}.csv"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    print(f"Downloading NSE Bhav Copy from: {url}")
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Failed to download Bhav Copy for {date_str}. Status Code: {response.status_code}")
        
    raw_csv = response.content
    
    # Write to Landing Layer in S3
    bucket_name = os.environ.get('S3_LANDING_BUCKET', 'project-intelligent-landing-307828758318')
    s3_key = f"nse/bhav_copy/date={date_str}/sec_bhavdata_full_{date_formatted}.csv"
    
    s3_client = boto3.client('s3', region_name='ap-south-1')
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=raw_csv
    )
    
    s3_uri = f"s3://{bucket_name}/{s3_key}"
    print(f"Successfully saved raw Bhav Copy to {s3_uri}")
    return s3_uri
