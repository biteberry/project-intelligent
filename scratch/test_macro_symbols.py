import yfinance as yf

symbols = ['GC=F', 'CL=F', 'INR=X']
df = yf.download(symbols, period='5d', group_by='ticker')
print(df)
