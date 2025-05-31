import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

st.set_page_config(page_title="股票技術分析看板", layout="wide")

# 你關注的股票清單
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
start = end - datetime.timedelta(days=90)

st.title("📈 股票技術分析儀表板")

# 自動每 5 分鐘更新資料 (但實際抓的是日線資料)
@st.cache_data(ttl=300)
def fetch_data(symbol):
    data = yf.download(symbol, start=start, end=end, interval="1d")
    if data.empty or "Close" not in data.columns:
        return None

    data["SMA20"] = data["Close"].rolling(window=20).mean()

    delta = data["Close"].diff().values  # 一維 numpy 陣列
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain, index=data.index).rolling(window=14).mean()
    avg_loss = pd.Series(loss, index=data.index).rolling(window=14).mean()

    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    exp1 = data["Close"].ewm(span=12, adjust=False).mean()
    exp2 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = exp1 - exp2
    data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()

    return data

# 顯示每支股票的資訊
for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")

    data = fetch_data(symbol)

    if data is None or data.empty:
        st.warning(f"{symbol} 沒有資料，請稍後再試。")
        continue

    # 顯示今日及前一日收盤價
    if len(data) < 2:
        st.warning(f"{symbol} 資料不足，無法顯示收盤價比較。")
        continue

    latest = data.iloc[-1]
    prev = data.iloc[-2]

    col1, col2 = st.columns(2)
    col1.metric("今日收盤價", f"{latest['Close']:.2f}", f"{latest['Close'] - prev['Close']:+.2f}")
    col2.metric("昨日收盤價", f"{prev['Close']:.2f}")

    # 買賣訊號判斷
    signals = []
    if "MACD" in data.columns and "Signal" in data.columns:
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

    # 技術指標圖表
    st.line_chart(data[["Close", "SMA20"]].dropna())
    st.line_chart(data[["MACD", "Signal"]].dropna())
    st.line_chart(data[["RSI"]].dropna())

    st.markdown("---")
