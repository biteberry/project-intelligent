import pandas as pd

def get_universe(market_context: str = None):
    """
    Dynamically fetches the active universe of symbols from the NSE Equity master list.
    """
    if market_context == "us":
        return ["AAPL", "MSFT"] # Keep a fallback for US stocks if needed
        
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        df = pd.read_csv(url)
        # Filter for normal equities (EQ series)
        df = df[df[' SERIES'] == 'EQ']
        symbols = [f"{sym}.NS" for sym in df['SYMBOL'].tolist()]
        return symbols
    except Exception as e:
        print(f"Warning: Failed to fetch NSE universe: {e}. Falling back to default list.")
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

def get_market_context(symbol: str) -> str:
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return "india"
    return "us"
