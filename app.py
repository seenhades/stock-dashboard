import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

# === 1. 設定區 ===
st.set_page_config(layout="wide", page_title="高級股票技術指標監控系統")
st.title("🚀 全方位量化交易監控系統 (穩定版)")

# 股票清單
stock_list = {
    "1306 ETF": "1306.T", "Panasonic 松下電器": "6752.T", "Sony Group": "6758.T",
    "NTT 日本電信": "9432.T", "英業達": "2356.TW", "希華": "2484.TW",
    "晶彩科": "3535.TW", "群電": "6412.TW", "康舒": "6282.TW",
    "台中銀": "2812.TW", "台新金": "2887.TW", "香港中華燃氣": "0003.HK",
    "國泰航空": "0293.HK", "Rolls Royce": "RR.L", "Shell": "SHEL.L",
}

end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=365)

# === 2. 技術指標計算函式 (修正維度問題) ===
def get_indicators(df):
    # 確保數據是一維的 (處理 yfinance 的 MultiIndex 問題)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    volume = df['Volume'].squeeze()

    # (1) KD 指標
    low_min = low.rolling(window=9).min()
    high_max = high.rolling(window=9).max()
    rsv = (close - low_min) / (high_max - low_min + 1e-9) * 100
    df['K'] = rsv.ewm(com=2, adjust=False).mean()
    df['D'] = df['K'].ewm(com=2, adjust=False).mean()

    # (2) EMA (12/26)
    df['EMA12'] = close.ewm(span=12, adjust=False).mean()
    df['EMA26'] = close.ewm(span=26, adjust=False).mean()

    # (3) ATR 平均真實波幅
    h_l = high - low
    h_pc = (high - close.shift(1)).abs()
    l_pc = (low - close.shift(1)).abs()
    tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()

    # (4) ADX 趨勢強度
    up_move = high.diff()
    down_move = low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0).flatten()
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0).flatten()
    tr14 = tr.rolling(window=14).sum()
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(14).sum() / (tr14 + 1e-9))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(14).sum() / (tr14 + 1e-9))
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)) * 100
    df['ADX'] = dx.rolling(window=14).mean()

    # (5) 成交量倍率
    df['Vol_MA20'] = volume.rolling(window=20).mean()
    df['Vol_Ratio'] = volume / (df['Vol_MA20'] + 1e-9)

    # 基礎指標 (RSI, Bollinger, Box)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    df['MA20'] = close.rolling(window=20).mean()
    df['UpperBB'] = df['MA20'] + (2 * close.rolling(window=20).std())
    df['LowerBB'] = df['MA20'] - (2 * close.rolling(window=20).std())
    df['BoxHigh'] = high.rolling(window=20).max()
    df['BoxLow'] = low.rolling(window=20).min()
    
    return df

# === 3. UI 輔助函式 ===
def render_card(title, text, color):
    return f"""
    <div style='background-color: #f7f9fc; border-left: 6px solid {color}; padding: 12px; margin: 8px 0; border-radius: 4px;'>
        <div style='color: gray; font-size: 14px;'>{title}</div>
        <div style='color: {color}; font-size: 18px; font-weight: bold;'>{text}</div>
    </div>
    """

# === 4. 主程式迴圈 ===
tabs = st.tabs(["🇯🇵 日本", "🇹🇼 台灣", "🇭🇰 香港", "🇬🇧 英國", "🇩🇪 德國", "🇺🇸 美國"])
suffixes = {0: ".T", 1: ".TW", 2: ".HK", 3: ".L", 4: ".DE", 5: ""}

for i, tab in enumerate(tabs):
    with tab:
        curr_suffix = suffixes[i]
        stocks = {k: v for k, v in stock_list.items() if (v.endswith(curr_suffix) if curr_suffix else "." not in v)}
        
        for name, symbol in stocks.items():
            st.subheader(f"{name} ({symbol})")
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if data.empty or len(data) < 50:
                st.warning(f"{symbol} 資料不足或下載失敗")
                continue
            
            data = get_indicators(data)
            last = data.iloc[-1]
            prev_close = data['Close'].iloc[-2]
            
            # --- 計算建議價位邏輯 ---
            buy_price = (last['LowerBB'] + last['EMA26'] + (last['Close'] - 1.5 * last['ATR'])) / 3
            sell_price = (last['UpperBB'] + (last['Close'] + 1.5 * last['ATR'])) / 2
            stop_loss = last['Close'] - (2 * last['ATR'])

            # --- 顯示介面 ---
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.metric("最新股價", f"{last['Close']:.2f}", f"{last['Close']-prev_close:+.2f}")
                trend_text = "🔥 強勁趨勢" if last['ADX'] > 25 else "💤 盤整區間"
                st.write(f"**趨勢強度:** {trend_text}")
                st.write(f"**成交量比:** {last['Vol_Ratio']:.2f}x")

            with c2:
                st.markdown(render_card("建議買進價位", f"≦ {buy_price:.2f}", "green"), unsafe_allow_html=True)
                st.markdown(render_card("建議賣出價位", f"≧ {sell_price:.2f}", "red"), unsafe_allow_html=True)
            
            with c3:
                st.markdown(render_card("建議止損位", f"{stop_loss:.2f}", "orange"), unsafe_allow_html=True)
                st.write(f"**RSI:** {last['RSI']:.1f}")
                st.write(f"**KD:** {last['K']:.1f} / {last['D']:.1f}")
                
            with c4:
                st.write("💡 **關鍵訊號提示**")
                if last['K'] < 20 and last['K'] > last['D']: st.success("✅ KD 低檔金叉 (買進)")
                if last['Vol_Ratio'] > 1.5 and last['Close'] > prev_close: st.success("✅ 帶量攻擊 (買進)")
                if last['RSI'] > 70: st.warning("⚠️ 超買警戒 (觀望)")
                if last['Close'] < last['LowerBB']: st.info("ℹ️ 觸及布林下軌 (支撐)")

            st.divider()
