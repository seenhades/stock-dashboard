import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd
import pandas_ta as ta  # 建議安裝 pandas_ta 來簡化複雜指標計算

# === 1. 設定區 ===
st.set_page_config(layout="wide", page_title="高級股票技術指標與量化監控")
st.title("🚀 全方位量化交易監控系統 (含 5 大新指標)")

# 股票清單
stock_list = {
    "1306 ETF": "1306.T", "Panasonic 松下電器": "6752.T", "Sony Group. 索尼集團": "6758.T",
    "NTT 日本電信電話": "9432.T", "英業達": "2356.TW", "希華": "2484.TW",
    "晶彩科": "3535.TW", "群電": "6412.TW", "康舒": "6282.TW",
    "台中銀": "2812.TW", "台新金": "2887.TW", "香港中華燃氣": "0003.HK",
    "國泰航空": "0293.HK", "Rolls Royce 勞斯萊斯": "RR.L",
    "Shell 殼牌石油": "SHEL.L", "Porsche SE": "PAH3.DE", "Pfizer 輝瑞": "PFE",
}

end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=365)

# === 2. 新增指標計算函式 ===
def calculate_advanced_indicators(df):
    # (1) KD 指標 (Stochastic)
    stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=9, d=3)
    df['K'], df['D'] = stoch['STOCHk_9_3_3'], stoch['STOCHd_9_3_3']
    
    # (2) 成交量變化 (Volume SMA)
    df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
    df['Vol_Ratio'] = df['Volume'] / df['Vol_MA20'] # 當前成交量與平均比值
    
    # (3) ATR (平均真實波幅) - 用於計算波動止損
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
    
    # (4) ADX (平均趨向指數) - 判斷趨勢強度
    adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    df['ADX'] = adx_df['ADX_14']
    
    # (5) EMA (指數平滑移動平均線) - 靈敏趨勢線
    df['EMA12'] = ta.ema(df['Close'], length=12)
    df['EMA26'] = ta.ema(df['Close'], length=26)
    
    return df

# === 3. 邏輯判斷優化 ===
def evaluate_advanced_signals(d):
    signals = []
    # KD 邏輯
    if d['K'] < 20 and d['K'] > d['D']: signals.append("KD低檔金叉 (強買)")
    elif d['K'] > 80 and d['K'] < d['D']: signals.append("KD高檔死叉 (強賣)")
    
    # ADX 趨勢強度邏輯
    trend_str = "強勁趨勢" if d['ADX'] > 25 else "盤整區間"
    
    # 成交量確認
    vol_str = "爆量確認" if d['Vol_Ratio'] > 1.5 else "量能平穩"
    if d['Vol_Ratio'] > 1.5 and d['Close'] > d['EMA12']: signals.append("價漲量增 (動能確認)")
    
    # 原始指標整合 (RSI, MACD 等...)
    if d['RSI'] < 30: signals.append("RSI超賣")
    
    # 綜合建議價位計算 (加入 ATR 波動考量)
    suggested_buy = d['Close'] - (1.5 * d['ATR'])  # 波動支撐買點
    suggested_sell = d['Close'] + (1.5 * d['ATR']) # 波動壓力賣點
    stop_loss = d['Close'] - (2.5 * d['ATR'])      # 寬鬆止損位
    
    return signals, trend_str, vol_str, suggested_buy, suggested_sell, stop_loss

# === 4. UI 介面與主程式 ===
tabs = st.tabs(["🇯🇵 日本", "🇹🇼 台灣", "🇭🇰 香港", "🇬🇧 英國", "🇩🇪 德國", "🇺🇸 美國"])
suffixes = {0: ".T", 1: ".TW", 2: ".HK", 3: ".L", 4: ".DE", 5: ""}

for i, tab in enumerate(tabs):
    with tab:
        curr_suffix = suffixes[i]
        stocks = {k: v for k, v in stock_list.items() if (v.endswith(curr_suffix) if curr_suffix else "." not in v)}
        
        for name, symbol in stocks.items():
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if data.empty or len(data) < 50: continue
            
            # 計算所有指標
            data = calculate_advanced_indicators(data)
            # 為了相容原本邏輯，計算基礎指標
            data['RSI'] = ta.rsi(data['Close'], length=14)
            
            # 提取最新數據
            last = data.iloc[-1].to_dict()
            prev_close = data['Close'].iloc[-2]
            
            # 執行進階評估
            sigs, trend, vol, buy_p, sell_p, sl_p = evaluate_advanced_signals(last)
            
            # --- 顯示介面 ---
            st.subheader(f"{name} ({symbol})")
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.metric("當前股價", f"{last['Close']:.2f}", f"{last['Close']-prev_close:+.2f}")
                st.write(f"📊 **趨勢強度:** {trend} (ADX:{last['ADX']:.1f})")
                st.write(f"🔊 **量能狀態:** {vol}")

            with c2:
                st.write("🎯 **進場參考 (ATR/EMA)**")
                st.info(f"建議買入: {buy_p:.2f}")
                st.warning(f"建議賣出: {sell_p:.2f}")
            
            with c3:
                st.write("🛡️ **風險管理**")
                st.error(f"建議止損位: {sl_p:.2f}")
                st.write(f"波動值 (ATR): {last['ATR']:.2f}")
                
            with c4:
                st.write("💡 **關鍵訊號**")
                for s in sigs:
                    st.caption(f"✅ {s}")
            
            st.divider()
