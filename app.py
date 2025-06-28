import streamlit as st
import yfinance as yf
import datetime
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")
st.title("📈 股票技術指標與收盤價監控")

stock_list = {
    "Panasonic 松下電器": "6752.T",
    "NTT 日本電信電話": "9432.T",
    "1306 ETF": "1306.T",
    "燿華": "2367.TW",
    "銘異": "3060.TW",
    "台新金": "2887.TW",
    "國泰航空": "0293.HK",
    "碧桂園": "2007.HK",
    "中糧家佳康": "1610.HK",
    "Shell 殼牌石油": "SHEL.L",
    "Rolls Royce 勞斯萊斯": "RR.L",
    "Porsche SE 保時捷控股": "PAH3.DE",
    "Porsche AG 保時捷製造": "P911.DE",
    "Infineon 英飛凌": "IFX.DE",
    "Organon 歐嘉隆": "OGN",
    "Newmont 紐曼礦業": "NEM",
    "VanEck Gold ETF": "OUNZ",
}

end = datetime.datetime.now()
start = end - datetime.timedelta(days=250)

# === 指標計算函式 ===
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

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
    cci = (tp - sma) / (0.015 * mad)
    return cci

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
    upper_band = sma + num_std * std
    lower_band = sma - num_std * std
    return upper_band, lower_band

def calculate_box_range(series, period=20):
    upper = series.rolling(window=period).max()
    lower = series.rolling(window=period).min()
    return upper, lower
    
def evaluate_bollinger_box(close, upperbb, lowerbb, boxhigh, boxlow):
    signals = []
    if close > upperbb:
        signals.append("💡 突破布林上軌，可能進入強勢區")
    elif close < lowerbb:
        signals.append("⚠ 跌破布林下軌，可能轉弱")
    else:
        signals.append("📊 價格在布林通道內")

    if pd.notna(boxhigh) and close > boxhigh:
        signals.append("💡 突破箱型上緣")
    elif pd.notna(boxlow) and close < boxlow:
        signals.append("⚠ 跌破箱型下緣")
    else:
        signals.append("📊 價格在箱型區間內")

    return signals

def evaluate_ma_trend(ma5, ma10, ma20):
    if ma5 > ma10 > ma20:
        return "📈 短期均線呈多頭排列"
    elif ma5 < ma10 < ma20:
        return "📉 短期均線呈空頭排列"
    else:
        return "🔄 短期均線呈糾結狀態"

def evaluate_ma_trend_mid(ma20, ma60, ma120):
    if ma20 > ma60 > ma120:
        return "📈 中期均線呈多頭排列"
    elif ma20 < ma60 < ma120:
        return "📉 中期均線呈空頭排列"
    else:
        return "🔄 中期均線呈糾結狀態"

def evaluate_ma_cross(ma_cross_short, ma_cross_mid, label=""):
    if ma_cross_short > ma_cross_mid:
        return f"💰 {label}黃金交叉，買進訊號"
    elif ma_cross_short < ma_cross_mid:
        return f"⚠️ {label}死亡交叉，賣出訊號"
    else:
        return f"🔄 {label}均線重合，中性觀望"

