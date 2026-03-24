import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

# === 1. 設定區 ===
st.set_page_config(layout="wide", page_title="高級股票量化監控 (手寫指標版)")
st.title("🚀 全方位量化交易監控系統 (純淨版)")

stock_list = {
    "1306 ETF": "1306.T", "Panasonic 松下電器": "6752.T", "Sony Group. 索尼集團": "6758.T",
    "NTT 日本電信電話": "9432.T", "英業達": "2356.TW", "希華": "2484.TW",
    "晶彩科": "3535.TW", "群電": "6412.TW", "康舒": "6282.TW",
    "台中銀": "2812.TW", "台新金": "2887.TW", "香港中華燃氣": "0003.HK",
    "國泰航空": "0293.HK", "Rolls Royce": "RR.L", "Shell": "SHEL.L",
}

end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=365)

# === 2. 手寫指標計算區 (無須外部套件) ===
def get_indicators(df):
    # (1) KD 指標
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(com=2, adjust=False).mean() # 1/3 平滑
    df['D'] = df['K'].ewm(com=2, adjust=False).mean()

    # (2) EMA 指數平滑均線 (12/26)
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()

    # (3) ATR 平均真實波幅
    h_l = df['High'] - df['Low']
    h_pc = (df['High'] - df['Close'].shift(1)).abs()
    l_pc = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()

    # (4) ADX 趨勢強度 (簡化版邏輯)
    up_move = df['High'].diff()
    down_move = df['Low'].diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    tr14 = tr.rolling(window=14).sum()
    plus_di = 100 * (pd.Series(plus_dm).rolling(14).sum() / tr14)
    minus_di = 100 * (pd.Series(minus_dm).rolling(14).sum() / tr14).values
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    df['ADX'] = dx.rolling(window=14).mean().values

    # (5) 成交量倍率
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_MA20']

    # 基礎指標 (RSI, Bollinger)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['Std20'] = df['Close'].rolling(window=20).std()
    df['UpperBB'] = df['MA20'] + (2 * df['Std20'])
    df['LowerBB'] = df['MA20'] - (2 * df['Std20'])
    
    return df

# === 3. 主程式 UI ===
tabs = st.tabs(["🇯🇵 日本", "🇹🇼 台灣", "🇭🇰 香港", "🇬🇧 英國", "🇺🇸 美國"])
suffixes = {0: ".T", 1: ".TW", 2: ".HK", 3: ".L", 4: ""}

for i, tab in enumerate(tabs):
    with tab:
        curr_suffix = suffixes[i]
        stocks = {k: v for k, v in stock_list.items() if (v.endswith(curr_suffix) if curr_suffix else "." not in v)}
        
        for name, symbol in stocks.items():
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if data.empty or len(data) < 50: continue
            
            data = get_indicators(data)
            last = data.iloc[-1]
            prev_close = data['Close'].iloc[-2]
            
            # --- 計算建議價位邏輯 ---
            # 買進：參考布林下軌、EMA26、與波動支撐的平均
            buy_price = (last['LowerBB'] + last['EMA26'] + (last['Close'] - 1.5 * last['ATR'])) / 3
            # 賣出：參考布林上軌與波動壓力的平均
            sell_price = (last['UpperBB'] + (last['Close'] + 1.5 * last['ATR'])) / 2
            # 止損：收盤價減去 2 倍 ATR
            stop_loss = last['Close'] - (2 * last['ATR'])

            # --- 顯示 ---
            st.subheader(f"{name} ({symbol})")
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.metric("最新股價", f"{last['Close']:.2f}", f"{last['Close']-prev_close:+.2f}")
                trend_status = "🔥 強勁趨勢" if last['ADX'] > 25 else "💤 盤整中"
                st.write(f"**趨勢強度:** {trend_status}")
                st.write(f"**量能比:** {last['Vol_Ratio']:.2f}x")

            with c2:
                st.write("🎯 **買賣點建議**")
                st.success(f"建議買入位: `{buy_price:.2f}`")
                st.error(f"建議賣出位: `{sell_price:.2f}`")
            
            with c3:
                st.write("🛡️ **風險控管**")
                st.warning(f"建議止損位: `{stop_loss:.2f}`")
                st.write(f"當前 RSI: `{last['RSI']:.1f}`")

            with c4:
                st.write("💡 **指標訊號**")
                if last['K'] < 20 and last['K'] > last['D']: st.caption("✅ KD 低檔金叉")
                if last['Vol_Ratio'] > 1.5: st.caption("✅ 帶量突破中")
                if last['Close'] > last['UpperBB']: st.caption("⚠️ 股價突破布林上軌")
                if last['RSI'] > 70: st.caption("⚠️ RSI 進入超買區")
            
            st.divider()
