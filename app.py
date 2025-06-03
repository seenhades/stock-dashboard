import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

st.title("股票技術指標與收盤價監控")

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

def calculate_bollinger(data, period=20):
    ma = data['Close'].rolling(window=period).mean()
    std = data['Close'].rolling(window=period).std()
    upper = ma + 2 * std
    lower = ma - 2 * std
    return upper, lower

def box_range_analysis(close_series):
    recent_high = close_series.rolling(window=20).max()
    recent_low = close_series.rolling(window=20).min()
    return recent_high, recent_low

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

    # 技術指標計算
    data['RSI'] = calculate_rsi(data['Close'])
    data['MACD'], data['Signal'] = calculate_macd(data['Close'])
    data['CCI'] = calculate_cci(data)
    data['%K'], data['%D'] = calculate_kd(data)
    data['5MA'] = data['Close'].rolling(window=5).mean()
    data['10MA'] = data['Close'].rolling(window=10).mean()
    data['20MA'] = data['Close'].rolling(window=20).mean()
    data['BB_upper'], data['BB_lower'] = calculate_bollinger(data)
    data['BoxHigh'], data['BoxLow'] = box_range_analysis(data['Close'])

    # 最新值
    latest_rsi = data['RSI'].iloc[-1]
    latest_macd = data['MACD'].iloc[-1]
    latest_signal = data['Signal'].iloc[-1]
    latest_cci = data['CCI'].iloc[-1]
    latest_k = data['%K'].iloc[-1]
    latest_d = data['%D'].iloc[-1]
    latest_5ma = data['5MA'].iloc[-1]
    latest_10ma = data['10MA'].iloc[-1]
    latest_20ma = data['20MA'].iloc[-1]
    latest_bb_upper = data['BB_upper'].iloc[-1]
    latest_bb_lower = data['BB_lower'].iloc[-1]
    latest_box_high = data['BoxHigh'].iloc[-1]
    latest_box_low = data['BoxLow'].iloc[-1]

    # 顯示資料
    st.metric("📌 最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")
    st.write(f"📊 5MA: {latest_5ma:.2f}, 10MA: {latest_10ma:.2f}, 20MA: {latest_20ma:.2f}")
    st.write(f"📊 RSI: {latest_rsi:.2f}")
    st.write(f"📊 MACD: {latest_macd:.4f}, Signal: {latest_signal:.4f}")
    st.write(f"📊 CCI: {latest_cci:.2f}")
    st.write(f"📊 KD: %K = {latest_k:.2f}, %D = {latest_d:.2f}")
    st.write(f"📊 布林通道: Upper = {latest_bb_upper:.2f}, Lower = {latest_bb_lower:.2f}")
    st.write(f"📊 箱型區間: 高點 = {latest_box_high:.2f}, 低點 = {latest_box_low:.2f}")

    # 均線排列分析
    if latest_5ma > latest_10ma > latest_20ma:
        st.info("📈 均線多頭排列，可能為上升趨勢")
    elif latest_5ma < latest_10ma < latest_20ma:
        st.warning("📉 均線空頭排列，可能為下降趨勢")
    else:
        st.info("🔁 均線混合排列，趨勢不明")

    # 綜合訊號評估
    signals, overall = evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)
    for s in signals:
        st.info(s)
    st.success(overall)

    st.markdown("---")
