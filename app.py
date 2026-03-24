import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

# === 1. 設定區 ===
st.set_page_config(layout="wide", page_title="股票技術指標與資金管理監控")
st.title("📈 股票技術指標與凱利公式監控 (含價位建議)")

# 股票清單 (從 PDF 擷取)
stock_list = {
    "1306 ETF": "1306.T", "Panasonic 松下電器": "6752.T", "Sony Group. 索尼集團": "6758.T",
    "NTT 日本電信電話": "9432.T", "英業達": "2356.TW", "希華": "2484.TW",
    "晶彩科": "3535.TW", "群電": "6412.TW", "康舒": "6282.TW",
    "台中銀": "2812.TW", "台新金": "2887.TW", "香港中華燃氣": "0003.HK",
    "國泰航空": "0293.HK", "碧桂園": "2007.HK", "Rolls Royce 勞斯萊斯": "RR.L",
    "Shell 殼牌石油": "SHEL.L", "Porsche SE 保時捷控股": "PAH3.DE",
    "Porsche AG 保時捷製造": "P911.DE", "Organon 歐嘉隆": "OGN",
    "Pfizer 輝瑞": "PFE", "Tower Semiconductor": "TSEM",
}

end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=365)
REWARD_RISK_RATIO = 2.0

# === 2. 技術指標與邏輯函式 ===
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    return 100 - (100 / (1 + rs))

