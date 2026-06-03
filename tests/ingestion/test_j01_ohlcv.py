import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.utils.market_context import get_market_context
from src.ingestion.fetcher import fetch_daily_ohlcv
from src.ingestion.j01_ohlcv_daily import run_j01

def test_get_market_context():
    assert get_market_context("RELIANCE.NS") == "india"
    assert get_market_context("TCS.BO") == "india"
    assert get_market_context("AAPL") == "us"

@patch('src.ingestion.fetcher.yf.Ticker')
def test_fetch_daily_ohlcv_success(mock_ticker_class):
    # Setup mock
    mock_ticker = MagicMock()
    mock_ticker_class.return_value = mock_ticker

    # Create dummy dataframe
    df = pd.DataFrame({
        'Open': [100.0],
        'High': [105.0],
        'Low': [99.0],
        'Close': [104.0],
        'Volume': [1000],
        'Adj Close': [104.0]
    })
    mock_ticker.history.return_value = df

    result = fetch_daily_ohlcv("AAPL")

    assert not result.empty
    assert "Open" in result.columns
    assert "Adj Close" in result.columns
    mock_ticker.history.assert_called_once_with(period="1d", auto_adjust=False)

@patch('src.ingestion.fetcher.yf.Ticker')
def test_fetch_daily_ohlcv_empty(mock_ticker_class):
    mock_ticker = MagicMock()
    mock_ticker_class.return_value = mock_ticker
    mock_ticker.history.return_value = pd.DataFrame()

    with pytest.raises(Exception):
        fetch_daily_ohlcv("INVALID_TICKER")

@patch('src.ingestion.j01_ohlcv_daily.fetch_daily_ohlcv')
def test_run_j01_dry_run(mock_fetch, capsys):
    # Setup mock to return a dummy df so it doesn't actually hit yfinance
    mock_fetch.return_value = pd.DataFrame({'Open': [1], 'Close': [1]})

    # Run in dry_run mode to avoid S3 and DynamoDB calls
    run_j01(dry_run=True)

    captured = capsys.readouterr()
    assert "Job completed with status: SUCCESS" in captured.out
    assert "DRY RUN" in captured.out
