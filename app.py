import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

st.set_page_config(page_title="股票技術分析看板", layout="wide")

stocks = {
    "Organon": "OGN",
    "Infineon": "IFX.DE",
    "Shell": "SHEL",
    "1306 ETF": "1306.TW",
    "Newmont": "NEM",
    "Panasonic": "6752.T",
    "NTT": "9432.T"
}

@st.cache_data(ttl=300)  # 每 5 分鐘快取更新
def load_data(ticker):
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=60)
    try:
        df = yf.download(ticker, start=start, end=end, interval="5m", progress=False)
        df = df.dropna()
        df["SMA20"] = df["Close"].rolling(window=20).mean()
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        return df
    except Exception as e:
        st.error(f"{ticker} 資料取得失敗：{e}")
        return pd.DataFrame()

st.title("📊 股票技術分析看板")

for name, ticker in stocks.items():
    st.subheader(f"{name} ({ticker})")
    data = load_data(ticker)

    if data.empty:
        st.warning("資料不足或下載失敗")
        continue

    current_price = data["Close"].iloc[-1]
    rsi = data["RSI"].iloc[-1]
    macd = data["MACD"].iloc[-1]
    signal = data["Signal"].iloc[-1]

    col1, col2, col3 = st.columns(3)

    try:
        current_price = float(current_price)
        col1.metric("目前股價", f"{current_price:.2f}")
    except (ValueError, TypeError):
        col1.metric("目前股價", "無法取得")

    try:
        rsi = float(rsi)
        col2.metric("RSI", f"{rsi:.2f}")
    except (ValueError, TypeError):
        col2.metric("RSI", "無法取得")

    try:
        macd = float(macd)
        signal = float(signal)
        col3.metric("MACD", f"{macd:.2f} / Signal: {signal:.2f}")
    except (ValueError, TypeError):
        col3.metric("MACD", "無法取得")

    if isinstance(rsi, float):
        if rsi > 70:
            st.warning("⚠️ RSI 過熱（>70）— 可能超買")
        elif rsi < 30:
            st.info("💡 RSI 超跌（<30）— 可能超賣")

    # 買賣訊號簡單判斷，防呆判斷前一筆是否存在
    if (
        "MACD" in data.columns and
        "Signal" in data.columns and
        len(data) > 1 and
        not data["MACD"].isna().all() and
        not data["Signal"].isna().all()
    ):
        prev_macd = data["MACD"].iloc[-2]
        prev_signal = data["Signal"].iloc[-2]
        if macd > signal and prev_macd <= prev_signal:
            st.success("✅ 買進訊號：MACD 黃金交叉")
        elif macd < signal and prev_macd >= prev_signal:
            st.error("⚠️ 賣出訊號：MACD 死亡交叉")

    if all(col in data.columns for col in ["Close", "SMA20"]) and len(data) >= 20:
        st.line_chart(data[["Close", "SMA20"]])
    else:
        st.warning("無法繪製 SMA20（資料不足）")

    if "RSI" in data.columns and not data["RSI"].isna().all():
        st.line_chart(data[["RSI"]])
    else:
        st.warning("無法顯示 RSI（資料不足）")

    if all(col in data.columns for col in ["MACD", "Signal"]) and not data["MACD"].isna().all():
        st.line_chart(data[["MACD", "Signal"]])
    else:
        st.warning("無法顯示 MACD（資料不足）")

    st.divider()
