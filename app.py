import streamlit as st
import yfinance as yf
import datetime

st.title("📊 股票最新收盤價與價差")

stock_list = {
    "Organon": "OGN",
    "Infineon": "IFX.DE",
    "Shell": "SHEL.L",
    "1306 ETF": "1306.TW",
    "Newmont": "NEM",
    "Panasonic": "6752.T",
    "NTT": "9432.T"
}

# 抓取最近5天資料，確保有兩個交易日以上
end = datetime.datetime.now()
start = end - datetime.timedelta(days=7)

for name, symbol in stock_list.items():
    st.subheader(f"{name} ({symbol})")

    try:
        data = yf.download(symbol, start=start, end=end, interval="1d", progress=False)

        if data.empty or "Close" not in data.columns:
            st.warning(f"{symbol} 資料取得失敗或缺 Close 欄位")
            continue

        if len(data) < 2:
            st.warning(f"{symbol} 資料不足，至少需要兩天以上資料")
            continue

        latest_close = data["Close"].iloc[-1]
        prev_close = data["Close"].iloc[-2]
        diff = latest_close - prev_close

        st.metric(label="最新收盤價", value=f"{latest_close:.2f}", delta=f"{diff:+.2f}")

    except Exception as e:
        st.error(f"{symbol} 抓取資料時出錯: {e}")
