import json
import boto3
import re
from bs4 import BeautifulSoup

def _read_s3_object(s3_uri: str) -> str:
    bucket = s3_uri.split('/')[2]
    key = '/'.join(s3_uri.split('/')[3:])
    s3_client = boto3.client('s3', region_name='ap-south-1')
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response['Body'].read().decode('utf-8')

def parse_macro(date_str: str, s3_uris: dict) -> dict:
    """
    Parses the yfinance JSON and the RBI HTML to create a combined macro record.
    """
    yf_json = json.loads(_read_s3_object(s3_uris['yf_uri']))
    rbi_html = _read_s3_object(s3_uris['rbi_uri'])
    
    # 1. Parse yfinance data
    record = {
        'date': date_str,
        'market_context': 'india',
        'india_vix_close': yf_json.get('^INDIAVIX', {}).get('close', None),
        'nifty50_close': yf_json.get('^NSEI', {}).get('close', None),
        'rbi_repo_rate': None,
        'india_10y_yield': None
    }
    
    # 2. Parse RBI HTML using BeautifulSoup
    soup = BeautifulSoup(rbi_html, 'html.parser')
    tables = soup.find_all('table')
    
    for t in tables:
        for tr in t.find_all('tr'):
            tds = [td.text.strip() for td in tr.find_all(['td', 'th'])]
            if len(tds) >= 2:
                # Look for Policy Repo Rate
                if 'Policy Repo Rate' in tds[0]:
                    # Format is usually ':\r\n                    5.25%'
                    rate_str = tds[1].replace(':', '').replace('%', '').strip()
                    try:
                        record['rbi_repo_rate'] = float(rate_str)
                    except ValueError:
                        pass
                
                # Look for 10Y Bond Yield (GS 203x)
                if 'GS 203' in tds[0] or 'GS 204' in tds[0]:
                    # E.g., '6.48% GS 2035' -> ': 7.0015% #'
                    # We grab the highest yield among the long-term bonds if there are multiple, or just the first match
                    yield_str = tds[1].replace(':', '').replace('%', '').replace('#', '').strip()
                    try:
                        val = float(yield_str)
                        if record['india_10y_yield'] is None or val > record['india_10y_yield']:
                            record['india_10y_yield'] = val
                    except ValueError:
                        pass
                        
    return record
