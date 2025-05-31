import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

st.title("多市場股票技術指標與收盤價監控")

stock_list = {
    "Organon (美股)": "OGN",
    "Newmont (美股)": "NEM",
    "Infineon (德股)": "IFX.DE",
    "Porsche SE (德股)": "PAH3.DE",
    "Shell (英股)": "SHEL.L",
    "1306 ETF (日股)": "1306.T",
    "Panasonic (日股)": "6752.T",
    "NTT (日股)": "9432.T",
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=90)  # 取90天資料計算技術指標

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
    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    sma_tp = typical_price.rolling(window=period).mean()
    mad = typical_price.rolling(window=period).apply(lambda x: np.fabs(x - x.mean()).mean())
    cci = (typical_price - sma_tp) / (0.015 * mad)
    return cci

def evaluate_signals(rsi, macd, signal, cci):
    signals = []
    # RSI訊號
    if rsi < 30:
        signals.append("🧊 RSI過冷，可能超賣，買進訊號")
    elif rsi > 70:
        signals.append("🔥 RSI過熱，可能過買，賣出訊號")

    # MACD訊號
    if macd > signal:
        signals.append("💰 MACD黃金交叉，買進訊號")
    else:
        signals.append("⚠️ MACD死亡交叉，賣出訊號")

    # CCI訊號
    if cci < -100:
        signals.append("🧊 CCI過低，可能超賣，買進訊號")
    elif cci > 100:
        signals.append("🔥 CCI過高，可能過買，賣出訊號")

    # 綜合評估（簡單版）
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

    # 計算技術指標
    data['RSI'] = calculate_rsi(data['Close'])
    data['MACD'], data['Signal'] = calculate_macd(data['Close'])
    data['CCI'] = calculate_cci(data)

    # 取最新技術指標值
    latest_rsi = data['RSI'].iloc[-1]
    latest_macd = data['MACD'].iloc[-1]
    latest_signal = data['Signal'].iloc[-1]
    latest_cci = data['CCI'].iloc[-1]

    # 顯示收盤價與價差
    st.metric("最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")

    # 顯示技術指標
    st.write(f"RSI: {latest_rsi:.2f}")
    st.write(f"MACD: {latest_macd:.4f}, Signal: {latest_signal:.4f}")
    st.write(f"CCI: {latest_cci:.2f}")

    # 綜合訊號判斷
    signals, overall = evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci)
    for s in signals:
        st.info(s)
    st.success(overall)

    st.markdown("---")
