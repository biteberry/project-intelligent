import yfinance as yf
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_daily_ohlcv(symbol: str) -> pd.DataFrame:
    """
    Fetch the most recent daily OHLCV data for a given symbol using yfinance.
    Returns a pandas DataFrame with both raw prices and Adj Close.
    Retries up to 3 times with exponential backoff on failure.
    """
    ticker = yf.Ticker(symbol)
    # Using auto_adjust=False to ensure we get raw Open/High/Low/Close and a separate 'Adj Close'
    df = ticker.history(period="1d", auto_adjust=False)
    
    if df.empty:
        raise ValueError(f"No data returned for symbol {symbol}")
        
    return df
