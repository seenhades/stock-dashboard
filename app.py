import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

st.set_page_config(page_title="股票技術分析看板", layout="wide")

# 股票清單
stock_list = {
    "Organon": "OGN",
    "Infineon": "IFX.DE",
    "Shell": "SHEL",
    "1306 ETF": "1306.T",
    "Newmont": "NEM",
    "Panasonic": "6752.T",
    "NTT": "9432.T"
}

# 時間範圍
end = datetime.datetime.now()
start = end - datetime.timedelta(days=30)

st.title("📈 股票技術分析儀表板")

# 自動快取資料，5 分鐘更新
@st.cache_data(ttl=300)
def fetch_data(symbol):
    try:
        data = yf.download(symbol, start=start, end=end, interval="15m")
        if data.empty:
            return None
        data["SMA20"] = data["Close"].rolling(window=20).mean()

        delta = data["Close"].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(window=14).mean()
        avg_loss = pd.Series(loss).rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data["RSI"] = 100 - (100 / (1 + rs))

        exp1 = data["Close"].ewm(span=12, adjust=False).mean()
        exp2 = data["Close"].ewm(span=26, adjust=False).mean()
        data["MACD"] = exp1 - exp2
        data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
        return data
    except Exception as e:
        return None

# 顯示每支股票資訊
for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")

    data = fetch_data(symbol)

    if data is None or data.empty or "Close" not in data.columns:
        st.warning(f"{symbol} 抓取資料失敗或無可用數據。")
        st.markdown("---")
        continue

    # 顯示目前股價與漲跌
    try:
        current_price = data["Close"].iloc[-1]
        previous_price = data["Close"].iloc[-2]
        delta = current_price - previous_price
        col1, col2 = st.columns(2)
        col1.metric("目前股價", f"{current_price:.2f}", f"{delta:+.2f}")
    except:
        st.write("⚠️ 股價資訊不足")
        continue

    # 買賣訊號判斷
    signals = []
    if "MACD" in data.columns and "Signal" in data.columns:
        if data["MACD"].iloc[-1] > data["Signal"].iloc[-1] and data["MACD"].iloc[-2] <= data["Signal"].iloc[-2]:
            signals.append("💰 買進訊號 (MACD 黃金交叉)")
        elif data["MACD"].iloc[-1] < data["Signal"].iloc[-1] and data["MACD"].iloc[-2] >= data["Signal"].iloc[-2]:
            signals.append("⚠️ 賣出訊號 (MACD 死亡交叉)")

    # RSI 提醒
    if "RSI" in data.columns:
        rsi = data["RSI"].iloc[-1]
        if rsi > 70:
            signals.append("🔥 RSI 過熱 (>70)，可能過買")
        elif rsi < 30:
            signals.append("🧊 RSI 過冷 (<30)，可能超賣")

    if signals:
        for s in signals:
            st.info(s)
    else:
        st.write("尚無明確買賣訊號。")

    # 技術圖表
    with st.expander("📊 技術指標圖"):
        if "Close" in data.columns and "SMA20" in data.columns:
            st.line_chart(data[["Close", "SMA20"]])
        if "MACD" in data.columns and "Signal" in data.columns:
            st.line_chart(data[["MACD", "Signal"]])
        if "RSI" in data.columns:
            st.line_chart(data[["RSI"]])

    st.markdown("---")
