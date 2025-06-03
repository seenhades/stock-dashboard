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
    "Pfizer (美股)": "PFE",
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=120)

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
    macd = ema_short - ema_long
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def calculate_cci(data, period=20):
    tp = (data['High'] + data['Low'] + data['Close']) / 3
    sma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.fabs(x - x.mean()).mean())
    return (tp - sma) / (0.015 * mad)

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
    if rsi < 20:
        results.append("🧊 RSI 過冷 → 買進訊號")
    elif rsi > 70:
        results.append("🔥 RSI 過熱 → 賣出訊號")
    if macd > signal:
        results.append("💰 MACD 黃金交叉 → 買進")
    else:
        results.append("⚠️ MACD 死亡交叉 → 賣出")
    if cci < -100:
        results.append("🧊 CCI 過低 → 買進")
    elif cci > 100:
        results.append("🔥 CCI 過高 → 賣出")
    if k < 20 and d < 20 and k > d:
        results.append("💰 KD 低檔黃金交叉 → 買進")
    elif k > 80 and d > 80 and k < d:
        results.append("⚠️ KD 高檔死亡交叉 → 賣出")
    buy_count = sum("買進" in x for x in results)
    sell_count = sum("賣出" in x for x in results)
    if buy_count > sell_count:
        summary = "🔵 綜合評估：買進"
    elif sell_count > buy_count:
        summary = "🔴 綜合評估：賣出"
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

    st.metric("📌 最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")

    # ... 以下顯示區塊保持不變（略） ...
