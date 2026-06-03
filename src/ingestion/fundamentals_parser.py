import json
import boto3
import pandas as pd

def parse_fundamentals(s3_landing_uri: str, symbol: str) -> dict:
    """
    Reads the raw yfinance .info JSON from the Landing bucket and extracts Bronze schema fields.
    Returns a dictionary of the extracted fields.
    """
    # Parse S3 URI
    # Format: s3://bucket-name/path/to/file.json
    bucket = s3_landing_uri.split('/')[2]
    key = '/'.join(s3_landing_uri.split('/')[3:])
    
    s3_client = boto3.client('s3', region_name='ap-south-1')
    response = s3_client.get_object(Bucket=bucket, Key=key)
    raw_json = response['Body'].read().decode('utf-8')
    
    info = json.loads(raw_json)
    
    # Safe extraction function
    def safe_get(data: dict, key: str, default=pd.NA):
        val = data.get(key)
        return val if val is not None else default
        
    # Extract only the keys we need for the Bronze fundamentals schema
    parsed_record = {
        'symbol': symbol,
        
        # Valuation
        'pe_ratio': safe_get(info, 'trailingPE'),
        'forward_pe': safe_get(info, 'forwardPE'),
        'price_to_book': safe_get(info, 'priceToBook'),
        'market_cap': safe_get(info, 'marketCap'),
        
        # Institutional Positioning
        'institutional_ownership_pct': safe_get(info, 'institutionalHolders', default=0.0) if safe_get(info, 'institutionalHolders') is not None else pd.NA,
        # 'impliedHoldersPercent' is often used as institutional ownership %
        'implied_institutional_ownership_pct': safe_get(info, 'impliedSharesOutstanding'), # not exact but we use what we can get
        'held_percent_institutions': safe_get(info, 'heldPercentInstitutions'),
        'held_percent_insiders': safe_get(info, 'heldPercentInsiders'),
        'short_ratio': safe_get(info, 'shortRatio'),
        'short_percent_of_float': safe_get(info, 'shortPercentOfFloat'),
        
        # Financial Health
        'total_revenue': safe_get(info, 'totalRevenue'),
        'net_income': safe_get(info, 'netIncomeToCommon'),
        'total_debt': safe_get(info, 'totalDebt'),
        'operating_cashflow': safe_get(info, 'operatingCashflow'),
        
        # Determine if fundamentals exist (for fraud risk detection)
        # We define "presence" as having a non-null P/E ratio or revenue
    }
    
    # Normalize percentages to be 0-1 if they aren't already (yfinance sometimes returns 0.50 for 50%, sometimes 50)
    # usually heldPercent is 0.5 for 50%
    
    # Flag for fraud analysis: 1 if fundamental presence exists, 0 if missing
    has_fundamentals = (parsed_record['pe_ratio'] is not pd.NA) or (parsed_record['total_revenue'] is not pd.NA)
    parsed_record['fundamental_presence_flag'] = 1 if has_fundamentals else 0
    
    return parsed_record
