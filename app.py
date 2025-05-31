import streamlit as st
import yfinance as yf
import datetime
import numpy as np

st.title("多市場股票最新收盤價與前日價差")

stock_list = {
    "Organon (美股)": "OGN",
    "Newmont (美股)": "NEM",
    "Infineon (德股)": "IFX.DE",
    "Porsche SE (德股)": "PAH3.DE",
    "Shell (英股)": "SHEL.L",
    "1306 ETF (日股)": "1306.T",
    "Panasonic (日股)": "6752.T",
    "NTT (日股)": "9432.T",
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

    try:
        latest_close = data["Close"].iloc[-1].item()
        prev_close = data["Close"].iloc[-2].item()
    except Exception as e:
        st.warning(f"{symbol} 讀取收盤價錯誤: {e}")
        continue

    if not np.isfinite(latest_close) or not np.isfinite(prev_close):
        st.warning(f"{symbol} 收盤價為空值或非數值，跳過顯示")
        continue

    st.metric("最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")
    st.markdown("---")
