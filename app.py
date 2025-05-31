import yfinance as yf
import streamlit as st
import pandas as pd
import datetime

# 假設這是你前面取得資料的程式
ticker = "AAPL"  # 可改成你想追蹤的股票
start_date = datetime.datetime.now() - datetime.timedelta(days=60)
data = yf.download(ticker, start=start_date)

# 技術指標：SMA20
data["SMA20"] = data["Close"].rolling(window=20).mean()

st.title(f"{ticker} 技術分析看板")

# 檢查資料是否為空
if not data.empty:
    # 處理 MultiIndex 欄位（如有）
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    st.subheader("收盤價與20日均線")

    # 顯示目前股價
    current_price = data["Close"].iloc[-1] if "Close" in data.columns else None
    if current_price is not None:
        st.metric("目前股價", f"{current_price:.2f}")
    else:
        st.warning("無法顯示目前股價")

    # 繪圖
    needed_cols = ["Close", "SMA20"]
    missing_cols = [col for col in needed_cols if col not in data.columns]

    if not missing_cols and len(data) >= 20:
        st.line_chart(data[needed_cols])
    else:
        st.warning(f"無法繪圖，缺少欄位：{', '.join(missing_cols)} 或資料筆數不足")
else:
    st.error("未成功取得資料，請確認股票代號或網路狀態")
