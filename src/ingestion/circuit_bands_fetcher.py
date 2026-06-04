import os
import boto3
import requests

def download_circuit_bands(date_str: str) -> str:
    """
    Downloads the NSE security list (sec_list.csv) which contains the active 
    circuit bands for all NSE symbols. Saves it to the S3 Landing layer.
    """
    url = "https://nsearchives.nseindia.com/content/equities/sec_list.csv"
    
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    }
    
    print(f"Downloading NSE Circuit Bands from: {url}")
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Failed to download Circuit Bands for {date_str}. Status Code: {response.status_code}")
        
    raw_csv = response.content
    
    # Write to Landing Layer in S3
    bucket_name = os.environ.get('S3_LANDING_BUCKET', 'project-intelligent-landing-307828758318')
    s3_key = f"nse/circuit_bands/date={date_str}/sec_list.csv"
    
    s3_client = boto3.client('s3', region_name='ap-south-1')
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=raw_csv
    )
    
    s3_uri = f"s3://{bucket_name}/{s3_key}"
    return s3_uri
