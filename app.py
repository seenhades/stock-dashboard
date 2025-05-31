import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="股票技術指標看板", layout="wide")

st.title("📈 股票技術指標看板")

# 使用者輸入股票代碼
tickers = st.multiselect("選擇股票代碼（例如：AAPL, TSLA, 2330.TW）", ["AAPL", "TSLA", "2330.TW"])

# 設定資料抓取間隔（秒）
interval = 300  # 5 分鐘

@st.cache_data(ttl=interval)
def get_data(ticker):
    df = yf.download(ticker, period="1mo", interval="5m")
    df.dropna(inplace=True)
    return df

def compute_indicators(df):
    df["SMA20"] = df["Close"].rolling(window=20).mean()
    df["RSI"] = compute_rsi(df["Close"])
    df["MACD"], df["Signal"] = compute_macd(df["Close"])
    return df

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

if tickers:
    for ticker in tickers:
        st.subheader(f"📊 {ticker} 技術指標分析")
        data = get_data(ticker)
        data = compute_indicators(data)
        
        columns_to_show = []

if "Close" in data.columns and "SMA20" in data.columns:
    columns_to_show = ["Close", "SMA20"]
    st.line_chart(data[columns_to_show])
else:
    st.warning(f"{ticker} 的 SMA20 或 Close 資料無法取得")

if "RSI" in data.columns:
    st.line_chart(data[["RSI"]])
else:
    st.warning(f"{ticker} 的 RSI 資料無法取得")

if "MACD" in data.columns and "Signal" in data.columns:
    st.line_chart(data[["MACD", "Signal"]])
else:
    st.warning(f"{ticker} 的 MACD 或 Signal 資料無法取得")

        
        st.dataframe(data.tail(10))
        st.markdown("---")
else:
    st.info("請選擇至少一個股票代碼以查看分析。")
