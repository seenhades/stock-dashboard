import yfinance as yf

data = yf.download("OGN", period="5d", interval="1d")
print(data.columns)
print(data.head())
