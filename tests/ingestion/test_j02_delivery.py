import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.ingestion.bhav_copy_fetcher import download_bhav_copy
from src.ingestion.bhav_copy_parser import parse_delivery_pct
from src.utils.holidays import is_trading_day

def test_is_trading_day():
    # Test weekend
    assert is_trading_day("2026-06-06", market="BSE") == False
    # Test holiday (Republic Day)
    assert is_trading_day("2026-01-26", market="BSE") == False
    # Test normal weekday
    assert is_trading_day("2026-06-03", market="BSE") == True

@patch('src.ingestion.bhav_copy_fetcher.boto3.client')
@patch('src.ingestion.bhav_copy_fetcher.requests.get')
def test_download_bhav_copy(mock_get, mock_boto3):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"SYMBOL, SERIES, DELIV_PER\nRELIANCE, EQ, 55.4\n"
    mock_get.return_value = mock_response
    
    mock_s3 = MagicMock()
    mock_boto3.return_value = mock_s3
    
    s3_uri = download_bhav_copy("2026-06-03")
    
    assert "project-intelligent-landing" in s3_uri
    assert "03062026.csv" in s3_uri
    mock_s3.put_object.assert_called_once()

@patch('src.ingestion.bhav_copy_parser.boto3.client')
def test_parse_delivery_pct(mock_boto3):
    mock_s3 = MagicMock()
    mock_boto3.return_value = mock_s3
    
    mock_response = {
        'Body': MagicMock(read=lambda: b"SYMBOL, SERIES, DELIV_PER\nRELIANCE, EQ, 55.4\nINVALID, BE, 10.0")
    }
    mock_s3.get_object.return_value = mock_response
    
    df = parse_delivery_pct("s3://bucket/test.csv")
    
    assert len(df) == 1
    assert df.iloc[0]['symbol'] == 'RELIANCE.NS'
    assert df.iloc[0]['delivery_pct'] == 55.4
