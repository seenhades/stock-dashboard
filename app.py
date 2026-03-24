import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

# === 1. 設定區 ===
st.set_page_config(layout="wide", page_title="高級股票量化監控系統 (資金管理版)")
st.title("🚀 全方位量化交易監控系統 (含凱利公式資金管理)")

stock_list = {
    "1306 ETF": "1306.T", "Panasonic 松下": "6752.T", "Sony Group": "6758.T",
    "NTT 日本電信": "9432.T", "英業達": "2356.TW", "希華": "2484.TW",
    "晶彩科": "3535.TW", "群電": "6412.TW", "康舒": "6282.TW",
    "台中銀": "2812.TW", "台新金": "2887.TW", "碧桂園": "2007.HK",
    "香港中華燃氣": "0003.HK", "國泰航空": "0293.HK", "Rolls Royce": "RR.L", 
    "Shell": "SHEL.L", "Porsche SE": "PAH3.DE", "Porsche AG": "P911.DE",
    "Organon 歐嘉隆": "OGN", "Pfizer 輝瑞": "PFE", "Tower Semi": "TSEM"
}

end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=365)

# === 2. 技術指標計算函式 ===
def get_indicators(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df.index = df.index.tz_localize(None)
    close = df['Close'].astype(float).squeeze()
    high = df['High'].astype(float).squeeze()
    low = df['Low'].astype(float).squeeze()
    volume = df['Volume'].astype(float).squeeze()

    # (1) KD 指標
    low_min = low.rolling(window=9).min()
    high_max = high.rolling(window=9).max()
    rsv = (close - low_min) / (high_max - low_min + 1e-9) * 100
    df['K'] = rsv.ewm(com=2, adjust=False).mean()
    df['D'] = df['K'].ewm(com=2, adjust=False).mean()

    # (2) EMA / MA
    df['EMA12'] = close.ewm(span=12, adjust=False).mean()
    df['EMA26'] = close.ewm(span=26, adjust=False).mean()
    df['MA20'] = close.rolling(window=20).mean()

    # (3) ATR 平均真實波幅
    h_l = high - low
    h_pc = (high - close.shift(1)).abs()
    l_pc = (low - close.shift(1)).abs()
    tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()

    # (4) ADX & RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
    
    # (5) 布林通道
    df['UpperBB'] = df['MA20'] + (2 * close.rolling(window=20).std())
    df['LowerBB'] = df['MA20'] - (2 * close.rolling(window=20).std())

    # (6) 成交量
    df['Vol_MA20'] = volume.rolling(window=20).mean()
    df['Vol_Ratio'] = volume / (df['Vol_MA20'] + 1e-9)

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
tab_suffix = {0: ".T", 1: ".TW", 2: ".HK", 3: ".L", 4: ".DE", 5: "USA"}

for i, tab in enumerate(tabs):
    with tab:
        suffix = tab_suffix[i]
        stocks = {k: v for k, v in stock_list.items() if (v.endswith(suffix) if suffix != "USA" else "." not in v)}
        
        if not stocks:
            st.info("目前清單中無此區域股票")
            continue

        for name, symbol in stocks.items():
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if data.empty or len(data) < 30: continue
            
            data = get_indicators(data)
            last = data.iloc[-1]
            prev_close = data['Close'].iloc[-2]

            # --- 買賣點與止損位計算 ---
            buy_p = (last['LowerBB'] + last['EMA26']) / 2
            sell_p = (last['UpperBB'] + (last['Close'] + 1.5 * last['ATR'])) / 2
            stop_l = last['Close'] - (2 * last['ATR'])

            # --- 核心：期望值與凱利公式計算 ---
            # 勝率 (Win Rate): 以過去 20 天上漲機率估算
            win_count = (data['Close'].diff() > 0).tail(20).sum()
            win_p = win_count / 20
            # 賠率 (Odds): 預期獲利 / 預期風險
            reward = max(sell_p - last['Close'], 0)
            risk = max(last['Close'] - stop_l, 1e-9)
            b_odds = reward / risk
            # 期望值 (EV)
            ev = (win_p * b_odds) - (1 - win_p)
            # 凱利比例 (Kelly %) - 採保守下注 (max 確保不為負)
            kelly_f = max(ev / (b_odds + 1e-9), 0)

            # --- 評分系統 ---
            buy_score = 0
            if last['K'] < 30 and last['K'] > last['D']: buy_score += 1
            if last['RSI'] < 40: buy_score += 1
            if last['Vol_Ratio'] > 1.2: buy_score += 1
            
            if buy_score >= 2:
                status_text, status_color = "建議買進 (多頭訊號) 🟢", "green"
            elif last['RSI'] > 70 or last['Close'] > last['UpperBB']:
                status_text, status_color = "建議賣出 (空頭警戒) 🔴", "red"
            else:
                status_text, status_color = "建議觀望 (趨勢中性) 🟠", "orange"

            # --- 顯示介面 ---
            st.subheader(f"{name} ({symbol})")
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.metric("最新股價", f"{last['Close']:.2f}", f"{last['Close']-prev_close:+.2f}")
                st.write(f"**成交量比:** {last['Vol_Ratio']:.2f}x")
            
            with c2:
                st.markdown(render_card("買進建議位", f"≦ {buy_p:.2f}", "green"), unsafe_allow_html=True)
                st.markdown(render_card("賣出建議位", f"≧ {sell_p:.2f}", "red"), unsafe_allow_html=True)
            
            with c3:
                st.markdown(render_card("行動建議", status_text, status_color), unsafe_allow_html=True)
                st.write(f"**止損參考:** `{stop_l:.2f}`")

            with c4:
                st.write("📊 **資金管理 (Kelly)**")
                st.write(f"預期勝率: `{win_p*100:.0f}%` / 賠率: `{b_odds:.2f}`")
                st.write(f"交易期望值: `{ev:.2f}`")
                # 顯示建議倉位，並標註半凱利更安全
                st.success(f"建議倉位: **{kelly_f*100:.1f}%**")
                st.caption("*(建議使用半凱利，即減半投入)*")

            st.divider()
