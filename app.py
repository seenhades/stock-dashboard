import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")
st.title("📈 股票技術指標與收盤價監控")

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

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series, span_short=12, span_long=26, signal_span=9):
    ema_short = series.ewm(span=span_short, adjust=False).mean()
    ema_long = series.ewm(span=span_long, adjust=False).mean()
    macd = ema_short - ema_long
    signal = macd.ewm(span=signal_span, adjust=False).mean()
    return macd, signal

def calculate_cci(data, period=20):
    tp = (data['High'] + data['Low'] + data['Close']) / 3
    sma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.fabs(x - x.mean()).mean())
    cci = (tp - sma) / (0.015 * mad)
    return cci

def calculate_kd(data, k_period=9, d_period=3):
    low_min = data['Low'].rolling(window=k_period).min()
    high_max = data['High'].rolling(window=k_period).max()
    rsv = (data['Close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=d_period-1, adjust=False).mean()
    d = k.ewm(com=d_period-1, adjust=False).mean()
    return k, d

def calculate_bollinger_bands(series, window=20, num_std=2):
    sma = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper_band = sma + num_std * std
    lower_band = sma - num_std * std
    return upper_band, lower_band

def calculate_box_range(series, period=20):
    upper = series.rolling(window=period).max()
    lower = series.rolling(window=period).min()
    return upper, lower

def evaluate_signals(rsi, macd, signal, cci, k, d):
    signals = []
    if rsi < 20:
        signals.append("🧊 RSI過冷，可能超賣，買進訊號")
    elif rsi > 70:
        signals.append("🔥 RSI過熱，可能過買，賣出訊號")
    if macd > signal:
        signals.append("💰 MACD黃金交叉，買進訊號")
    else:
        signals.append("⚠️ MACD死亡交叉，賣出訊號")
    if cci < -100:
        signals.append("🧊 CCI過低，可能超賣，買進訊號")
    elif cci > 100:
        signals.append("🔥 CCI過高，可能過買，賣出訊號")
    if k < 20 and d < 20 and k > d:
        signals.append("💰 KD低檔黃金交叉，買進訊號")
    elif k > 80 and d > 80 and k < d:
        signals.append("⚠️ KD高檔死亡交叉，賣出訊號")

    buy_signals = sum(1 for s in signals if "買進" in s)
    sell_signals = sum(1 for s in signals if "賣出" in s)
    if buy_signals > sell_signals:
        overall = "🔵 綜合評估：買進"
    elif sell_signals > buy_signals:
        overall = "🔴 綜合評估：賣出"
    else:
        overall = "🟠 綜合評估：持有"

    return signals, overall

for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")
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
    data['UpperBB'], data['LowerBB'] = calculate_bollinger_bands(data['Close'])
    data['BoxHigh'], data['BoxLow'] = calculate_box_range(data['Close'])

    latest_rsi = data['RSI'].iloc[-1]
    latest_macd = data['MACD'].iloc[-1]
    latest_signal = data['Signal'].iloc[-1]
    latest_cci = data['CCI'].iloc[-1]
    latest_k = data['%K'].iloc[-1]
    latest_d = data['%D'].iloc[-1]
    latest_5ma = data['5MA'].iloc[-1]
    latest_10ma = data['10MA'].iloc[-1]
    latest_20ma = data['20MA'].iloc[-1]
    latest_upperbb = data['UpperBB'].iloc[-1]
    latest_lowerbb = data['LowerBB'].iloc[-1]
    latest_boxhigh = data['BoxHigh'].iloc[-1]
    latest_boxlow = data['BoxLow'].iloc[-1]

    st.metric("📌 最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 均線與動能指標")
        st.markdown(f"<div style='font-size: 18px;'>5MA: {latest_5ma:.2f}, 10MA: {latest_10ma:.2f}, 20MA: {latest_20ma:.2f}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 18px;'>RSI: {latest_rsi:.2f}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 18px;'>MACD: {latest_macd:.4f}, Signal: {latest_signal:.4f}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 18px;'>CCI: {latest_cci:.2f}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 18px;'>KD: %K = {latest_k:.2f}, %D = {latest_d:.2f}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("### 📉 趨勢區間與價格帶")
        st.markdown(f"<div style='font-size: 18px;'>布林通道：上軌 = {latest_upperbb:.2f}, 下軌 = {latest_lowerbb:.2f}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 18px;'>箱型區間：高點 = {latest_boxhigh:.2f}, 低點 = {latest_boxlow:.2f}</div>", unsafe_allow_html=True)

    signals, overall = evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)
    for s in signals:
        st.markdown(f"<div style='font-size: 18px;'>{s}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size: 20px; font-weight: bold; color: green;'>{overall}</div>", unsafe_allow_html=True)

    st.markdown("---")
