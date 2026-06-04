import os
import json
import boto3
import yfinance as yf
from datetime import datetime
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential

def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    from datetime import date, datetime
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_calendar_for_symbol(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    calendar = ticker.calendar
    
    if not calendar or 'Earnings Date' not in calendar:
        return {}
        
    dates = calendar['Earnings Date']
    if not dates:
        return {}
        
    # Get the nearest upcoming date
    # yfinance often returns a list of future dates for earnings
    future_dates = [d for d in dates if hasattr(d, 'date') and d.date() >= datetime.utcnow().date()]
    
    if future_dates:
        # Get the closest one
        nearest_date = min(future_dates)
        return {'next_earnings_date': nearest_date.strftime('%Y-%m-%d')}
        
    return {}

def fetch_earnings_calendar(universe: List[str], date_str: str) -> str:
    """
    Fetches the next earnings date for all symbols in the universe.
    Saves the payload to S3 Landing and returns the S3 URI.
    """
    all_calendars = {}
    
    for symbol in universe:
        try:
            cal = _fetch_calendar_for_symbol(symbol)
            if cal:
                all_calendars[symbol] = cal
        except Exception as e:
            print(f"Warning: Failed to fetch calendar for {symbol}: {e}")
            
    bucket_name = os.environ.get('S3_LANDING_BUCKET', 'project-intelligent-landing-307828758318')
    s3_client = boto3.client('s3', region_name='ap-south-1')
    
    s3_key = f"yfinance/earnings_calendar/date={date_str}/calendar.json"
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(all_calendars, default=_json_serial).encode('utf-8')
    )
    
    return f"s3://{bucket_name}/{s3_key}"
