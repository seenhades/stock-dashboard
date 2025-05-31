import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="股票技術分析看板", layout="wide")

# 股票清單（含美股、德股、英股、日股、港股）
stock_list = {
    "Organon (美股)": "OGN",
    "Newmont (美股)": "NEM",
    "Infineon (德股)": "IFX.DE",
    "Porsche SE (德股)": "PAH3.DE",
    "Shell (英股)": "SHEL.L",
    "1306 ETF (日股)": "1306.T",
    "Panasonic (日股)": "6752.T",
    "NTT (日股)": "9432.T",
    "國泰航空 (港股)": "0293.HK",
    "中糧家佳康 (港股)": "1610.HK",
    "碧桂園 (港股)": "2007.HK",
}

@st.cache_data(ttl=600)
def fetch_data(symbol):
    data = yf.download(symbol, period="90d", interval="1d")
    if data.empty or "Close" not in data.columns:
        return None

    # 計算技術指標
    data["SMA20"] = data["Close"].rolling(window=20).mean()

    # RSI
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = data["Close"].ewm(span=12, adjust=False).mean()
    exp2 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = exp1 - exp2
    data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()

    # CCI
    typical_price = (data["High"] + data["Low"] + data["Close"]) / 3
    ma_typical = typical_price.rolling(window=20).mean()
    mean_deviation = typical_price.rolling(window=20).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    data["CCI"] = (typical_price - ma_typical) / (0.015 * mean_deviation)

    # KD值
    low_min = data["Low"].rolling(window=14).min()
    high_max = data["High"].rolling(window=14).max()
    data["%K"] = 100 * (data["Close"] - low_min) / (high_max - low_min)
    data["%D"] = data["%K"].rolling(window=3).mean()

    return data

st.title("📊 多市場股票技術分析看板")

for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")

    data = fetch_data(symbol)
    if data is None or len(data) < 30:
        st.warning(f"{symbol} 資料不足或無法取得")
        st.markdown("---")
        continue

    latest = data.iloc[-1]
    prev = data.iloc[-2]

    # 顯示最新收盤價和前一天差價
    try:
        latest_close = latest["Close"]
        prev_close = prev["Close"]
    except KeyError:
        st.warning("資料格式錯誤，無法取得收盤價")
        st.markdown("---")
        continue

    st.metric("最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")

    # 買賣訊號示例
    signals = []

    # MACD 黃金交叉 / 死亡交叉
    if data["MACD"].iloc[-1] > data["Signal"].iloc[-1] and data["MACD"].iloc[-2] <= data["Signal"].iloc[-2]:
        signals.append("💰 買進訊號 (MACD 黃金交叉)")
    elif data["MACD"].iloc[-1] < data["Signal"].iloc[-1] and data["MACD"].iloc[-2] >= data["Signal"].iloc[-2]:
        signals.append("⚠️ 賣出訊號 (MACD 死亡交叉)")

    # RSI 超買超賣
    rsi_val = latest["RSI"]
    if rsi_val > 70:
        signals.append("🔥 RSI 過熱 (>70)")
    elif rsi_val < 30:
        signals.append("🧊 RSI 超賣 (<30)")

    # CCI 超買超賣
    cci_val = latest["CCI"]
    if cci_val > 100:
        signals.append("🔥 CCI 超買 (>100)")
    elif cci_val < -100:
        signals.append("🧊 CCI 超賣 (<-100)")

    # KD黃金交叉 / 死亡交叉
    if data["%K"].iloc[-1] > data["%D"].iloc[-1] and data["%K"].iloc[-2] <= data["%D"].iloc[-2]:
        signals.append("💰 KD 黃金交叉")
    elif data["%K"].iloc[-1] < data["%D"].iloc[-1] and data["%K"].iloc[-2] >= data["%D"].iloc[-2]:
        signals.append("⚠️ KD 死亡交叉")

    if signals:
        for s in signals:
            st.info(s)
    else:
        st.write("尚無明確買賣訊號")

    # 畫圖：收盤價 + SMA20
    st.line_chart(data[["Close", "SMA20"]])

    # MACD + Signal
    st.line_chart(data[["MACD", "Signal"]])

    # RSI、CCI、%K、%D
    st.line_chart(data[["RSI", "CCI", "%K", "%D"]])

    st.markdown("---")
