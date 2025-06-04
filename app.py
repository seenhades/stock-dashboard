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

end = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
start = end - datetime.timedelta(days=90)

# 技術指標函數...（略，保持原樣）
# evaluate_signals, colorize, 等函數保持原樣

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

    st.markdown("### 🧭 <b>均線與動能指標</b>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:18px;'>
    🔹 <b>5MA</b>: {0:.2f}, <b>10MA</b>: {1:.2f}, <b>20MA</b>: {2:.2f}<br>
    🔹 <b>RSI</b>: <span style='color:{3}'>{4:.2f}</span><br>
    🔹 <b>MACD</b>: <span style='color:{5}'>{6:.4f}</span>, Signal: {7:.4f}<br>
    🔹 <b>CCI</b>: <span style='color:{8}'>{9:.2f}</span><br>
    🔹 <b>K</b>: <span style='color:{10}'>{11:.2f}</span>, <b>D</b>: <span style='color:{10}'>{12:.2f}</span>
    </div>
    """.format(
        latest_5ma, latest_10ma, latest_20ma,
        colorize(latest_rsi, [30, 70], ["green", "white", "red"]), latest_rsi,
        "green" if latest_macd > latest_signal else "red", latest_macd, latest_signal,
        colorize(latest_cci, [-100, 100], ["green", "white", "red"]), latest_cci,
        "green" if latest_k > latest_d and latest_k < 20 else "red" if latest_k < latest_d and latest_k > 80 else "white",
        latest_k, latest_d
    ), unsafe_allow_html=True)

    st.markdown("### 📐 <b>趨勢區間與價格帶</b>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:18px;'>
    🔹 <b>布林通道</b>: 上軌 = {0:.2f}, 下軌 = {1:.2f}<br>
    🔹 <b>箱型區間</b>: 高點 = {2}, 低點 = {3}
    </div>
    """.format(
        latest_upperbb, latest_lowerbb,
        f"{latest_boxhigh:.2f}" if latest_boxhigh else "資料不足",
        f"{latest_boxlow:.2f}" if latest_boxlow else "資料不足"
    ), unsafe_allow_html=True)

    st.markdown("### 🧠 <b>指標分析</b>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='font-size:18px; background-color:#222; color:#eee; padding:10px; border-radius:6px;'>
    <b>🔸 均線：</b> {ma_status}<br>
    <b>🔸 RSI：</b> {evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)[0][0]}<br>
    <b>🔸 MACD：</b> {evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)[0][1]}<br>
    <b>🔸 CCI：</b> {evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)[0][2]}<br>
    <b>🔸 KD：</b> {evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)[0][3]}<br>
    <b>🔸 布林通道：</b> {"偏高" if latest_close > latest_upperbb else "偏低" if latest_close < latest_lowerbb else "中性"}<br>
    <b>🔸 箱型：</b> {"突破箱頂" if latest_close > latest_boxhigh else "跌破箱底" if latest_close < latest_boxlow else "箱內震盪"}
    </div>
    """, unsafe_allow_html=True)

    signals, overall = evaluate_signals(latest_rsi, latest_macd, latest_signal, latest_cci, latest_k, latest_d)
    for s in signals:
        st.markdown(f"<div style='font-size: 18px; background-color:#333; color:#ddd; padding:6px; border-radius:5px;'>{s}</div>", unsafe_allow_html=True)

    color = "lightgreen" if "買進" in overall else "salmon" if "賣出" in overall else "orange"
    st.markdown(f"<div style='font-size: 20px; font-weight: bold; background-color:#111; padding:8px; border-radius:8px; color:{color};'>{overall}</div>", unsafe_allow_html=True)
    st.markdown("---")
