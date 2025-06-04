import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")
st.title("📈 股票技術指標與收盤價監控（夜間版）")

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

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def calculate_cci(df, n=20):
    TP = (df['High'] + df['Low'] + df['Close']) / 3
    MA = TP.rolling(window=n).mean()
    MD = TP.rolling(window=n).apply(lambda x: np.fabs(x - x.mean()).mean())
    cci = (TP - MA) / (0.015 * MD)
    return cci

def calculate_kd(df, n=14):
    low_min = df['Low'].rolling(window=n).min()
    high_max = df['High'].rolling(window=n).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=2).mean()
    d = k.ewm(com=2).mean()
    return k, d

def calculate_bollinger_bands(series, n=20):
    ma = series.rolling(window=n).mean()
    std = series.rolling(window=n).std()
    upper = ma + 2 * std
    lower = ma - 2 * std
    return upper, lower

def calculate_box_range(series, n=20):
    # 箱型區間：近 n 天高低價
    box_high = series.rolling(window=n).max()
    box_low = series.rolling(window=n).min()
    return box_high, box_low

def evaluate_ma_trend(ma5, ma10, ma20):
    if ma5 > ma10 > ma20:
        return "多頭排列"
    elif ma5 < ma10 < ma20:
        return "空頭排列"
    else:
        return "盤整或交錯"

def evaluate_signals(rsi, macd, signal_line, cci, k, d):
    signals = []
    overall = "中性"

    # RSI
    if rsi < 30:
        signals.append("RSI 超賣，可能買進訊號")
    elif rsi > 70:
        signals.append("RSI 超買，可能賣出訊號")

    # MACD
    if macd > signal_line:
        signals.append("MACD 多頭排列")
    else:
        signals.append("MACD 空頭排列")

    # CCI
    if cci < -100:
        signals.append("CCI 超賣，可能買進訊號")
    elif cci > 100:
        signals.append("CCI 超買，可能賣出訊號")

    # KD
    if k < 20 and d < 20 and k > d:
        signals.append("KD 黃金交叉，買進訊號")
    elif k > 80 and d > 80 and k < d:
        signals.append("KD 死亡交叉，賣出訊號")

    # 綜合判斷
    buy_count = sum(1 for s in signals if "買進" in s or "多頭" in s)
    sell_count = sum(1 for s in signals if "賣出" in s or "空頭" in s)

    if buy_count > sell_count:
        overall = "整體偏多，建議買進"
    elif sell_count > buy_count:
        overall = "整體偏空，建議賣出"

    return signals, overall

def colorize_night(value, thresholds, colors):
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

    latest_close = data["Close"].iloc[-1]
    prev_close = data["Close"].iloc[-2]

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
        st.markdown("### 🟢 指標分析（均線與動能）", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 18px;'>"
                    f"• <b>5MA:</b> {latest_5ma:.2f} &nbsp;&nbsp;"
                    f"• <b>10MA:</b> {latest_10ma:.2f} &nbsp;&nbsp;"
                    f"• <b>20MA:</b> {latest_20ma:.2f}</div>", unsafe_allow_html=True)

        rsi_color = colorize_night(latest_rsi, [30, 70], ["#6FCF97", "#F2F2F2", "#EB5757"])
        st.markdown(f"<div style='font-size: 18px;'>• <b>RSI:</b> <span style='color:{rsi_color}'>{latest_rsi:.2f}</span></div>", unsafe_allow_html=True)

        macd_color = "#6FCF97" if latest_macd > latest_signal else "#EB5757"
        st.markdown(f"<div style='font-size: 18px;'>• <b>MACD:</b> <span style='color:{macd_color}'>{latest_macd:.4f}</span>, <b>Signal:</b> {latest_signal:.4f}</div>", unsafe_allow_html=True)

        cci_color = colorize_night(latest_cci, [-100, 100], ["#6FCF97", "#F2F2F2", "#EB5757"])
        st.markdown(f"<div style='font-size: 18px;'>• <b>CCI:</b> <span style='color:{cci_color}'>{latest_cci:.2f}</span></div>", unsafe_allow_html=True)

        if latest_k < 20 and latest_d < 20 and latest_k > latest_d:
            kd_color = "#6FCF97"
        elif latest_k > 80 and latest_d > 80 and latest_k < latest_d:
            kd_color = "#EB5757"
        else:
            kd_color = "#F2F2F2"
        st.markdown(f"<div style='font-size: 18px;'>• <b>K:</b> <span style='color:{kd_color}'>{latest_k:.2f}</span>, <b>D:</b> <span style='color:{kd_color}'>{latest_d:.2f}</span></div>", unsafe_allow_html=True)

        st.markdown(f"<div style='font-size: 18px; margin-top: 10px;'><b>均線排列狀態：</b>{ma_status}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 🔵 趨勢區間與價格帶", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 18px;'>• <b>布林通道：</b>上軌 = {latest_upperbb:.2f}, 下軌 = {latest_lowerbb:.2f}</div>", unsafe_allow_html=True)
        if latest_boxhigh is not None and latest_boxlow is not None:
            st.markdown(f"<div style='font-size: 18px;'>• <b>箱型區間：</b>高點 = {latest_boxhigh:.2f}, 低點 = {latest_boxlow:.2f}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size: 18px; color:#888888;'>• 箱型區間資料不足</div>", unsafe_allow_html=True)

    signals, overall = evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)

    for s in signals:
        st.markdown(f"<div style='font-size: 18px; background-color:#1f2937; padding:8px; border-radius:5px; margin-top:6px; color:#cbd5e1;'>• {s}</div>", unsafe_allow_html=True)

    overall_color = "#6FCF97" if "買進" in overall else "#EB5757" if "賣出" in overall else "#F2A365"
    st.markdown(f"<div style='font-size: 20px; font-weight: bold; background-color:#111827; padding:12px; border-radius:8px; color:{overall_color}; margin-top:10px;'>"
                f"{overall}</div>", unsafe_allow_html=True)

    st.markdown("---")
