import streamlit as stMore actions
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
    "Pfizer (美股)": "PFE",
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=120)
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

def calculate_macd(series, short=12, long=26, signal=9):
    ema_short = series.ewm(span=short, adjust=False).mean()
    ema_long = series.ewm(span=long, adjust=False).mean()
def calculate_macd(series, span_short=12, span_long=26, signal_span=9):
    ema_short = series.ewm(span=span_short, adjust=False).mean()
    ema_long = series.ewm(span=span_long, adjust=False).mean()
    macd = ema_short - ema_long
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line
    signal = macd.ewm(span=signal_span, adjust=False).mean()
    return macd, signal

def calculate_cci(data, period=20):
    tp = (data['High'] + data['Low'] + data['Close']) / 3
    sma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.fabs(x - x.mean()).mean())
    return (tp - sma) / (0.015 * mad)
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
    upper = sma + num_std * std
    lower = sma - num_std * std
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return sma, upper, lower

def evaluate_ma_signals(price, ma5, ma10, ma20):
    if price > ma5 > ma10 > ma20:
        return "📈 均線多頭排列（短期強勢）"
    elif price < ma5 < ma10 < ma20:
        return "📉 均線空頭排列（短期弱勢）"
    elif max(abs(ma5 - ma10), abs(ma10 - ma20), abs(ma5 - ma20)) < 0.5:
        return "⚠️ 均線糾結（盤整或變盤前兆）"
    else:
        return "➖ 均線無明顯趨勢排列"

