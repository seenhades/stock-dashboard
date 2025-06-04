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

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def calculate_cci(data, period=20):
    tp = (data['High'] + data['Low'] + data['Close']) / 3
    cci = (tp - tp.rolling(window=period).mean()) / (0.015 * tp.rolling(window=period).std())
    return cci

def calculate_kd(data, period=14):
    low_min = data['Low'].rolling(window=period).min()
    high_max = data['High'].rolling(window=period).max()
    rsv = (data['Close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    return k, d

def calculate_bollinger_bands(series, window=20):
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = sma + 2 * std
    lower = sma - 2 * std
    return upper, lower

def calculate_box_range(series, window=20):
    box_high = series.rolling(window=window).max()
    box_low = series.rolling(window=window).min()
    return box_high, box_low

def evaluate_ma_trend(ma5, ma10, ma20):
    if ma5 > ma10 > ma20:
        return "多頭排列"
    elif ma5 < ma10 < ma20:
        return "空頭排列"
    elif abs(ma5 - ma10) < 0.2 and abs(ma10 - ma20) < 0.2:
        return "均線糾結"
    else:
        return "不明確"

def evaluate_signals(rsi, macd, signal, cci, k, d, close, bb_upper, bb_lower, box_high, box_low):
    result = []
    if rsi < 30:
        result.append("RSI 超賣，可考慮買進")
    elif rsi > 70:
        result.append("RSI 超買，可能回檔")
    else:
        result.append("RSI 中性")

    if macd > signal:
        result.append("MACD 黃金交叉")
    elif macd < signal:
        result.append("MACD 死亡交叉")
    else:
        result.append("MACD 中性")

    if cci > 100:
        result.append("CCI 強勢區域")
    elif cci < -100:
        result.append("CCI 弱勢區域")
    else:
        result.append("CCI 中性")

    if k > d and k < 20:
        result.append("KD 黃金交叉（低檔）")
    elif k < d and k > 80:
        result.append("KD 死亡交叉（高檔）")
    else:
        result.append("KD 中性")

    if close >= bb_upper:
        result.append("布林通道：高於上軌，可能過熱")
    elif close <= bb_lower:
        result.append("布林通道：低於下軌，可能超賣")
    else:
        result.append("布林通道：正常範圍")

    if close >= box_high.iloc[-1]:
        result.append("箱型區間：接近壓力位")
    elif close <= box_low.iloc[-1]:
        result.append("箱型區間：接近支撐位")
    else:
        result.append("箱型區間：區間震盪")

    # 綜合評估邏輯
    neutral_count = sum("中性" in r for r in result)
    buy_like = any("黃金" in r or "強勢" in r or "超賣" in r for r in result)
    sell_like = any("死亡" in r or "弱勢" in r or "過熱" in r for r in result)

    if neutral_count <= 3 and buy_like:
        overall = "🟢 綜合評估：可考慮買進"
    elif neutral_count <= 3 and sell_like:
        overall = "🔴 綜合評估：建議觀望或賣出"
    else:
        overall = "🟡 綜合評估：中性，請觀察後續走勢"

    return result, overall

def colorize(value, thresholds, colors):
    if value < thresholds[0]:
        return colors[0]
    elif value > thresholds[1]:
        return colors[2]
    else:
        return colors[1]

# 主程式開始
end = datetime.datetime.now()
start = end - datetime.timedelta(days=90)

for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")
    data = yf.download(symbol, start=start, end=end, interval="1d")
    if data.empty or len(data) < 30:
        st.warning(f"{symbol} 資料不足或無法取得")
        continue

    data['RSI'] = calculate_rsi(data['Close'])
    data['MACD'], data['Signal'] = calculate_macd(data['Close'])
    data['CCI'] = calculate_cci(data)
    data['%K'], data['%D'] = calculate_kd(data)
    data['5MA'] = data['Close'].rolling(window=5).mean()
    data['10MA'] = data['Close'].rolling(window=10).mean()
    data['20MA'] = data['Close'].rolling(window=20).mean()
    data['BB_Upper'], data['BB_Lower'] = calculate_bollinger_bands(data['Close'])
    data['Box_High'], data['Box_Low'] = calculate_box_range(data['Close'])

    latest = data.iloc[-1]

    # 均線排列狀態
    ma_trend = evaluate_ma_trend(latest['5MA'], latest['10MA'], latest['20MA'])

    # 指標分析與綜合評估
    signals, overall = evaluate_signals(
        latest['RSI'], latest['MACD'], latest['Signal'], latest['CCI'], latest['%K'], latest['%D'],
        latest['Close'], latest['BB_Upper'], latest['BB_Lower'], data['Box_High'], data['Box_Low']
    )

    # 兩欄顯示技術指標
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 均線與動能指標")
        st.write(f"• 5MA: {latest['5MA']:.2f}")
        st.write(f"• 10MA: {latest['10MA']:.2f}")
        st.write(f"• 20MA: {latest['20MA']:.2f}")
        st.write(f"• RSI: {latest['RSI']:.2f}")
        st.write(f"• MACD: {latest['MACD']:.4f}")
        st.write(f"• Signal: {latest['Signal']:.4f}")
        st.write(f"• CCI: {latest['CCI']:.2f}")
        st.write(f"• KD %K: {latest['%K']:.2f}")
        st.write(f"• KD %D: {latest['%D']:.2f}")

    with col2:
        st.markdown("### 📈 趨勢區間與價格帶")
        st.write(f"• 布林通道上軌: {latest['BB_Upper']:.2f}")
        st.write(f"• 布林通道下軌: {latest['BB_Lower']:.2f}")
        st.write(f"• 箱型區間高點: {data['Box_High'].iloc[-1]:.2f}")
        st.write(f"• 箱型區間低點: {data['Box_Low'].iloc[-1]:.2f}")

    # 分析結果區塊，有底色與較大字體
    st.markdown("### 🔍 指標分析")
    for sig in signals:
        st.markdown(f"<p style='background-color:#f0f0f5; font-size:18px; padding:6px; border-radius:4px;'>{sig}</p>", unsafe_allow_html=True)

    st.markdown(f"<p style='background-color:#d1e7dd; font-size:20px; padding:8px; border-radius:6px; font-weight:bold;'>均線狀態：{ma_trend}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='background-color:#cfe2ff; font-size:20px; padding:8px; border-radius:6px; font-weight:bold;'>{overall}</p>", unsafe_allow_html=True)

    st.markdown("---")
