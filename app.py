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

# === 技術指標計算函式 ===
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

# === 總體呈現與卡片 ===
def render_card(icon, text, color):
    return f"""
    <div style='
        background-color: #f7f9fc;
        border-left: 6px solid {color};
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 18px;
        display: flex;
        align-items: center;
        gap: 12px;
    '>
        <div style='font-size: 24px;'>{icon}</div>
        <div style='color:{color}; font-weight: 600;'>{text}</div>
    </div>
    """

def get_color(signal_text):
    if "買進" in signal_text:
        return "green"
    elif "賣出" in signal_text:
        return "red"
    else:
        return "orange"

def evaluate_ma_trend(ma5, ma10, ma20):
    if ma5 > ma10 > ma20:
        return "📈 均線呈多頭排列"
    elif ma5 < ma10 < ma20:
        return "📉 均線呈空頭排列"
    else:
        return "🔄 均線呈糾結狀態"

for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")
    data = yf.download(symbol, start=start, end=end)
    if data.empty or len(data) < 30:
        st.warning(f"{symbol} 資料不足")
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

    latest = data.iloc[-1]
    prev_close = data['Close'].iloc[-2]
    
    st.metric("📌 最新收盤價", f"{latest['Close']:.2f}", f"{latest['Close'] - prev_close:+.2f}")

    ma_status = evaluate_ma_trend(latest['5MA'], latest['10MA'], latest['20MA'])
    ma_color = ("green" if "多頭" in ma_status else "red" if "空頭" in ma_status else "orange")

    st.markdown(render_card("📈", ma_status, ma_color), unsafe_allow_html=True)

    # RSI
    if latest['RSI'] < 20:
        rsi_signal = "🧊 RSI過冷，可能超賣，買進訊號"
    elif latest['RSI'] > 70:
        rsi_signal = "🔥 RSI過熱，可能過買，賣出訊號"
    else:
        rsi_signal = "🔄 RSI中性"

    # MACD
    if latest['MACD'] > latest['Signal']:
        macd_signal = "💰 MACD黃金交叉，買進訊號"
    else:
        macd_signal = "⚠️ MACD死亡交叉，賣出訊號"

    # CCI
    if latest['CCI'] < -100:
        cci_signal = "🧊 CCI過低，可能超賣，買進訊號"
    elif latest['CCI'] > 100:
        cci_signal = "🔥 CCI過高，可能過買，賣出訊號"
    else:
        cci_signal = "🔄 CCI中性"

    # KD
    if latest['%K'] < 20 and latest['%D'] < 20 and latest['%K'] > latest['%D']:
        kd_signal = "💰 KD低檔黃金交叉，買進訊號"
    elif latest['%K'] > 80 and latest['%D'] > 80 and latest['%K'] < latest['%D']:
        kd_signal = "⚠️ KD高檔死亡交叉，賣出訊號"
    else:
        kd_signal = "🔄 KD中性"

    st.markdown(render_card("📉", f"RSI: {latest['RSI']:.2f} - {rsi_signal}", get_color(rsi_signal)), unsafe_allow_html=True)
    st.markdown(render_card("📈", f"MACD: {latest['MACD']:.4f} (Signal: {latest['Signal']:.4f}) - {macd_signal}", get_color(macd_signal)), unsafe_allow_html=True)
    st.markdown(render_card("📊", f"CCI: {latest['CCI']:.2f} - {cci_signal}", get_color(cci_signal)), unsafe_allow_html=True)
    st.markdown(render_card("🎯", f"KD: K={latest['%K']:.2f}, D={latest['%D']:.2f} - {kd_signal}", get_color(kd_signal)), unsafe_allow_html=True)

    st.divider()
