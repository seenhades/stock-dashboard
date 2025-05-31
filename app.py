import streamlit as st
import yfinance as yf
import datetime
import numpy as np

st.title("日本股票最新收盤價與前日價差")

stock_list = {
    "Panasonic": "6752.T",
    "NTT": "9432.T",
    "1306 ETF（日股ETF）": "1306.T",
    "Sony": "6758.T",
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=10)

for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")

    data = yf.download(symbol, start=start, end=end, interval="1d")

    if data.empty or "Close" not in data.columns:
        st.warning(f"{symbol} 資料抓取失敗或無收盤價資料。")
        continue

    if len(data) < 2:
        st.warning(f"{symbol} 資料筆數不足，無法計算前日價差。")
        continue

    latest = data.iloc[-1]
    prev = data.iloc[-2]

    # 檢查是否有NaN或非數字
    if np.isnan(latest['Close']) or np.isnan(prev['Close']):
        st.warning(f"{symbol} 最新或前日收盤價為空值，無法顯示。")
        continue

    st.metric("最新收盤價", f"{latest['Close']:.2f}", f"{latest['Close'] - prev['Close']:+.2f}")
    st.markdown("---")
