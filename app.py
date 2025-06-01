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
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=90)

@st.cache_data(ttl=86400)
def fetch_fundamentals(symbol):
    ticker = yf.Ticker(symbol)
    try:
        # EPS: 最近年度
        eps = ticker.info.get("trailingEps")

        # PB: Price / Book
        pb = ticker.info.get("priceToBook")

        # 用歷史資料估算年度平均價（去年）
        today = datetime.date.today()
        year_start = f"{today.year - 1}-01-01"
        year_end = f"{today.year - 1}-12-31"
        hist = ticker.history(start=year_start, end=year_end)
        avg_price = hist['Close'].mean() if not hist.empty else None

        pe = avg_price / eps if eps and avg_price else None
        return eps, avg_price, pe, pb
    except Exception:
        return None, None, None, None

# ...其餘技術指標計算函式與主邏輯維持不變...

    # 放在 evaluate_signals 結果之後：
    eps, avg_price, pe, pb = fetch_fundamentals(symbol)
    if eps:
        st.markdown("### 🧾 財務指標（最新年度）")
        st.markdown(f"<div style='font-size:18px'>EPS：{eps:.2f}</div>", unsafe_allow_html=True)
        if avg_price:
            st.markdown(f"<div style='font-size:18px'>年度平均股價：約 {avg_price:.2f}</div>", unsafe_allow_html=True)
        if pe:
            st.markdown(f"<div style='font-size:18px'>本益比（PE）：{pe:.2f}</div>", unsafe_allow_html=True)
        if pb:
            st.markdown(f"<div style='font-size:18px'>股價淨值比（PB）：{pb:.2f}</div>", unsafe_allow_html=True)
    else:
        st.info("無法取得財報指標資料")
