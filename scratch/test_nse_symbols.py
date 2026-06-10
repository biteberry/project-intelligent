import pandas as pd

try:
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    df = pd.read_csv(url)
    symbols = df['SYMBOL'].tolist()
    print(f"Found {len(symbols)} symbols in NSE Equity master list.")
    print("Sample:", symbols[:5])
except Exception as e:
    print(f"Error: {e}")
