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

    if close >= box_high:
        result.append("箱型區間：接近壓力位")
    elif close <= box_low:
        result.append("箱型區間：接近支撐位")
    else:
        result.append("箱型區間：區間震盪")

    if result.count("中性") <= 3 and any("黃金" in r or "強勢" in r for r in result):
        overall = "🟢 綜合評估：可考慮買進"
    elif result.count("中性") <= 3 and any("死亡" in r or "弱勢" in r for r in result):
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

# 👉 UI 顯示邏輯會在資料下載與計算後加入
