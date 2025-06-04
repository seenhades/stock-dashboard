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

# 取得歷史資料
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=100)
data = ticker.history(start=start_date, end=end_date)
data.dropna(inplace=True)

# 計算技術指標
data['MA5'] = data['Close'].rolling(window=5).mean()
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA60'] = data['Close'].rolling(window=60).mean()

data['RSI'] = 100 - (100 / (1 + data['Close'].pct_change().rolling(window=14).mean() /
                               data['Close'].pct_change().rolling(window=14).std()))

exp1 = data['Close'].ewm(span=12, adjust=False).mean()
exp2 = data['Close'].ewm(span=26, adjust=False).mean()
data['MACD'] = exp1 - exp2
data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

cci = (data['Close'] - (data['High'] + data['Low'] + data['Close']) / 3)
cci = cci / (0.015 * (data['Close'].rolling(20).std()))
data['CCI'] = cci

data['K'] = data['Close'].rolling(window=9).apply(lambda x: (x[-1] - x.min()) / (x.max() - x.min()) * 100)
data['D'] = data['K'].rolling(window=3).mean()

# 最新一筆資料
latest = data.iloc[-1]
rsi = latest['RSI']
macd = latest['MACD']
signal = latest['Signal']
cci = latest['CCI']
k_value = latest['K']
d_value = latest['D']

# 均線排列分析
if latest['MA5'] > latest['MA20'] > latest['MA60']:
    ma_analysis = "多頭排列"
elif latest['MA5'] < latest['MA20'] < latest['MA60']:
    ma_analysis = "空頭排列"
else:
    ma_analysis = "均線糾結"

# MACD 訊號
if macd > signal:
    macd_signal = "黃金交叉"
elif macd < signal:
    macd_signal = "死亡交叉"
else:
    macd_signal = "無明確交叉"

# === Streamlit UI ===
st.set_page_config(page_title="技術指標卡片", layout="centered")
st.title("📊 股票技術指標分析卡片")

# === 均線排列卡片 ===
if ma_analysis == "多頭排列":
    st.markdown("#### 📈 <span style='color:green'>均線呈多頭排列</span>", unsafe_allow_html=True)
elif ma_analysis == "空頭排列":
    st.markdown("#### 📉 <span style='color:red'>均線呈空頭排列</span>", unsafe_allow_html=True)
else:
    st.markdown("#### ➰ <span style='color:orange'>均線糾結，盤整訊號</span>", unsafe_allow_html=True)

st.markdown("---")

# === RSI 卡片 ===
if rsi > 70:
    st.markdown(f"#### 🔥 <span style='color:red'>RSI過熱，可能過買，賣出訊號</span>", unsafe_allow_html=True)
elif rsi < 30:
    st.markdown(f"#### ❄️ <span style='color:green'>RSI偏低，可能過賣，買進訊號</span>", unsafe_allow_html=True)

st.markdown("---")

# === MACD 卡片 ===
if macd_signal == "黃金交叉":
    st.markdown(f"#### 💰 <span style='color:green'>MACD黃金交叉，買進訊號</span>", unsafe_allow_html=True)
elif macd_signal == "死亡交叉":
    st.markdown(f"#### 💣 <span style='color:red'>MACD死亡交叉，賣出訊號</span>", unsafe_allow_html=True)

st.markdown("---")

# === CCI 卡片 ===
if cci > 100:
    st.markdown(f"#### 🔥 <span style='color:red'>CCI過高，可能過買，賣出訊號</span>", unsafe_allow_html=True)
elif cci < -100:
    st.markdown(f"#### ❄️ <span style='color:green'>CCI過低，可能過賣，買進訊號</span>", unsafe_allow_html=True)

st.markdown("---")

# === KD 卡片 ===（中性不顯示）
if k_value > 80 and d_value > 80:
    st.markdown(f"#### 🔃 <span style='color:red'>KD高檔，可能過熱</span>", unsafe_allow_html=True)
elif k_value < 20 and d_value < 20:
    st.markdown(f"#### 🔃 <span style='color:green'>KD低檔，可能反彈</span>", unsafe_allow_html=True)

st.markdown("---")

# === 綜合評估 ===
signals = []
if rsi > 70:
    signals.append("賣出")
elif rsi < 30:
    signals.append("買進")
if macd_signal == "黃金交叉":
    signals.append("買進")
elif macd_signal == "死亡交叉":
    signals.append("賣出")
if cci > 100:
    signals.append("賣出")
elif cci < -100:
    signals.append("買進")
if k_value > 80 and d_value > 80:
    signals.append("賣出")
elif k_value < 20 and d_value < 20:
    signals.append("買進")

buy_count = signals.count("買進")
sell_count = signals.count("賣出")

if sell_count > buy_count:
    overall = "<span style='color:red'>🔴 綜合評估：賣出</span>"
elif buy_count > sell_count:
    overall = "<span style='color:green'>🟢 綜合評估：買進</span>"
else:
    overall = "<span style='color:gray'>⚪ 綜合評估：觀望</span>"

st.markdown(f"### {overall}", unsafe_allow_html=True)
