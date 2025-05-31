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

# 時間範圍（改為日資料）
end = datetime.datetime.now()
start = end - datetime.timedelta(days=90)

st.title("📈 股票技術分析儀表板 (日線資料)")

@st.cache_data(ttl=3600)
def fetch_data(symbol):
    data = yf.download(symbol, start=start, end=end, interval="1d")
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

for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")
    data = fetch_data(symbol)

    if data is None or data.empty:
        st.warning("❌ 抓取資料失敗或無可用數據")
        continue

    current_price = data["Close"].iloc[-1]
    previous_price = data["Close"].iloc[-2]
    delta = current_price - previous_price
    col1, col2 = st.columns(2)
    col1.metric("目前股價", f"{current_price:.2f}", f"{delta:+.2f}")

    # 買賣訊號
    signals = []
    if data["MACD"].iloc[-1] > data["Signal"].iloc[-1] and data["MACD"].iloc[-2] <= data["Signal"].iloc[-2]:
        signals.append("💰 買進訊號 (MACD 黃金交叉)")
    elif data["MACD"].iloc[-1] < data["Signal"].iloc[-1] and data["MACD"].iloc[-2] >= data["Signal"].iloc[-2]:
        signals.append("⚠️ 賣出訊號 (MACD 死亡交叉)")

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

    # 顯示圖表
    st.line_chart(data[["Close", "SMA20"]].dropna())
    st.line_chart(data[["MACD", "Signal"]].dropna())
    st.line_chart(data[["RSI"]].dropna())

    st.markdown("---")
