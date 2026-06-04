import pandas as pd
import json
import boto3

def _read_s3_json(s3_uri: str) -> list:
    bucket = s3_uri.split('/')[2]
    key = '/'.join(s3_uri.split('/')[3:])
    s3_client = boto3.client('s3', region_name='ap-south-1')
    response = s3_client.get_object(Bucket=bucket, Key=key)
    json_string = response['Body'].read().decode('utf-8')
    return json.loads(json_string)

def parse_sentiment(s3_uri: str) -> pd.DataFrame:
    """
    Parses the raw JSON array from Landing into the Bronze DataFrame schema.
    Applies logic defined in ADR-005.
    """
    raw_data = _read_s3_json(s3_uri)
    
    rows = []
    for item in raw_data:
        symbol = item.get('requested_symbol')
        
        sentiment = item.get('sentiment', {})
        buzz = item.get('buzz', {})
        
        bullish = sentiment.get('bullishPercent', 0)
        bearish = sentiment.get('bearishPercent', 0)
        
        # Guard against None
        if bullish is None: bullish = 0
        if bearish is None: bearish = 0
        
        sentiment_score = bullish - bearish
        
        # Calculate direction
        if sentiment_score > 0.1:
            direction = 1
        elif sentiment_score < -0.1:
            direction = -1
        else:
            direction = 0
            
        news_intensity = buzz.get('articlesInLastWeek', 0)
        if news_intensity is None: news_intensity = 0
            
        coverage_flag = 'low' if news_intensity < 2 else 'normal'
        
        rows.append({
            'symbol': symbol,
            'sentiment_score': sentiment_score,
            'sentiment_direction': direction,
            'news_intensity': news_intensity,
            'news_coverage_flag': coverage_flag,
            'sentiment_source': 'finnhub'
        })
        
    df = pd.DataFrame(rows)
    return df