def evaluate_signals(ma5, ma20, ma60, rsi, macd, signal, cci, k, d, close, upperbb, lowerbb, boxhigh, boxlow):
    signals = []

    # 均線交叉訊號
    ma_cross_short = evaluate_ma_cross(ma5, ma20, "5/20MA ")
    ma_cross_mid = evaluate_ma_cross(ma20, ma60, "20/60MA ")
    
    if "中性" not in ma_cross_short:
        st.markdown(render_card("", ma_cross_short, get_color(ma_cross_short)), unsafe_allow_html=True)
    if "中性" not in ma_cross_mid:
        st.markdown(render_card("", ma_cross_mid, get_color(ma_cross_mid)), unsafe_allow_html=True)

    # RSI 訊號
    if rsi < 20:
        signals.append("🧊 RSI過冷，可能超賣，買進訊號")
    elif rsi > 70:
        signals.append("🔥 RSI過熱，可能過買，賣出訊號")

    # MACD 訊號
    if macd > signal:
        signals.append("💰 MACD黃金交叉，買進訊號")
    else:
        signals.append("⚠️ MACD死亡交叉，賣出訊號")

    # CCI 訊號
    if cci < -100:
        signals.append("🧊 CCI過低，可能超賣，買進訊號")
    elif cci > 100:
        signals.append("🔥 CCI過高，可能過買，賣出訊號")

    # KD 訊號
    if k < 20 and d < 20 and k > d:
        signals.append("💰 KD低檔黃金交叉，買進訊號")
    elif k > 80 and d > 80 and k < d:
        signals.append("⚠️ KD高檔死亡交叉，賣出訊號")

    # 布林通道訊號
    if close > upperbb:
        signals.append("💡 突破布林上軌，可能過熱，賣出訊號")
    elif close < lowerbb:
        signals.append("⚠️ 跌破布林下軌，可能轉弱，賣出訊號")

    # 箱型訊號
    if pd.notna(boxhigh) and close > boxhigh:
        signals.append("💡 突破箱型上緣，買進訊號")
    elif pd.notna(boxlow) and close < boxlow:
        signals.append("⚠️ 跌破箱型下緣，賣出訊號")

    # 綜合評估
    buy_signals = sum(1 for s in signals if "買進" in s)
    sell_signals = sum(1 for s in signals if "賣出" in s)
    if buy_signals > sell_signals:
        overall = "🟢 綜合評估：買進"
    elif sell_signals > buy_signals:
        overall = "🔴 綜合評估：賣出"
    else:
        overall = "🟠 綜合評估：持有"

    return signals, overall


def colorize(value, thresholds, colors):
    if value < thresholds[0]:
        return colors[0]
    elif value > thresholds[1]:
        return colors[2]
    else:
        return colors[1]

# === 將股票依國家分類 ===
jp_stocks = {k: v for k, v in stock_list.items() if v.endswith(".T")}
tw_stocks = {k: v for k, v in stock_list.items() if v.endswith(".TW")}
hk_stocks = {k: v for k, v in stock_list.items() if v.endswith(".HK")}
uk_stocks = {k: v for k, v in stock_list.items() if v.endswith(".L")}
de_stocks = {k: v for k, v in stock_list.items() if v.endswith(".DE")}
us_stocks = {k: v for k, v in stock_list.items() if "." not in v}  # 無副檔名假設為美股


tabs = st.tabs(["🇯🇵 日本", "🇹🇼 台灣", "🇭🇰 香港", "🇬🇧 英國", "🇩🇪 德國", "🇺🇸 美國"])
stock_groups = [jp_stocks, tw_stocks, hk_stocks, uk_stocks, de_stocks, us_stocks]

