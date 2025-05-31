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
    "NTT": "9432.T",
    "國泰航空": "293.HK",
    "中糧家佳康": "06106.HK",
    "碧桂園": "2007.HK"
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=90)

st.title("📈 股票技術分析儀表板")

def is_valid_number(x):
    return isinstance(x, (float, int)) and not pd.isna(x) and np.isfinite(x)

@st.cache_data(ttl=300)
def fetch_data(symbol):
    try:
        data = yf.download(symbol, start=start, end=end, interval="1d")
        if data.empty or "Close" not in data.columns:
            return None

        # 計算技術指標：SMA20
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
        typical_price = (data["High"] + data["Low"] + data["Close"]) / 3
        ma = typical_price.rolling(window=20).mean()
        md = typical_price.rolling(window=20).apply(lambda x: np.mean(np.abs(x - x.mean())))
        data["CCI"] = (typical_price - ma) / (0.015 * md)

        # KD 指標
        low_min = data["Low"].rolling(window=14).min()
        high_max = data["High"].rolling(window=14).max()
        data["%K"] = 100 * (data["Close"] - low_min) / (high_max - low_min)
        data["%D"] = data["%K"].rolling(window=3).mean()

        return data
    except Exception as e:
        return None

for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")
    data = fetch_data(symbol)

    if data is None:
        st.warning(f"{symbol} 無法取得資料，請確認代碼或稍後再試。")
        st.markdown("---")
        continue

    if len(data) < 2:
        st.warning("資料不足，無法顯示技術指標。")
        st.markdown("---")
        continue

    latest = data.iloc[-1]
    prev = data.iloc[-2]

    latest_close = latest["Close"]
    prev_close = prev["Close"]

    if not is_valid_number(latest_close) or not is_valid_number(prev_close):
        st.warning("收盤價資料不完整，跳過該股票")
        st.markdown("---")
        continue

    st.metric("最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")

    # 買賣訊號判斷
    signals = []
    if data["MACD"].iloc[-1] > data["Signal"].iloc[-1] and data["MACD"].iloc[-2] <= data["Signal"].iloc[-2]:
        signals.append("💰 買進訊號 (MACD 黃金交叉)")
    elif data["MACD"].iloc[-1] < data["Signal"].iloc[-1] and data["MACD"].iloc[-2] >= data["Signal"].iloc[-2]:
        signals.append("⚠️ 賣出訊號 (MACD 死亡交叉)")

    rsi = latest["RSI"]
    if is_valid_number(rsi):
        if rsi > 70:
            signals.append("🔥 RSI 過熱 (>70)，可能過買")
        elif rsi < 30:
            signals.append("🧊 RSI 過冷 (<30)，可能超賣")

    cci = latest["CCI"]
    if is_valid_number(cci):
        if cci > 100:
            signals.append("🔥 CCI 過熱 (>100)")
        elif cci < -100:
            signals.append("🧊 CCI 過冷 (<-100)")

    k = latest["%K"]
    d = latest["%D"]
    if is_valid_number(k) and is_valid_number(d):
        if k > d and data["%K"].iloc[-2] <= data["%D"].iloc[-2]:
            signals.append("💰 KD黃金交叉買進訊號")
        elif k < d and data["%K"].iloc[-2] >= data["%D"].iloc[-2]:
            signals.append("⚠️ KD死亡交叉賣出訊號")

    if signals:
        for s in signals:
            st.info(s)
    else:
        st.write("尚無明確買賣訊號。")

    # 視覺化技術指標圖表
    st.line_chart(data[["Close", "SMA20"]])
    st.line_chart(data[["MACD", "Signal"]])
    st.line_chart(data[["RSI"]])
    st.line_chart(data[["CCI"]])
    st.line_chart(data[["%K", "%D"]])

    st.markdown("---")
