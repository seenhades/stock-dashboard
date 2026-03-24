import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

# === 設定區 ===
st.set_page_config(layout="wide", page_title="股票技術指標與資金管理監控")
st.title("📈 股票技術指標與凱利公式監控")

# 股票清單
stock_list = {
    "Panasonic 松下電器": "6752.T",
    "NTT 日本電信電話": "9432.T",
    "Mitsubishi Corp. 三菱商事": "8058.T",
    "1306 ETF": "1306.T",
    "燿華": "2367.TW",
    "銘異": "3060.TW",
    "茂矽": "2342.TW",
    "群電": "6412.TW",
    "台中銀": "2812.TW",
    "台新金": "2887.TW",
    "華新": "1605.TW",
    "香港中華燃氣": "0003.HK",
    "國泰航空": "0293.HK",
    "碧桂園": "2007.HK",
    "Shell 殼牌石油": "SHEL.L",
    "Rolls Royce 勞斯萊斯": "RR.L",
    "Porsche SE 保時捷控股": "PAH3.DE",
    "Porsche AG 保時捷製造": "P911.DE",
    "Infineon 英飛凌": "IFX.DE",
    "Organon 歐嘉隆": "OGN",
    "Pfizer 輝瑞": "PFE",
    "Smith & Wesson Brands": "SWBI",
}

# 設定參數
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=365) # 增加天數以確保 120MA 計算正確
REWARD_RISK_RATIO = 2.0  # 預設賺賠比 (獲利/虧損)

# === 技術指標計算函式 ===
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, span_short=12, span_long=26, signal_span=9):
    ema_short = series.ewm(span=span_short, adjust=False).mean()
    ema_long = series.ewm(span=span_long, adjust=False).mean()
    macd = ema_short - ema_long
    signal = macd.ewm(span=signal_span, adjust=False).mean()
    return macd, signal

def calculate_cci(data, period=20):
    tp = (data['High'] + data['Low'] + data['Close']) / 3
    sma = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.fabs(x - x.mean()).mean())
    return (tp - sma) / (0.015 * mad)