for tab, stocks in zip(tabs, stock_groups):
    with tab:
        for name, symbol in stocks.items():
            st.subheader(f"{name} ({symbol})")
            data = yf.download(symbol, start=start, end=end, interval="1d")
            if data.empty or len(data) < 30:
                st.warning(f"{symbol} 資料不足或無法取得")
                continue

            try:
                latest_close = data["Close"].iloc[-1].item()
                prev_close = data["Close"].iloc[-2].item()
            except Exception as e:
                st.warning(f"{symbol} 收盤價讀取錯誤: {e}")
                continue

            if not (np.isfinite(latest_close) and np.isfinite(prev_close)):
                st.warning(f"{symbol} 收盤價非有效數值")
                continue

            # === 技術指標計算 ===
            data['RSI'] = calculate_rsi(data['Close'])
            data['MACD'], data['Signal'] = calculate_macd(data['Close'])
            data['CCI'] = calculate_cci(data)
            data['%K'], data['%D'] = calculate_kd(data)
            data['5MA'] = data['Close'].rolling(window=5).mean()
            data['10MA'] = data['Close'].rolling(window=10).mean()
            data['20MA'] = data['Close'].rolling(window=20).mean()
            data['60MA'] = data['Close'].rolling(window=60).mean()
            data['120MA'] = data['Close'].rolling(window=120).mean()
            data['UpperBB'], data['LowerBB'] = calculate_bollinger_bands(data['Close'])
            data['BoxHigh'], data['BoxLow'] = calculate_box_range(data['Close'])

            # === 最新值提取 ===
            latest_rsi = data['RSI'].iloc[-1]
            latest_macd = data['MACD'].iloc[-1]
            latest_signal = data['Signal'].iloc[-1]
            latest_cci = data['CCI'].iloc[-1]
            latest_k = data['%K'].iloc[-1]
            latest_d = data['%D'].iloc[-1]
            latest_5ma = data['5MA'].iloc[-1]
            latest_10ma = data['10MA'].iloc[-1]
            latest_20ma = data['20MA'].iloc[-1]
            latest_60ma = data['60MA'].iloc[-1]
            latest_120ma = data['120MA'].iloc[-1]
            latest_upperbb = data['UpperBB'].iloc[-1]
            latest_lowerbb = data['LowerBB'].iloc[-1]
            latest_boxhigh = data['BoxHigh'].iloc[-1]
            latest_boxlow = data['BoxLow'].iloc[-1]

            if not np.isfinite(latest_boxhigh) or not np.isfinite(latest_boxlow):
                latest_boxhigh = latest_boxlow = None

            ma_status = evaluate_ma_trend(latest_5ma, latest_10ma, latest_20ma)
            ma_status_mid = evaluate_ma_trend_mid(latest_20ma, latest_60ma, latest_120ma)

            st.metric("📌 最新收盤價", f"{latest_close:.2f}", f"{latest_close - prev_close:+.2f}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📊 <b>均線與動能指標</b>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 18px;'><b>5MA:</b> {latest_5ma:.2f}, <b>10MA:</b> {latest_10ma:.2f}, <b>20MA:</b> {latest_20ma:.2f}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 18px;'><b>20MA:</b> {latest_20ma:.2f}, <b>60MA:</b> {latest_60ma:.2f}, <b>120MA:</b> {latest_120ma:.2f}</div>", unsafe_allow_html=True)

                rsi_color = colorize(latest_rsi, [30, 70], ["green", "unsafe_allow_html=True", "red"])
                st.markdown(f"<div style='font-size: 18px;'><b>RSI:</b> <span style='color:{rsi_color}'>{latest_rsi:.2f}</span></div>", unsafe_allow_html=True)

                macd_color = "green" if latest_macd > latest_signal else "red"
                st.markdown(f"<div style='font-size: 18px;'><b>MACD:</b> <span style='color:{macd_color}'>{latest_macd:.4f}</span>, <b>Signal:</b> {latest_signal:.4f}</div>", unsafe_allow_html=True)

                cci_color = colorize(latest_cci, [-100, 100], ["green", "unsafe_allow_html=True", "red"])
                st.markdown(f"<div style='font-size: 18px;'><b>CCI:</b> <span style='color:{cci_color}'>{latest_cci:.2f}</span></div>", unsafe_allow_html=True)

                if latest_k < 20 and latest_d < 20 and latest_k > latest_d:
                    kd_color = "green"
                elif latest_k > 80 and latest_d > 80 and latest_k < latest_d:
                    kd_color = "red"
                else:
                    kd_color = "unsafe_allow_html=True"
                st.markdown(f"<div style='font-size: 18px;'><b>K:</b> <span style='color:{kd_color}'>{latest_k:.2f}</span>, <b>D:</b> <span style='color:{kd_color}'>{latest_d:.2f}</span></div>", unsafe_allow_html=True)

            with col2:
                st.markdown("### 📉 <b>趨勢區間與價格帶</b>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size: 18px;'><b>布林通道：</b>上軌 = {latest_upperbb:.2f}, 下軌 = {latest_lowerbb:.2f}</div>", unsafe_allow_html=True)
                if latest_boxhigh is not None and latest_boxlow is not None:
                    st.markdown(f"<div style='font-size: 18px;'><b>箱型區間：</b>高點 = {latest_boxhigh:.2f}, 低點 = {latest_boxlow:.2f}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='font-size: 18px; color:gray;'>箱型區間資料不足</div>", unsafe_allow_html=True)

            # 指標訊號卡片
            ma_color = (
                "green" if "多頭" in ma_status else
                "red" if "空頭" in ma_status else
                "orange"
            )
            st.markdown(
                f"""
                <div style='
                    background-color: #f7f9fc;
                    border-left: 6px solid {ma_color};
                    padding: 12px 16px;
                    margin: 12px 0;
                    font-size: 20px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                '>
                    <div> </div>
                    <div style='color:{ma_color}; font-weight: 600;'>{ma_status}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            ma_color_mid = (
                "green" if "多頭" in ma_status_mid else
                "red" if "空頭" in ma_status_mid else
                "orange"
            )
            st.markdown(
                f"""
                <div style='
                    background-color: #f7f9fc;
                    border-left: 6px solid {ma_color};
                    padding: 12px 16px;
                    margin: 12px 0;
                    font-size: 20px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                '>
                    <div> </div>
                    <div style='color:{ma_color_mid}; font-weight: 600;'>{ma_status_mid}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
            rsi_signal = ""
            if latest_rsi < 20:
                rsi_signal = "🧊 RSI過冷，可能超賣，買進訊號"
            elif latest_rsi > 70:
                rsi_signal = "🔥 RSI過熱，可能過買，賣出訊號"
            else:
                rsi_signal = "🔄 RSI中性"

            macd_signal = ""
            if latest_macd > latest_signal:
                macd_signal = "💰 MACD黃金交叉，買進訊號"
            else:
                macd_signal = "⚠️ MACD死亡交叉，賣出訊號"

            cci_signal = ""
            if latest_cci < -100:
                cci_signal = "🧊 CCI過低，可能超賣，買進訊號"
            elif latest_cci > 100:
                cci_signal = "🔥 CCI過高，可能過買，賣出訊號"
            else:
                cci_signal = "🔄 CCI中性"

            kd_signal = ""
            if latest_k < 20 and latest_d < 20 and latest_k > latest_d:
                kd_signal = "💰 KD低檔黃金交叉，買進訊號"
            elif latest_k > 80 and latest_d > 80 and latest_k < latest_d:
                kd_signal = "⚠️ KD高檔死亡交叉，賣出訊號"
            else:
                kd_signal = "🔄 KD中性"

            def render_card(icon, text, color):
                return f"""
                <div style='
                    background-color: #f7f9fc;
                    border-left: 6px solid {color};
                    padding: 12px 16px;
                    margin: 8px 0;
                    font-size: 20px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                '>
                    <div style='font-size: 24px;'>{icon}</div>
                    <div style='color:{color}; font-weight: 600;'>{text}</div>
                </div>
                """

            def get_color(signal_text):
                if "買進" in signal_text:
                    return "green"
                elif "賣出" in signal_text:
                    return "red"
                else:
                    return "orange"

            if rsi_signal != "🔄 RSI中性":
                st.markdown(render_card("", f"{rsi_signal}", get_color(rsi_signal)), unsafe_allow_html=True)
            st.markdown(render_card("", f"{macd_signal}", get_color(macd_signal)), unsafe_allow_html=True)
            if cci_signal != "🔄 CCI中性":
                st.markdown(render_card("", f"{cci_signal}", get_color(cci_signal)), unsafe_allow_html=True)
            if kd_signal != "🔄 KD中性":
                st.markdown(render_card("", f"{kd_signal}", get_color(kd_signal)), unsafe_allow_html=True)

            bollinger_box_signals = evaluate_bollinger_box(
                latest_close, latest_upperbb, latest_lowerbb,
                latest_boxhigh, latest_boxlow
            )
            for signal in bollinger_box_signals:
                if "📊" in signal:
                    continue
                color = get_color(signal)
                st.markdown(render_card("", signal, color), unsafe_allow_html=True)

            signals_list, overall_signal = evaluate_signals(
                latest_rsi, latest_macd, latest_signal,
                latest_cci, latest_k, latest_d,
                latest_close, latest_upperbb, latest_lowerbb,
                latest_boxhigh, latest_boxlow,
                latest_5ma, latest_20ma, latest_60ma
            )
            overall_color = get_color(overall_signal)
            st.markdown(render_card("", overall_signal, overall_color), unsafe_allow_html=True)

            st.markdown("---")