def box_range_analysis(series):
    q1 = np.percentile(series.dropna(), 25)
    q3 = np.percentile(series.dropna(), 75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    latest = series.dropna().iloc[-1]
    if latest > upper:
        return "📈 股價突破箱型上緣（可能過熱）"
    elif latest < lower:
        return "📉 股價跌破箱型下緣（可能超賣）"
    elif q1 <= latest <= q3:
        return "📦 股價位於箱型中段（正常波動）"
    else:
        return "➖ 股價位於箱型外圍（留意波動）"

def evaluate_signals(rsi, macd, signal, cci, k, d):
    results = []
    signals = []
    if rsi < 20:
        results.append("🧊 RSI 過冷 → 買進訊號")
        signals.append("🧊 RSI過冷，可能超賣，買進訊號")
    elif rsi > 70:
        results.append("🔥 RSI 過熱 → 賣出訊號")
        signals.append("🔥 RSI過熱，可能過買，賣出訊號")
    if macd > signal:
        results.append("💰 MACD 黃金交叉 → 買進")
    else:
        results.append("⚠️ MACD 死亡交叉 → 賣出")
        signals.append("💰 MACD黃金交叉，買進訊號")
from technical_analysis import *  # 假設已有完整技術分析函數

def evaluate_ma_signals(latest_close, ma5, ma10, ma20):
    if latest_close > ma5 > ma10 > ma20:
        return "📈 均線多頭排列（短期強勢）"
    elif latest_close < ma5 < ma10 < ma20:
        return "📉 均線空頭排列（短期弱勢）"
    elif max(abs(ma5 - ma10), abs(ma10 - ma20), abs(ma5 - ma20)) < 0.5:
        return "⚠️ 均線糾結（盤整或變盤前兆）"
else:
        signals.append("⚠️ MACD死亡交叉，賣出訊號")
    if cci < -100:
        results.append("🧊 CCI 過低 → 買進")
        signals.append("🧊 CCI過低，可能超賣，買進訊號")
    elif cci > 100:
        results.append("🔥 CCI 過高 → 賣出")
        signals.append("🔥 CCI過高，可能過買，賣出訊號")
    if k < 20 and d < 20 and k > d:
        results.append("💰 KD 低檔黃金交叉 → 買進")
        signals.append("💰 KD低檔黃金交叉，買進訊號")
    elif k > 80 and d > 80 and k < d:
        results.append("⚠️ KD 高檔死亡交叉 → 賣出")
    buy_count = sum("買進" in x for x in results)
    sell_count = sum("賣出" in x for x in results)
    if buy_count > sell_count:
        summary = "🔵 綜合評估：買進"
    elif sell_count > buy_count:
        summary = "🔴 綜合評估：賣出"
        signals.append("⚠️ KD高檔死亡交叉，賣出訊號")

    buy_signals = sum(1 for s in signals if "買進" in s)
    sell_signals = sum(1 for s in signals if "賣出" in s)
    if buy_signals > sell_signals:
        overall = "🔵 綜合評估：買進"
    elif sell_signals > buy_signals:
        overall = "🔴 綜合評估：賣出"
    else:
        summary = "🟠 綜合評估：持有"
    return results, summary

for name, symbol in stock_list.items():
    st.markdown(f"## {name} ({symbol})")
    data = yf.download(symbol, start=start, end=end, interval='1d')

    st.caption(f"共獲取 {len(data)} 筆資料")

    if data.empty or len(data) < 30:
        st.warning(f"{symbol} 資料不足或無法取得")
        continue

    data["RSI"] = calculate_rsi(data["Close"])
    data["MACD"], data["Signal"] = calculate_macd(data["Close"])
    data["CCI"] = calculate_cci(data)
    data["%K"], data["%D"] = calculate_kd(data)
    data["5MA"] = data["Close"].rolling(5).mean()
    data["10MA"] = data["Close"].rolling(10).mean()
    data["20MA"] = data["Close"].rolling(20).mean()
    data["BB_MID"], data["BB_UPPER"], data["BB_LOWER"] = calculate_bollinger_bands(data["Close"])
        overall = "🟠 綜合評估：持有"

    latest = data.iloc[-1]
    prev = data.iloc[-2] if len(data) >= 2 else latest

    try:
        latest_close = float(latest["Close"])
        prev_close = float(prev["Close"])
    except Exception as e:
        st.warning(f"⚠️ 收盤價轉換失敗：{e}")
        continue

    if data[["RSI", "MACD", "Signal", "CCI", "%K", "%D", "5MA", "10MA", "20MA"]].isnull().iloc[-1].any():
        st.warning("⚠️ 技術指標尚未完整計算，資料可能不足")
        continue
    return signals, overall
        return "➖ 均線無明顯趨勢排列"

    st.metric("📌 最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")
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
        ma_signal = evaluate_ma_signals(latest_close, latest_5ma, latest_10ma, latest_20ma)
        st.info(ma_signal)

    col1, col2 = st.columns(2)
st.markdown("### 💹 RSI 指標")
color_rsi = "#28B463" if latest_rsi < 30 else ("#C0392B" if latest_rsi > 70 else "#555")
st.markdown(f"<div style='font-size:18px'>RSI: <span style='color:{color_rsi}'>{latest_rsi:.2f}</span></div>", unsafe_allow_html=True)

with col1:
    st.markdown("### 📈 均線（MA）")
    st.markdown(
        f"<div style='font-size:18px'>"
        f"5日: <span style='color:#2E86C1'>{latest['5MA']:.2f}</span>, "
        f"10日: <span style='color:#28B463'>{latest['10MA']:.2f}</span>, "
        f"20日: <span style='color:#AF7AC5'>{latest['20MA']:.2f}</span>"
        f"</div>",
        unsafe_allow_html=True
    )
    st.info(f"📊 均線排列：{evaluate_ma_signals(latest_close, latest['5MA'], latest['10MA'], latest['20MA'])}")

    st.markdown("### 💹 RSI")
    rsi_color = "#28B463" if latest["RSI"] < 30 else ("#C0392B" if latest["RSI"] > 70 else "#555")
    st.markdown(f"<div style='font-size:18px'>RSI: <span style='color:{rsi_color}'>{latest['RSI']:.2f}</span></div>", unsafe_allow_html=True)

    st.markdown("### 📊 CCI")
    cci_color = "#28B463" if latest["CCI"] < -100 else ("#C0392B" if latest["CCI"] > 100 else "#555")
    st.markdown(f"<div style='font-size:18px'>CCI: <span style='color:{cci_color}'>{latest['CCI']:.2f}</span></div>", unsafe_allow_html=True)
st.markdown("### 📊 CCI 指標")
color_cci = "#28B463" if latest_cci < -100 else ("#C0392B" if latest_cci > 100 else "#555")
st.markdown(f"<div style='font-size:18px'>CCI: <span style='color:{color_cci}'>{latest_cci:.2f}</span></div>", unsafe_allow_html=True)

with col2:
    st.markdown("### 📉 MACD")
    macd_color = "#28B463" if latest["MACD"] > latest["Signal"] else "#C0392B"
    st.markdown(f"<div style='font-size:18px'>MACD: <span style='color:{macd_color}'>{latest['MACD']:.4f}</span>, Signal: {latest['Signal']:.4f}</div>", unsafe_allow_html=True)
st.markdown("### 📉 MACD 指標")
color_macd = "#28B463" if latest_macd > latest_signal else "#C0392B"
st.markdown(f"<div style='font-size:18px'>MACD: <span style='color:{color_macd}'>{latest_macd:.4f}</span>, Signal: {latest_signal:.4f}</div>", unsafe_allow_html=True)

    st.markdown("### 🌀 KD")
    st.markdown(f"<div style='font-size:18px'>%K = {latest['%K']:.2f}, %D = {latest['%D']:.2f}</div>", unsafe_allow_html=True)
st.markdown("### 🌀 KD 指標")
st.markdown(f"<div style='font-size:18px'>%K = {latest_k:.2f}, %D = {latest_d:.2f}</div>", unsafe_allow_html=True)

    st.markdown("### 📎 布林通道")
    st.markdown(f"<div style='font-size:18px'>中: {latest['BB_MID']:.2f}, 上: {latest['BB_UPPER']:.2f}, 下: {latest['BB_LOWER']:.2f}</div>", unsafe_allow_html=True)
    if latest['Close'] > latest['BB_UPPER']:
        st.info("📈 股價突破布林上軌，可能過熱")
    elif latest['Close'] < latest['BB_LOWER']:
        st.info("📉 股價跌破布林下軌，可能超賣")
st.markdown("### 📎 布林通道（BBands）")
st.markdown(f"<div style='font-size:18px'>中: {latest_bb_mid:.2f}, 上: {latest_bb_upper:.2f}, 下: {latest_bb_lower:.2f}</div>", unsafe_allow_html=True)

    st.info(f"📦 箱型分析：{box_range_analysis(data['Close'])}")
if latest_close < latest_bb_lower:
st.info("📉 股價跌破布林下軌，可能超賣")
elif latest_close > latest_bb_upper:
st.info("📈 股價突破布林上軌，可能過熱")

signals, summary = evaluate_signals(latest["RSI"], latest["MACD"], latest["Signal"], latest["CCI"], latest["%K"], latest["%D"])
signals, overall = evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)
for s in signals:
    st.info(s)
st.success(summary)
st.info(s)
st.success(overall)

st.markdown("---")
