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

def detect_signals(df):
    signal = ""
    if len(df) < 2:
        return "📉 資料不足無法判斷"

    rsi_now = df["RSI"].iloc[-1]
    macd_now = df["MACD"].iloc[-1]
    signal_now = df["Signal"].iloc[-1]
    macd_prev = df["MACD"].iloc[-2]
    signal_prev = df["Signal"].iloc[-2]

    if rsi_now < 30 and macd_prev < signal_prev and macd_now > signal_now:
        signal = "🟢 買進訊號（RSI 超賣 + MACD 黃金交叉）"
    elif rsi_now > 70 and macd_prev > signal_prev and macd_now < signal_now:
        signal = "🔴 賣出訊號（RSI 超買 + MACD 死亡交叉）"
    elif rsi_now > 70:
        signal = "⚠️ RSI 過熱，可能超買"
    elif rsi_now < 30:
        signal = "⚠️ RSI 過低，可能超賣"
    else:
        signal = "✅ 無明顯買賣訊號"

    return signal

if tickers:
    for ticker in tickers:
        st.subheader(f"📊 {ticker} 技術指標分析")
        data = get_data(ticker)
        
        if data.empty:
            st.warning(f"{ticker} 無可用資料")
            continue

        data = compute_indicators(data)

        # 顯示技術圖表
        if "Close" in data.columns and "SMA20" in data.columns:
            st.line_chart(data[["Close", "SMA20"]])
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

        # 顯示訊號
        if all(x in data.columns for x in ["RSI", "MACD", "Signal"]):
            result = detect_signals(data)
            st.success(result if "🟢" in result else result) if "🟢" in result else st.warning(result)

        st.dataframe(data.tail(10))
        st.markdown("---")
else:
    st.info("請選擇至少一個股票代碼以查看分析。")
