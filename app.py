import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="股票技術指標看板", layout="wide")

st.title("📈 股票技術指標看板")

# 股票清單
tickers = st.multiselect(
    "選擇股票代碼（例如：AAPL, TSLA, 2330.TW）",
    ["AAPL", "TSLA", "2330.TW", "ORGN", "IFX.DE", "SHEL", "1306.TW", "NEM", "6752.T", "9432.T"]
)

@st.cache_data(ttl=300)
def get_data(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="5m")
        df.dropna(inplace=True)
        return df
    except Exception as e:
        st.error(f"{ticker} 資料抓取失敗：{e}")
        return pd.DataFrame()

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
        
        if data.empty:
            st.warning(f"{ticker} 無可用資料")
            continue

        data = compute_indicators(data)

        if "Close" in data.columns and "SMA20" in data.columns:
            st.line_chart(data[["Close", "SMA20"]])
        else:
            st.warning(f"{ticker} 的 SMA20 或 Close 資料無法取得")

        if "RSI" in data.columns:
            st.line_chart(data[["RSI"]])
        else:
            st.warning(f"{ticker} 的 RSI 資料無法取得")

        if "MACD" in data.columns and "Signal" in data.columns:
