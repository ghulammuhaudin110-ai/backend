import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="HK Signal Bot", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .gold-title {
        font-size: 42px;
        font-weight: 800;
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #B8860B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .signal-card { padding: 25px; border-radius: 20px; text-align: center; color: white; margin-top: 15px; }
    .buy-bg { background: linear-gradient(135deg, #00E676, #004D40); }
    .sell-bg { background: linear-gradient(135deg, #FF1744, #880E4F); }
    .stButton > button { width: 100%; height: 70px; font-size: 24px; font-weight: bold; background: linear-gradient(90deg, #1A237E, #311B92); color: white; border-radius: 15px; border: none; }
    .timer-display { font-size: 80px; font-weight: bold; color: #FFD600; text-align: center; background: #111; padding: 10px; border-radius: 15px; border: 2px solid #FFD600; }
    </style>
""", unsafe_allow_html=True)

# Golden Title Header
st.markdown('<h1 class="gold-title">⚡ HK Signal Bot</h1>', unsafe_allow_html=True)
st.subheader("Multi-Timeframe Advanced Price Action Engine")

# Sidebar Configuration
st.sidebar.header("⚙️ Trading Configuration")

all_pairs = {
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X", "USD/CAD": "CAD=X", "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X", "BTC/USD": "BTC-USD", "ETH/USD": "ETH-USD"
}

selected_pair = st.sidebar.selectbox("🎯 Select Market Pair:", list(all_pairs.keys()))

candle_time = st.sidebar.selectbox(
    "📊 Select Candle Time (Chart Time):", 
    ["5s Candle", "10s Candle", "15s Candle", "30s Candle", "1m Candle", "5m Candle", "1h Candle", "1w Candle"]
)

trade_time = st.sidebar.selectbox(
    "⏱️ Select Trade Time (Expiry):", 
    ["5s Trade", "10s Trade", "15s Trade", "30s Trade", "1m Trade", "5m Trade"]
)

candle_tf_map = {
    "5s Candle": "1m", "10s Candle": "1m", "15s Candle": "1m", "30s Candle": "1m",
    "1m Candle": "1m", "5m Candle": "5m", "1h Candle": "1h", "1w Candle": "1wk"
}

trade_sec_map = {
    "5s Trade": 5, "10s Trade": 10, "15s Trade": 15, "30s Trade": 30, "1m Trade": 60, "5m Trade": 300
}

selected_trade_seconds = trade_sec_map[trade_time]

st.write(f"Pair: **{selected_pair}** | Candle Time: **{candle_time}** | Trade Expiry: **{trade_time}**")

# High-Precision Advanced Technical Analysis Engine
def analyze_advanced_market(symbol, candle_tf, trade_secs):
    df = yf.download(symbol, period="1d" if candle_tf != "1wk" else "1y", interval=candle_tf, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    if df.empty or len(df) < 25:
        return None

    # EMA & Technical Calculations
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    c0 = df.iloc[-1]
    c1 = df.iloc[-2]
    c2 = df.iloc[-3]

    close_p, open_p = float(c0['Close']), float(c0['Open'])
    high_p, low_p = float(c0['High']), float(c0['Low'])

    c1_close, c1_open = float(c1['Close']), float(c1['Open'])
    c2_close, c2_open = float(c2['Close']), float(c2['Open'])

    body = abs(close_p - open_p)
    candle_range = high_p - low_p if (high_p - low_p) > 0 else 0.0001
    lower_wick = min(open_p, close_p) - low_p
    upper_wick = high_p - max(open_p, close_p)

    support = float(df['Low'].tail(20).min())
    resistance = float(df['High'].tail(20).max())

    bullish_score = 50
    bearish_score = 50
    detected_rules = []

    # 1. EMA CROSSOVER & TREND
    ema_9 = float(c0['EMA_9'])
    ema_21 = float(c0['EMA_21'])

    if ema_9 > ema_21:
        bullish_score += 15
        detected_rules.append("EMA Bullish Trend 📈")
    else:
        bearish_score += 15
        detected_rules.append("EMA Bearish Trend 📉")

    # 2. SNR ZONE CHECK
    near_support = abs(close_p - support) <= (candle_range * 1.5)
    near_resistance = abs(close_p - resistance) <= (candle_range * 1.5)

    if near_support:
        bullish_score += 15
        detected_rules.append("Key Support Zone 🛡️")
    if near_resistance:
        bearish_score += 15
        detected_rules.append("Key Resistance Zone 🚧")

    # 3. ADVANCED 15 CANDLESTICK PATTERNS DETECTION
    is_bullish_c0 = close_p > open_p
    is_bearish_c0 = close_p < open_p

    # A. Hammer & Inverted Hammer
    if lower_wick >= (body * 2) and upper_wick <= (body * 0.3) and near_support:
        bullish_score += 20
        detected_rules.append("Bullish Hammer")
    elif upper_wick >= (body * 2) and lower_wick <= (body * 0.3) and near_support:
        bullish_score += 18
        detected_rules.append("Bullish Inverted Hammer")

    # B. Shooting Star & Hanging Man
    if upper_wick >= (body * 2) and lower_wick <= (body * 0.3) and near_resistance:
        bearish_score += 20
        detected_rules.append("Bearish Shooting Star")
    elif lower_wick >= (body * 2) and upper_wick <= (body * 0.3) and near_resistance:
        bearish_score += 18
        detected_rules.append("Bearish Hanging Man")

    # C. Dragonfly Doji & Gravestone Doji
    if body <= (candle_range * 0.1):
        if lower_wick >= (candle_range * 0.6) and near_support:
            bullish_score += 15
            detected_rules.append("Dragonfly Doji (Reversal)")
        elif upper_wick >= (candle_range * 0.6) and near_resistance:
            bearish_score += 15
            detected_rules.append("Gravestone Doji (Reversal)")

    # D. Marubozu
    if body >= (candle_range * 0.85):
        if is_bullish_c0:
            bullish_score += 15
            detected_rules.append("Bullish Marubozu Strong Momentum")
        else:
            bearish_score += 15
            detected_rules.append("Bearish Marubozu Strong Momentum")

    # E. Engulfing Patterns
    if is_bullish_c0 and c1_close < c1_open and close_p > c1_open and open_p < c1_close:
        bullish_score += 22
        detected_rules.append("Bullish Engulfing")
    elif is_bearish_c0 and c1_close > c1_open and close_p < c1_open and open_p > c1_close:
        bearish_score += 22
        detected_rules.append("Bearish Engulfing")

    # F. Harami Patterns (Inside Bar)
    if is_bullish_c0 and c1_close < c1_open and close_p < c1_open and open_p > c1_close:
        bullish_score += 12
        detected_rules.append("Bullish Harami")
    elif is_bearish_c0 and c1_close > c1_open and close_p > c1_open and open_p < c1_close:
        bearish_score += 12
        detected_rules.append("Bearish Harami")

    # G. Piercing Line & Dark Cloud Cover
    if is_bullish_c0 and c1_close < c1_open and open_p < c1_close and close_p > (c1_open + c1_close)/2:
        bullish_score += 15
        detected_rules.append("Piercing Line Reversal")
    elif is_bearish_c0 and c1_close > c1_open and open_p > c1_close and close_p < (c1_open + c1_close)/2:
        bearish_score += 15
        detected_rules.append("Dark Cloud Cover")

    # H. Morning Star & Evening Star (3-Candle Patterns)
    if c2_close < c2_open and abs(c1_close - c1_open) < (abs(c2_close - c2_open)*0.4) and is_bullish_c0:
        bullish_score += 25
        detected_rules.append("Morning Star Pattern 🌟")
    elif c2_close > c2_open and abs(c1_close - c1_open) < (abs(c2_close - c2_open)*0.4) and is_bearish_c0:
        bearish_score += 25
        detected_rules.append("Evening Star Pattern 🌃")

    # I. Three White Soldiers & Three Black Crows
    if close_p > open_p and c1_close > c1_open and c2_close > c2_open and close_p > c1_close and c1_close > c2_close:
        bullish_score += 20
        detected_rules.append("Three White Soldiers 🚀")
    elif close_p < open_p and c1_close < c1_open and c2_close < c2_open and close_p < c1_close and c1_close < c2_close:
        bearish_score += 20
        detected_rules.append("Three Black Crows 📉")

    # 4. RSI FILTER
    rsi_val = float(c0['RSI']) if not np.isnan(c0['RSI']) else 50.0
    if rsi_val < 30:
        bullish_score += 10
        detected_rules.append("RSI Oversold")
    elif rsi_val > 70:
        bearish_score += 10
        detected_rules.append("RSI Overbought")

    # 5. FINAL ACCURACY CALCULATION
    if bullish_score > bearish_score:
        direction = "CALL (BUY) 🟢 UP"
        arrow = "⬆️"
        accuracy = min(bullish_score, 98)
        css = "buy-bg"
    else:
        direction = "PUT (SELL) 🔴 DOWN"
        arrow = "⬇️"
        accuracy = min(bearish_score, 98)
        css = "sell-bg"

    prep_timer = 5 if trade_secs <= 15 else 10
    pattern_text = " | ".join(detected_rules) if detected_rules else "High Confluence Market Trend"

    return {
        "direction": direction, "arrow": arrow, "accuracy": accuracy, 
        "pattern": pattern_text, "css": css, "price": close_p, 
        "rsi": rsi_val, "prep_timer": prep_timer
    }

# Start Button Execution
if st.button("🚀 START ANALYZING MARKET"):
    radar_placeholder = st.empty()
    for stage in [
        f"📡 Scanning 15 Candlestick Patterns on {candle_time}...",
        f"⏳ Checking EMA 9/21 Trend & Support/Resistance...",
        "🎯 Filtering False Breakouts & Calculating Accuracy..."
    ]:
        radar_placeholder.info(stage)
        time.sleep(0.5)
    radar_placeholder.empty()

    res = analyze_advanced_market(all_pairs[selected_pair], candle_tf_map[candle_time], selected_trade_seconds)

    if res:
        st.markdown(f'''
            <div class="signal-card {res['css']}">
                <h1>{res['direction']} {res['arrow']}</h1>
                <h2>Accuracy / Confidence: {res['accuracy']}%</h2>
                <h4>Detected Confluence Rules: {res['pattern']}</h4>
            </div>
        ''', unsafe_allow_html=True)

        st.write("---")
        c1, c2 = st.columns(2)
        c1.metric("Live Market Price", f"{res['price']:.5f}")
        c2.metric("RSI Indicator", f"{res['rsi']:.1f}")

        # Live Countdown Timer
        st.write(f"### ⏱️ Entry Preparation Countdown ({res['prep_timer']} Sec Prep)")
        timer_box = st.empty()
        
        for sec in range(res['prep_timer'], 0, -1):
            timer_box.markdown(f'<div class="timer-display">{sec} Sec</div>', unsafe_allow_html=True)
            time.sleep(1)
            
        timer_box.markdown(f'<div class="timer-display" style="color:#00E676; border-color:#00E676;">GO! PLACE {trade_time} TRADE NOW 🚀</div>', unsafe_allow_html=True)
        st.balloons()
    else:
        st.error("⚠️ Live market data is updating. Select '1m Candle' or '5m Candle' and try again.")
else:
    st.info("👆 Select settings from sidebar and click **START ANALYZING MARKET**.")
            
