import yfinance as yf
import pandas as pd

symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
df = yf.download(symbols, period="1d", group_by="ticker")
print("Original Columns:")
print(df.columns)
print("\nHead:")
print(df.head())

# To transform a multi-index (Ticker, Price) into a flat table (Date, Symbol, Open, High, Low, Close, Volume):
df_flat = df.stack(level=0, future_stack=True).reset_index()
# Rename 'level_1' or whatever the ticker index is named to 'symbol'
df_flat = df_flat.rename(columns={'Ticker': 'symbol', 'level_1': 'symbol', 'Date': 'date'})
# Clean column names
df_flat.columns = [str(c).lower() for c in df_flat.columns]

print("\nFlattened:")
print(df_flat.head())
