import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import math

st.set_page_config(page_title="股票技術分析看板", layout="wide")

stock_list = {
    "Organon": "OGN",
    "Newmont": "NEM",
    "Infineon": "IFX.DE",
    "Porsche SE": "PAH3.DE",
    "Shell": "SHEL.L",
    "1306 ETF": "1306.T",
    "Panasonic": "6752.T",
    "NTT": "9432.T"
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=90)

st.title("📈 股票技術分析儀表板")

@st.cache_data(ttl=300)
def fetch_data(symbol):
    try:
        data = yf.download(symbol, start=start, end=end, interval="1d")
        if data.empty or "Close" not in data.columns:
            return None
        
        data = data.dropna(subset=['Close', 'High', 'Low'])
        if data.empty:
            return None
        
        # SMA20
        data["SMA20"] = data["Close"].rolling(window=20).mean()
        
        # RSI
        delta = data["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data["RSI"] = 100 - (100 / (1 + rs))

        # MACD & Signal
        exp1 = data["Close"].ewm(span=12, adjust=False).mean()
        exp2 = data["Close"].ewm(span=26, adjust=False).mean()
        data["MACD"] = exp1 - exp2
        data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()

        # CCI
        tp = (data["High"] + data["Low"] + data["Close"]) / 3
        ma = tp.rolling(window=20).mean()
        md = tp.rolling(window=20).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        data["CCI"] = (tp - ma) / (0.015 * md)

        # KD 指標 (Stochastic Oscillator)
        low_min = data["Low"].rolling(window=14).min()
        high_max = data["High"].rolling(window=14).max()
        data["%K"] = 100 * ((data["Close"] - low_min) / (high_max - low_min))
        data["%D"] = data["%K"].rolling(window=3).mean()

        return data
    except Exception as e:
        return None

for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")

    data = fetch_data(symbol)
    if data is None or len(data) < 15:
        st.warning(f"{symbol} 無法抓取足夠資料或資料不完整，請稍後再試。")
        st.markdown("---")
        continue

    latest_close = data["Close"].iloc[-1]
    prev_close = data["Close"].iloc[-2]

    # 檢查最新收盤價是否為有效數字
    if any([
        latest_close is None, prev_close is None,
        not isinstance(latest_close, (int, float)), not isinstance(prev_close, (int, float)),
        math.isnan(latest_close), math.isnan(prev_close)
    ]):
        st.warning(f"{symbol} 收盤價資料不完整，無法顯示。")
        st.markdown("---")
        continue

    col1, col2 = st.columns(2)
    col1.metric("最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")
    col2.metric("昨日收盤價", f"{prev_close:.2f}")

    # 買賣訊號判斷
    signals = []

    # MACD 黃金/死亡交叉
    if data["MACD"].iloc[-1] > data["Signal"].iloc[-1] and data["MACD"].iloc[-2] <= data["Signal"].iloc[-2]:
        signals.append("💰 買進訊號 (MACD 黃金交叉)")
    elif data["MACD"].iloc[-1] < data["Signal"].iloc[-1] and data["MACD"].iloc[-2] >= data["Signal"].iloc[-2]:
        signals.append("⚠️ 賣出訊號 (MACD 死亡交叉)")

    # RSI
    rsi = data["RSI"].iloc[-1]
    if rsi > 70:
        signals.append("🔥 RSI 過熱 (>70)，可能過買")
    elif rsi < 30:
        signals.append("🧊 RSI 過冷 (<30)，可能超賣")

    # CCI
    cci = data["CCI"].iloc[-1]
    if cci > 100:
        signals.append("🔥 CCI 過熱 (>100)，可能過買")
    elif cci < -100:
        signals.append("🧊 CCI 過冷 (<-100)，可能超賣")

    # KD黃金/死亡交叉
    if (data["%K"].iloc[-1] > data["%D"].iloc[-1]) and (data["%K"].iloc[-2] <= data["%D"].iloc[-2]):
        signals.append("💰 買進訊號 (KD 黃金交叉)")
    elif (data["%K"].iloc[-1] < data["%D"].iloc[-1]) and (data["%K"].iloc[-2] >= data["%D"].iloc[-2]):
        signals.append("⚠️ 賣出訊號 (KD 死亡交叉)")

    if signals:
        for s in signals:
            st.info(s)
    else:
        st.write("尚無明確買賣訊號。")

    # 繪製圖表
    st.line_chart(data[["Close", "SMA20"]])
    st.line_chart(data[["MACD", "Signal"]])
    st.line_chart(data[["RSI"]])
    st.line_chart(data[["CCI"]])
    st.line_chart(data[["%K", "%D"]])

    st.markdown("---")
