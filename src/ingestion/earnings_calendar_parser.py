import json
import boto3
from typing import List

def _read_s3_object(s3_uri: str) -> str:
    bucket = s3_uri.split('/')[2]
    key = '/'.join(s3_uri.split('/')[3:])
    s3_client = boto3.client('s3', region_name='ap-south-1')
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response['Body'].read().decode('utf-8')

def parse_earnings_calendar(s3_uri: str, market_context: str, date_str: str) -> List[dict]:
    """
    Parses the JSON payload from S3 into a list of flat earnings calendar records.
    """
    raw_data = json.loads(_read_s3_object(s3_uri))
    records = []
    
    for symbol, cal_dict in raw_data.items():
        if 'next_earnings_date' in cal_dict:
            records.append({
                'date': date_str,
                'symbol': symbol,
                'market_context': market_context,
                'next_earnings_date': cal_dict['next_earnings_date']
            })
                
    return records
