import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")
st.title("📈 股票技術指標與收盤價監控")

# 固定淺色風格 CSS（取消日夜模式）
st.markdown(
    """
    <style>
    .indicator-box {
        background-color: #f0f2f6;
        color: #000000;
        padding: 10px 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 18px;
        font-weight: 500;
    }
    .overall-box {
        background-color: #dde6ff;
        padding: 12px 16px;
        border-radius: 10px;
        font-size: 20px;
        font-weight: bold;
        margin-top: 12px;
        margin-bottom: 12px;
        color: #003399;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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

def evaluate_ma_trend(ma5, ma10, ma20):
    if ma5 > ma10 > ma20:
        return "📈 均線呈多頭排列"
    elif ma5 < ma10 < ma20:
        return "📉 均線呈空頭排列"
    else:
        return "🔄 均線呈糾結狀態"

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

def colorize(value, thresholds, colors):
    if value < thresholds[0]:
        return colors[0]
    elif value > thresholds[1]:
        return colors[2]
    else:
        return colors[1]

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

    if not np.isfinite(latest_boxhigh) or not np.isfinite(latest_boxlow):
        latest_boxhigh = latest_boxlow = None

    ma_status = evaluate_ma_trend(latest_5ma, latest_10ma, latest_20ma)

    st.metric("📌 最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 技術指標")

        # RSI 卡片
        rsi_color = colorize(latest_rsi, [30, 70], ["green", "black", "red"])
        st.markdown(f"<div class='indicator-box'>RSI: <span style='color:{rsi_color}; font-weight:bold;'>{latest_rsi:.2f}</span></div>", unsafe_allow_html=True)

        # MACD 卡片
        macd_color = "green" if latest_macd > latest_signal else "red"
        st.markdown(f"<div class='indicator-box'>MACD: <span style='color:{macd_color}; font-weight:bold;'>{latest_macd:.4f}</span>, Signal: {latest_signal:.4f}</div>", unsafe_allow_html=True)

        # CCI 卡片
        cci_color = colorize(latest_cci, [-100, 100], ["green", "black", "red"])
        st.markdown(f"<div class='indicator-box'>CCI: <span style='color:{cci_color}; font-weight:bold;'>{latest_cci:.2f}</span></div>", unsafe_allow_html=True)

        # 均線排列卡片
        st.markdown(f"<div class='indicator-box'>{ma_status}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 📉 趨勢區間與價格帶")
        st.markdown(f"布林通道上軌 = {latest_upperbb:.2f}, 下軌 = {latest_lowerbb:.2f}")
        if latest_boxhigh is not None and latest_boxlow is not None:
            st.markdown(f"箱型區間高點 = {latest_boxhigh:.2f}, 低點 = {latest_boxlow:.2f}")
        else:
            st.markdown("箱型區間資料不足")

    signals, overall = evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)
    for s in signals:
        st.markdown(f"<div class='indicator-box'>{s}</div>", unsafe_allow_html=True)

    # 整體評估顯示
    color = "#0073e6" if "買進" in overall else "#d42c2c" if "賣出" in overall else "#e68a00"
    st.markdown(f"<div class='overall-box' style='color:{color};'>{overall}</div>", unsafe_allow_html=True)

    st.markdown("---")
