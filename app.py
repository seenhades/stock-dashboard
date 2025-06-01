import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 股票技術指標與收盤價監控")

stock_list = {
    "Panasonic (日股)": "6752.T",
    "NTT (日股)": "9432.T",
    "1306 ETF (日股)": "1306.T",
    "國泰航空(港股)": "0293.HK",
    "碧桂園(港股)": "2007.HK",
    "中糧家佳康(港股)": "1610.HK",
    "Shell (英股)": "SHEL.L",
    "Porsche SE (德股)": "PAH3.DE",
    "Infineon (德股)": "IFX.DE",
    "Organon (美股)": "OGN",
    "Newmont (美股)": "NEM",    
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=90)

@st.cache_data(ttl=86400)
def fetch_fundamentals(symbol):
    ticker = yf.Ticker(symbol)
    try:
        eps = ticker.info.get("trailingEps")
        pb = ticker.info.get("priceToBook")
        today = datetime.date.today()
        year_start = f"{today.year - 1}-01-01"
        year_end = f"{today.year - 1}-12-31"
        hist = ticker.history(start=year_start, end=year_end)
        avg_price = hist['Close'].mean() if not hist.empty else None
        pe = avg_price / eps if eps and avg_price else None
        return eps, avg_price, pe, pb
    except Exception:
        return None, None, None, None

from technical_analysis import *  # 假設已有完整技術分析函數

for name, symbol in stock_list.items():
    st.markdown(f"## {name} ({symbol})")
    data = yf.download(symbol, start=start, end=end, interval="1d")
    if data.empty or len(data) < 30:
        st.warning(f"{symbol} 資料不足或無法取得")
        continue

    try:
        latest_close = data["Close"].iloc[-1].item()
        prev_close = data["Close"].iloc[-2].item()
    except Exception as e:
        st.warning(f"{symbol} 收盤價讀取錯誤: {e}")
        continue

    if not (np.isfinite(latest_close) and np.isfinite(prev_close)):
        st.warning(f"{symbol} 收盤價非有效數值")
        continue

    data['RSI'] = calculate_rsi(data['Close'])
    data['MACD'], data['Signal'] = calculate_macd(data['Close'])
    data['CCI'] = calculate_cci(data)
    data['%K'], data['%D'] = calculate_kd(data)
    data['5MA'] = data['Close'].rolling(window=5).mean()
    data['10MA'] = data['Close'].rolling(window=10).mean()
    data['20MA'] = data['Close'].rolling(window=20).mean()
    data['BB_MID'], data['BB_UPPER'], data['BB_LOWER'] = calculate_bollinger_bands(data['Close'])

    latest_rsi = data['RSI'].iloc[-1]
    latest_macd = data['MACD'].iloc[-1]
    latest_signal = data['Signal'].iloc[-1]
    latest_cci = data['CCI'].iloc[-1]
    latest_k = data['%K'].iloc[-1]
    latest_d = data['%D'].iloc[-1]
    latest_5ma = data['5MA'].iloc[-1]
    latest_10ma = data['10MA'].iloc[-1]
    latest_20ma = data['20MA'].iloc[-1]
    latest_bb_mid = data['BB_MID'].iloc[-1]
    latest_bb_upper = data['BB_UPPER'].iloc[-1]
    latest_bb_lower = data['BB_LOWER'].iloc[-1]

    st.metric("📌 最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📈 均線（MA）")
        st.markdown(f"<div style='font-size:18px'>5日: <span style='color:#2E86C1'>{latest_5ma:.2f}</span>, 10日: <span style='color:#28B463'>{latest_10ma:.2f}</span>, 20日: <span style='color:#AF7AC5'>{latest_20ma:.2f}</span></div>", unsafe_allow_html=True)

        st.markdown("### 💹 RSI 指標")
        color_rsi = "#28B463" if latest_rsi < 30 else ("#C0392B" if latest_rsi > 70 else "#555")
        st.markdown(f"<div style='font-size:18px'>RSI: <span style='color:{color_rsi}'>{latest_rsi:.2f}</span></div>", unsafe_allow_html=True)

        st.markdown("### 📊 CCI 指標")
        color_cci = "#28B463" if latest_cci < -100 else ("#C0392B" if latest_cci > 100 else "#555")
        st.markdown(f"<div style='font-size:18px'>CCI: <span style='color:{color_cci}'>{latest_cci:.2f}</span></div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 📉 MACD 指標")
        color_macd = "#28B463" if latest_macd > latest_signal else "#C0392B"
        st.markdown(f"<div style='font-size:18px'>MACD: <span style='color:{color_macd}'>{latest_macd:.4f}</span>, Signal: {latest_signal:.4f}</div>", unsafe_allow_html=True)

        st.markdown("### 🌀 KD 指標")
        st.markdown(f"<div style='font-size:18px'>%K = {latest_k:.2f}, %D = {latest_d:.2f}</div>", unsafe_allow_html=True)

        st.markdown("### 📎 布林通道（BBands）")
        st.markdown(f"<div style='font-size:18px'>中: {latest_bb_mid:.2f}, 上: {latest_bb_upper:.2f}, 下: {latest_bb_lower:.2f}</div>", unsafe_allow_html=True)

        if latest_close < latest_bb_lower:
            st.info("📉 股價跌破布林下軌，可能超賣")
        elif latest_close > latest_bb_upper:
            st.info("📈 股價突破布林上軌，可能過熱")

    signals, overall = evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)
    for s in signals:
        st.info(s)
    st.success(overall)

    eps, avg_price, pe, pb = fetch_fundamentals(symbol)
    if eps:
        st.markdown("### 🧾 財務指標（最新年度）")
        st.markdown(f"<div style='font-size:18px'>EPS：{eps:.2f}</div>", unsafe_allow_html=True)
        if avg_price:
            st.markdown(f"<div style='font-size:18px'>年度平均股價：約 {avg_price:.2f}</div>", unsafe_allow_html=True)
        if pe:
            st.markdown(f"<div style='font-size:18px'>本益比（PE）：{pe:.2f}</div>", unsafe_allow_html=True)
        if pb:
            st.markdown(f"<div style='font-size:18px'>股價淨值比（PB）：{pb:.2f}</div>", unsafe_allow_html=True)
    else:
        st.info("無法取得財報指標資料")

    st.markdown("---")