def calculate_macd(series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_bollinger_bands(series, window=20, num_std=2):
    sma = series.rolling(window).mean()
    std = series.rolling(window).std()
    return sma + (num_std * std), sma - (num_std * std)

def calculate_box_range(series, period=20):
    return series.rolling(window=period).max(), series.rolling(window=period).min()

def evaluate_ma_trend(ma5, ma10, ma20):
    if ma5 > ma10 > ma20: return "短期多頭 📈"
    elif ma5 < ma10 < ma20: return "短期空頭 📉"
    return "短期糾結 🔄"

def evaluate_ma_trend_mid(ma20, ma60, ma120):
    if ma20 > ma60 > ma120: return "中期多頭 📈"
    elif ma20 < ma60 < ma120: return "中期空頭 📉"
    return "中期糾結 🔄"

def calculate_kelly(win_rate, b=REWARD_RISK_RATIO):
    p, q = win_rate, 1 - win_rate
    if b == 0: return 0
    f_star = (b * p - q) / b
    return max(0.0, float(f_star))

def evaluate_signals(d):
    signals = []
    ma_s = evaluate_ma_trend(d['5MA'], d['10MA'], d['20MA'])
    ma_m = evaluate_ma_trend_mid(d['20MA'], d['60MA'], d['120MA'])
    
    if "多頭" in ma_s: signals.append("短期多頭 (買進)")
    if "多頭" in ma_m: signals.append("中期多頭 (買進)")
    if "空頭" in ma_s: signals.append("短期空頭 (賣出)")
    if "空頭" in ma_m: signals.append("中期空頭 (賣出)")
    
    if d['RSI'] < 30: signals.append("RSI超賣 (買進)")
    elif d['RSI'] > 70: signals.append("RSI超買 (賣出)")
    
    if d['MACD'] > d['Signal']: signals.append("MACD金叉 (買進)")
    else: signals.append("MACD死叉 (賣出)")
    
    if d['Close'] > d['UpperBB']: signals.append("突破布林上軌 (買進)")
    if d['Close'] > d['BoxHigh']: signals.append("突破箱型上緣 (買進)")
    if d['Close'] < d['LowerBB']: signals.append("跌破布林下軌 (賣出)")
    
    buy_cnt = sum(1 for s in signals if "買進" in s)
    sell_cnt = sum(1 for s in signals if "賣出" in s)
    total = buy_cnt + sell_cnt
    win_rate = buy_cnt / total if total > 0 else 0.5
    return signals, win_rate, ma_s, ma_m, buy_cnt, sell_cnt

# --- 新增：價格建議函式 ---
def get_trade_advice(d):
    # 買進建議：參考布林下軌與箱型底部的平均
    suggested_buy = (d['LowerBB'] + d['BoxLow']) / 2
    # 賣出建議：參考布林上軌與箱型頂部的平均
    suggested_sell = (d['UpperBB'] + d['BoxHigh']) / 2
    return suggested_buy, suggested_sell

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
        current_stocks = {k: v for k, v in stock_list.items() if (v.endswith(suffixes[i]) if suffixes[i] else "." not in v)}
        
        for name, symbol in current_stocks.items():
            st.subheader(f"{name} ({symbol})")
            data = yf.download(symbol, start=start_date, end=end_date, interval="1d", progress=False)
            
            if data.empty or len(data) < 120:
                st.warning(f"{symbol} 資料不足")
                continue

            # 計算指標
            data['RSI'] = calculate_rsi(data['Close'])
            data['MACD'], data['Signal'] = calculate_macd(data['Close'])
            for m in [5, 10, 20, 60, 120]: data[f'{m}MA'] = data['Close'].rolling(m).mean()
            data['UpperBB'], data['LowerBB'] = calculate_bollinger_bands(data['Close'])
            data['BoxHigh'], data['BoxLow'] = calculate_box_range(data['Close'])

            try:
                # 數據提取
                def get_scalar(df, col, idx):
                    val = df[col].iloc[idx]
                    return float(val.iloc[0]) if isinstance(val, (pd.Series, pd.DataFrame)) else float(val)

                cols = ['Close', '5MA', '10MA', '20MA', '60MA', '120MA', 'RSI', 'MACD', 'Signal', 'UpperBB', 'LowerBB', 'BoxHigh', 'BoxLow']
                latest_vals = {c: get_scalar(data, c, -1) for c in cols}
                prev_close = get_scalar(data, 'Close', -2)

                # 執行評估與價位計算
                signals, win_rate, ma_s, ma_m, b_cnt, s_cnt = evaluate_signals(latest_vals)
                buy_price, sell_price = get_trade_advice(latest_vals)
                kelly_f = calculate_kelly(win_rate)
                ev = (win_rate * REWARD_RISK_RATIO) - (1 - win_rate)

                # 狀態判斷
                status_text, status_color = ("建議買進 (多頭強勢) 🟢", "green") if ev > 0.1 and kelly_f > 0 else \
                                           ("建議賣出 (空頭佔優) 🔴", "red") if ev < -0.1 or s_cnt > b_cnt else \
                                           ("建議觀望 (趨勢不明) 🟠", "orange")

                # UI 顯示
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("最新收盤價", f"{latest_vals['Close']:.2f}", f"{latest_vals['Close']-prev_close:+.2f}")
                    st.write(f"**短期:** {ma_s}")
                    st.write(f"**中期:** {ma_m}")
                with c2:
                    st.markdown(render_card("建議買進價位", f"≦ {buy_price:.2f}", "green"), unsafe_allow_html=True)
                    st.markdown(render_card("建議賣出價位", f"≧ {sell_price:.2f}", "red"), unsafe_allow_html=True)
                with c3:
                    st.markdown(render_card("預估勝率", f"{win_rate:.1%}", "blue"), unsafe_allow_html=True)
                    st.markdown(render_card("凱利建議位階", f"{kelly_f:.1%}", "purple"), unsafe_allow_html=True)
                with c4:
                    st.markdown(f"<div style='text-align: center; padding: 20px; border: 2px solid {status_color}; border-radius: 10px;'><h3 style='color: {status_color};'>{status_text}</h3></div>", unsafe_allow_html=True)

                with st.expander("詳細訊號分析"):
                    st.write(f"買進: {b_cnt} | 賣出: {s_cnt} | 期望值: {ev:.2f}")
                    st.info(", ".join(signals))

            except Exception as e:
                st.error(f"{symbol} 運算錯誤: {e}")
            st.divider()
