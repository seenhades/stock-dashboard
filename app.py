import streamlit as st
import yfinance as yf
import datetime
import numpy as np

st.title("美股最新收盤價與前日價差")

stock_list = {
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "Microsoft": "MSFT",
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=10)

for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")

    data = yf.download(symbol, start=start, end=end, interval="1d")

    if data.empty or "Close" not in data.columns:
        st.warning(f"{symbol} 無法取得資料或無收盤價欄位")
        continue

    if len(data) < 2:
        st.warning(f"{symbol} 資料筆數不足，無法顯示前日價差")
        continue

    latest = data.iloc[-1]
    prev = data.iloc[-2]

    # 檢查是否為數值
    if np.isnan(latest['Close']) or np.isnan(prev['Close']):
        st.warning(f"{symbol} 收盤價為空值，跳過顯示")
        continue

    st.metric("最新收盤價", f"{latest['Close']:.2f}", f"{latest['Close'] - prev['Close']:+.2f}")
    st.markdown("---")
