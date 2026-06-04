import os
import json
import boto3
import yfinance as yf
from datetime import datetime, timedelta
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_actions_for_symbol(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    actions_df = ticker.actions
    
    if actions_df.empty:
        return {}
        
    # Filter for actions in the last 7 days to avoid re-ingesting full history every week
    seven_days_ago = datetime.utcnow().date() - timedelta(days=7)
    
    recent_actions = {}
    for date_idx, row in actions_df.iterrows():
        # Yahoo returns timezone-aware timestamps, convert to naive date
        action_date = date_idx.date() if hasattr(date_idx, 'date') else date_idx
        if action_date >= seven_days_ago:
            date_str = action_date.strftime('%Y-%m-%d')
            if date_str not in recent_actions:
                recent_actions[date_str] = {}
            
            if 'Dividends' in row and row['Dividends'] > 0:
                recent_actions[date_str]['dividend'] = float(row['Dividends'])
            if 'Stock Splits' in row and row['Stock Splits'] > 0:
                recent_actions[date_str]['split'] = float(row['Stock Splits'])
                
    return recent_actions

def fetch_corporate_actions(universe: List[str], date_str: str) -> str:
    """
    Fetches corporate actions for all symbols in the universe for the last 7 days.
    Saves the payload to S3 Landing and returns the S3 URI.
    """
    all_actions = {}
    
    for symbol in universe:
        try:
            actions = _fetch_actions_for_symbol(symbol)
            if actions:
                all_actions[symbol] = actions
        except Exception as e:
            print(f"Warning: Failed to fetch actions for {symbol}: {e}")
            
    bucket_name = os.environ.get('S3_LANDING_BUCKET', 'project-intelligent-landing-307828758318')
    s3_client = boto3.client('s3', region_name='ap-south-1')
    
    s3_key = f"yfinance/corporate_actions/date={date_str}/actions.json"
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(all_actions).encode('utf-8')
    )
    
    return f"s3://{bucket_name}/{s3_key}"
