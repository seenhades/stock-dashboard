import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")
st.title("📈 股票技術指標與收盤價監控")

# 計算與分析函數區

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
    try:
        if ma5.iloc[-1] > ma10.iloc[-1] > ma20.iloc[-1]:
            return "多頭排列"
        elif ma5.iloc[-1] < ma10.iloc[-1] < ma20.iloc[-1]:
            return "空頭排列"
        elif abs(ma5.iloc[-1] - ma10.iloc[-1]) < 0.2 and abs(ma10.iloc[-1] - ma20.iloc[-1]) < 0.2:
            return "均線糾結"
        else:
            return "不明確"
    except:
        return "資料不足"

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

    if close >= box_high:
        result.append("箱型區間：接近壓力位")
    elif close <= box_low:
        result.append("箱型區間：接近支撐位")
    else:
        result.append("箱型區間：區間震盪")

    neutral_count = sum("中性" in r for r in result)
    if neutral_count <= 3 and any("黃金" in r or "強勢" in r for r in result):
        overall = "🟢 綜合評估：可考慮買進"
    elif neutral_count <= 3 and any("死亡" in r or "弱勢" in r for r in result):
        overall = "🔴 綜合評估：建議觀望或賣出"
    else:
        overall = "🟡 綜合評估：中性，請觀察後續走勢"
    return result, overall

# 股票列表與選擇
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

selected_stock = st.selectbox("請選擇股票：", list(stock_list.keys()))
ticker = stock_list[selected_stock]
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=90)
data = yf.download(ticker, start=start_date, end=end_date)
data.dropna(inplace=True)

if data.empty:
    st.error("無法取得該股票資料，請稍後再試或選擇其他股票。")
    st.stop()

# 計算指標
data['MA5'] = data['Close'].rolling(window=5).mean()
data['MA10'] = data['Close'].rolling(window=10).mean()
data['MA20'] = data['Close'].rolling(window=20).mean()
data['RSI'] = calculate_rsi(data['Close'])
data['MACD'], data['MACD_signal'] = calculate_macd(data['Close'])
data['CCI'] = calculate_cci(data)
data['K'], data['D'] = calculate_kd(data)
data['BB_upper'], data['BB_lower'] = calculate_bollinger_bands(data['Close'])
data['Box_High'], data['Box_Low'] = calculate_box_range(data['Close'])

# 把 NaN 用前一筆補齊（避免float轉換錯誤）
data.fillna(method='ffill', inplace=True)
latest = data.iloc[-1]

ma_trend = evaluate_ma_trend(data['MA5'], data['MA10'], data['MA20'])

signals, overall = evaluate_signals(
    float(latest['RSI']),
    float(latest['MACD']),
    float(latest['MACD_signal']),
    float(latest['CCI']),
    float(latest['K']),
    float(latest['D']),
    float(latest['Close']),
    float(latest['BB_upper']),
    float(latest['BB_lower']),
    float(latest['Box_High']),
    float(latest['Box_Low'])
)

st.markdown("## 📊 技術指標一覽")
col1, col2 = st.columns(2)
with col1:
    st.markdown("### 📌 均線與動能指標")
    st.markdown(f"- 🔹 5MA：{latest['MA5']:.2f}")
    st.markdown(f"- 🔹 10MA：{latest['MA10']:.2f}")
    st.markdown(f"- 🔹 20MA：{latest['MA20']:.2f}")
    st.markdown(f"- 🔹 RSI：{latest['RSI']:.2f}")
    st.markdown(f"- 🔹 MACD：{latest['MACD']:.2f} / Signal：{latest['MACD_signal']:.2f}")
    st.markdown(f"- 🔹 CCI：{latest['CCI']:.2f}")
    st.markdown(f"- 🔹 KD：K={latest['K']:.2f}, D={latest['D']:.2f}")

with col2:
    st.markdown("### 📌 趨勢區間與價格帶")
    st.markdown(f"- 🔹 布林上軌：{latest['BB_upper']:.2f}")
    st.markdown(f"- 🔹 布林下軌：{latest['BB_lower']:.2f}")
    st.markdown(f"- 🔹 箱型區間上緣：{latest['Box_High']:.2f}")
    st.markdown(f"- 🔹 箱型區間下緣：{latest['Box_Low']:.2f}")

st.markdown("### 📋 指標分析")
st.markdown(f"- 均線排列：**{ma_trend}**")
for s in signals:
    st.markdown(f"- {s}")

st.markdown(f"## 🧠 {overall}")
