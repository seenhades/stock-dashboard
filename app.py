import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

# 設定頁面
st.set_page_config(layout="wide")
st.title("📈 多國股票技術指標分析")

# 分國家分類股票清單
stock_tabs = {
    "🇹🇼 台灣": {},
    "🇺🇸 美國": {
        "Organon": "OGN",
        "Newmont": "NEM",
        "VanEck Gold ETF": "OUNZ",
    },
    "🇬🇧 英國": {
        "Shell": "SHEL.L",
        "Rolls Royce": "RR.L",
    },
    "🇯🇵 日本": {
        "Panasonic": "6752.T",
        "NTT": "9432.T",
        "1306 ETF": "1306.T",
    },
    "🇭🇰 香港": {
        "國泰航空": "0293.HK",
        "碧桂園": "2007.HK",
        "中糧家佳康": "1610.HK",
    },
    "🇩🇪 德國": {
        "Porsche SE": "PAH3.DE",
        "Infineon": "IFX.DE",
    },
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=250)  # 為了能算出120MA

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

def calculate_ma(series, windows):
    return {f"{w}MA": series.rolling(window=w).mean() for w in windows}

def evaluate_ma_trend(ma1, ma2, ma3):
    if ma1 > ma2 > ma3:
        return "📈 均線呈多頭排列"
    elif ma1 < ma2 < ma3:
        return "📉 均線呈空頭排列"
    else:
        return "🔄 均線呈糾結狀態"

def render_card(icon, text, color):
    return f"""
    <div style='background-color: #f7f9fc; border-left: 6px solid {color}; padding: 12px 16px; margin: 8px 0; font-size: 20px; display: flex; align-items: center; gap: 12px;'>
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

# === 顯示各分頁 ===
tabs = st.tabs(list(stock_tabs.keys()))
for idx, (market, stocks) in enumerate(stock_tabs.items()):
    with tabs[idx]:
        for name, symbol in stocks.items():
            st.subheader(f"{name} ({symbol})")
            data = yf.download(symbol, start=start, end=end, interval="1d")
            if data.empty or len(data) < 130:
                st.warning(f"{symbol} 資料不足或無法取得")
                continue

            data['RSI'] = calculate_rsi(data['Close'])
            data['MACD'], data['Signal'] = calculate_macd(data['Close'])
            data['CCI'] = calculate_cci(data)
            data['%K'], data['%D'] = calculate_kd(data)

            ma_dict = calculate_ma(data['Close'], [20, 60, 120])
            for k, v in ma_dict.items():
                data[k] = v

            latest = data.iloc[-1]
            ma_status = evaluate_ma_trend(latest['20MA'], latest['60MA'], latest['120MA'])

            st.metric("📌 最新收盤價", f"{latest['Close']:.2f}", f"{latest['Close'] - data['Close'].iloc[-2]:+.2f}")

            st.markdown(f"<div style='font-size: 18px;'><b>20MA:</b> {latest['20MA']:.2f}, <b>60MA:</b> {latest['60MA']:.2f}, <b>120MA:</b> {latest['120MA']:.2f}</div>", unsafe_allow_html=True)

            ma_color = "green" if "多頭" in ma_status else "red" if "空頭" in ma_status else "orange"
            st.markdown(render_card("", ma_status, ma_color), unsafe_allow_html=True)

            # RSI 卡片
            rsi_signal = "🧊 RSI過冷，可能超賣，買進訊號" if latest['RSI'] < 20 else "🔥 RSI過熱，可能過買，賣出訊號" if latest['RSI'] > 70 else "🔄 RSI中性"
            if "中性" not in rsi_signal:
                st.markdown(render_card("", rsi_signal, get_color(rsi_signal)), unsafe_allow_html=True)

            # MACD 卡片
            macd_signal = "💰 MACD黃金交叉，買進訊號" if latest['MACD'] > latest['Signal'] else "⚠️ MACD死亡交叉，賣出訊號"
            st.markdown(render_card("", macd_signal, get_color(macd_signal)), unsafe_allow_html=True)

            # CCI 卡片
            cci_signal = "🧊 CCI過低，可能超賣，買進訊號" if latest['CCI'] < -100 else "🔥 CCI過高，可能過買，賣出訊號" if latest['CCI'] > 100 else "🔄 CCI中性"
            if "中性" not in cci_signal:
                st.markdown(render_card("", cci_signal, get_color(cci_signal)), unsafe_allow_html=True)

            # KD 卡片
            k, d = latest['%K'], latest['%D']
            if k < 20 and d < 20 and k > d:
                kd_signal = "💰 KD低檔黃金交叉，買進訊號"
            elif k > 80 and d > 80 and k < d:
                kd_signal = "⚠️ KD高檔死亡交叉，賣出訊號"
            else:
                kd_signal = "🔄 KD中性"
            if "中性" not in kd_signal:
                st.markdown(render_card("", kd_signal, get_color(kd_signal)), unsafe_allow_html=True)

            st.markdown("---")