def calculate_kd(data, k_period=9, d_period=3):
    low_min = data['Low'].rolling(window=k_period).min()
    high_max = data['High'].rolling(window=k_period).max()
    rsv = (data['Close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=d_period-1, adjust=False).mean()
    d = k.ewm(com=d_period-1, adjust=False).mean()
    return k, d

def calculate_bollinger_bands(series, window=20, num_std=2):
    sma = series.rolling(window).mean()
    std = series.rolling(window).std()
    return sma + (num_std * std), sma - (num_std * std)

def calculate_box_range(series, period=20):
    return series.rolling(window=period).max(), series.rolling(window=period).min()

# === 趨勢與訊號評估函式 ===
def evaluate_ma_trend(ma5, ma10, ma20):
    if ma5 > ma10 > ma20: return "短期均線多頭排列 📈"
    elif ma5 < ma10 < ma20: return "短期均線空頭排列 📉"
    return "短期均線糾結 🔄"

def evaluate_ma_trend_mid(ma20, ma60, ma120):
    if ma20 > ma60 > ma120: return "中期均線多頭排列 📈"
    elif ma20 < ma60 < ma120: return "中期均線空頭排列 📉"
    return "中期均線糾結 🔄"

def calculate_expected_value(win_rate, b=REWARD_RISK_RATIO):
    """計算期望值: (勝率 * 賺賠比) - (敗率 * 1)"""
    return (win_rate * b) - (1 - win_rate)

def calculate_kelly(win_rate, b=REWARD_RISK_RATIO):
    """凱利公式: f* = (bp - q) / b"""
    p = win_rate
    q = 1 - p
    if b == 0: return 0
    f_star = (b * p - q) / b
    return max(0, f_star) # 負值代表不建議投資

def evaluate_signals(data_row):
    signals = []
    # 均線趨勢
    ma_s = evaluate_ma_trend(data_row['5MA'], data_row['10MA'], data_row['20MA'])
    ma_m = evaluate_ma_trend_mid(data_row['20MA'], data_row['60MA'], data_row['120MA'])
    if "多頭" in ma_s: signals.append("短期多頭 (買進)")
    if "多頭" in ma_m: signals.append("中期多頭 (買進)")
    if "空頭" in ma_s: signals.append("短期空頭 (賣出)")
    if "空頭" in ma_m: signals.append("中期空頭 (賣出)")

    # RSI
    if data_row['RSI'] < 30: signals.append("RSI超賣 (買進)")
    elif data_row['RSI'] > 70: signals.append("RSI超買 (賣出)")
    
    # MACD
    if data_row['MACD'] > data_row['Signal']: signals.append("MACD金叉 (買進)")
    else: signals.append("MACD死叉 (賣出)")

    # 布林 & 箱型
    if data_row['Close'] > data_row['UpperBB']: signals.append("突破布林上軌 (買進)")
    if data_row['Close'] > data_row['BoxHigh']: signals.append("突破箱型上緣 (買進)")
    if data_row['Close'] < data_row['LowerBB']: signals.append("跌破布林下軌 (賣出)")

    buy_cnt = sum(1 for s in signals if "買進" in s)
    sell_cnt = sum(1 for s in signals if "賣出" in s)
    
    # 計算估計勝率 (簡單模型：買進訊號佔比)
    total = buy_cnt + sell_cnt
    win_rate = buy_cnt / total if total > 0 else 0.5
    
    return signals, win_rate, ma_s, ma_m

# === UI 輔助函式 ===
def render_card(title, text, color):
    return f"""
    <div style='background-color: #f7f9fc; border-left: 6px solid {color}; padding: 12px; margin: 8px 0; border-radius: 4px;'>
        <div style='color: gray; font-size: 14px;'>{title}</div>
        <div style='color: {color}; font-size: 18px; font-weight: bold;'>{text}</div>
    </div>
    """

# === 主程式迴圈 ===
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
            data['5MA'] = data['Close'].rolling(5).mean()
            data['10MA'] = data['Close'].rolling(10).mean()
            data['20MA'] = data['Close'].rolling(20).mean()
            data['60MA'] = data['Close'].rolling(60).mean()
            data['120MA'] = data['Close'].rolling(120).mean()
            data['UpperBB'], data['LowerBB'] = calculate_bollinger_bands(data['Close'])
            data['BoxHigh'], data['BoxLow'] = calculate_box_range(data['Close'])
            
            # 取得最新一列
            latest = data.iloc[-1]
            prev_close = data['Close'].iloc[-2]
            
            # 評估與計算
            signals, win_rate, ma_s, ma_m = evaluate_signals(latest)
            ev = calculate_expected_value(win_rate)
            kelly_f = calculate_kelly(win_rate)
            
            # 顯示資訊
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("最新收盤價", f"{latest['Close']:.2f}", f"{latest['Close']-prev_close:+.2f}")
                st.write(f"**短期趨勢:** {ma_s}")
                st.write(f"**中期趨勢:** {ma_m}")
            
            with col2:
                ev_color = "green" if ev > 0 else "red"
                st.markdown(render_card("期望值 (EV)", f"{ev:.2f}", ev_color), unsafe_allow_html=True)
                st.markdown(render_card("估計勝率", f"{win_rate:.1%}", "blue"), unsafe_allow_html=True)

            with col3:
                kelly_color = "green" if kelly_f > 0.2 else "orange" if kelly_f > 0 else "red"
                st.markdown(render_card("凱利建議位階 (Kelly %)", f"{kelly_f:.1%}", kelly_color), unsafe_allow_html=True)
                
                status = "🟢 建議買進" if ev > 0 and kelly_f > 0 else "🔴 建議觀望/賣出"
                st.markdown(f"### 最終燈號: {status}")

            with st.expander("查看所有觸發訊號"):
                st.write(", ".join(signals))
            st.divider()

