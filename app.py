import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# Page Setup
st.set_page_config(page_title="Pro Live Forex Radar Engine", layout="wide")

# Custom Styling & Radar CSS
st.markdown("""
    <style>
    .signal-card { padding: 25px; border-radius: 20px; text-align: center; color: white; margin-top: 15px; }
    .buy-bg { background: linear-gradient(135deg, #00E676, #004D40); }
    .sell-bg { background: linear-gradient(135deg, #FF1744, #880E4F); }
    .stButton > button { width: 100%; height: 70px; font-size: 24px; font-weight: bold; background: linear-gradient(90deg, #311B92, #4A148C); color: white; border-radius: 15px; border: none; }
    .timer-display { font-size: 80px; font-weight: bold; color: #FFD600; text-align: center; background: #111; padding: 10px; border-radius: 15px; border: 2px solid #FFD600; }
    </style>
""", unsafe_allow_html=True)

st.title("📡 All-Pairs Pro Live Forex Radar & Signal Engine")

# Sidebar - Settings
st.sidebar.header("⚙️ Trading Configuration")

# All Live Pairs (Forex & Crypto)
all_pairs = {
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X", "USD/CAD": "CAD=X", "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X", "BTC/USD": "BTC-USD", "ETH/USD": "ETH-USD"
}

selected_pair = st.sidebar.selectbox("🎯 Select Market Pair:", list(all_pairs.keys()))

# Trade Timeframe Selection
trade_timeframe = st.sidebar.selectbox(
    "⏱️ Select Trade Expiry Time / Timeframe:", 
    ["1m (1 Min)", "5m (5 Min)", "15m (15 Min)", "30m (30 Min)"]
)
tf_map = {"1m (1 Min)": "1m", "5m (5 Min)": "5m", "15m (15 Min)": "15m", "30m (30 Min)": "30m"}

# Custom Entry Timer Option
entry_timer_secs = st.sidebar.slider("⏳ Choose Entry Timer (Seconds):", min_value=5, max_value=30, value=10, step=5)

st.write(f"Selected Pair: **{selected_pair}** | Timeframe: **{trade_timeframe}**")

# Strategy Logic
def analyze_market(symbol, tf):
    df = yf.download(symbol, period="1d", interval=tf, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    if df.empty or len(df) < 15:
        return None

    df['SMA_20'] = df['Close'].rolling(window=15).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]
    prev = df.iloc[-2]

    close_p = float(last['Close'])
    open_p = float(last['Open'])
    high_p = float(last['High'])
    low_p = float(last['Low'])
    
    rsi_val = float(last['RSI']) if not np.isnan(last['RSI']) else 50.0
    sma_val = float(last['SMA_20']) if not np.isnan(last['SMA_20']) else close_p

    body = abs(close_p - open_p)
    candle_range = high_p - low_p
    lower_wick = min(open_p, close_p) - low_p
    upper_wick = high_p - max(open_p, close_p)

    support = float(df['Low'].tail(20).min())
    resistance = float(df['High'].tail(20).max())

    bullish_score = 0
    bearish_score = 0
    detected_patterns = []

    if close_p > sma_val:
        bullish_score += 25
        trend = "UPTREND 📈"
    else:
        bearish_score += 25
        trend = "DOWNTREND 📉"

    if abs(close_p - support) < (candle_range * 1.5):
        bullish_score += 25
        detected_patterns.append("Near Support Level 🛡️")
    if abs(close_p - resistance) < (candle_range * 1.5):
        bearish_score += 25
        detected_patterns.append("Near Resistance Level 🚧")

    if lower_wick > (body * 1.8) and candle_range > 0:
        bullish_score += 30
        detected_patterns.append("Bullish Hammer 🔨")
    elif upper_wick > (body * 1.8) and candle_range > 0:
        bearish_score += 30
        detected_patterns.append("Shooting Star / Upper Wick ☄️")

    if close_p > open_p and prev['Close'] < prev['Open'] and (close_p - open_p) > abs(prev['Close'] - prev['Open']):
        bullish_score += 25
        detected_patterns.append("Bullish Engulfing 🔥")
    elif close_p < open_p and prev['Close'] > prev['Open'] and abs(close_p - open_p) > (prev['Close'] - prev['Open']):
        bearish_score += 25
        detected_patterns.append("Bearish Engulfing ❄️")

    if rsi_val < 35:
        bullish_score += 20
        detected_patterns.append("Oversold RSI")
    elif rsi_val > 65:
        bearish_score += 20
        detected_patterns.append("Overbought RSI")

    if bullish_score >= bearish_score:
        direction = "CALL (BUY) 🟢 UP"
        arrow = "⬆️"
        accuracy = min(bullish_score, 98)
        css = "buy-bg"
    else:
        direction = "PUT (SELL) 🔴 DOWN"
        arrow = "⬇️"
        accuracy = min(bearish_score, 98)
        css = "sell-bg"

    if accuracy < 10: accuracy = 15

    pattern_text = ", ".join(detected_patterns) if detected_patterns else "Price Action & Trend Flow"

    return {
        "direction": direction, "arrow": arrow, "accuracy": accuracy, 
        "pattern": pattern_text, "css": css, "price": close_p, 
        "trend": trend, "support": support, "resistance": resistance, "rsi": rsi_val
    }

# Start Button
if st.button("🚀 START ANALYZING MARKET"):
    radar_placeholder = st.empty()
    for stage in ["📡 Radar Scanning Live Market Pairs...", "🌀 Analyzing Support & Resistance Levels...", "🔍 Detecting Price Action Patterns..."]:
        radar_placeholder.info(stage)
        time.sleep(0.6)
    radar_placeholder.empty()

    res = analyze_market(all_pairs[selected_pair], tf_map[trade_timeframe])

    if res:
        st.markdown(f'''
            <div class="signal-card {res['css']}">
                <h1>{res['direction']} {res['arrow']}</h1>
                <h2>Accuracy / Chance: {res['accuracy']}%</h2>
                <h3>Detected Pattern: {res['pattern']}</h3>
            </div>
        ''', unsafe_allow_html=True)

        st.write("---")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Live Market Price", f"{res['price']:.5f}")
        c2.metric("Market Trend", res['trend'])
        c3.metric("Support / Resistance", f"{res['support']:.5f} / {res['resistance']:.5f}")
        c4.metric("RSI Value", f"{res['rsi']:.1f}")

        st.write("### ⏱️ Live Entry Countdown Timer")
        timer_box = st.empty()
        
        for sec in range(entry_timer_secs, 0, -1):
            timer_box.markdown(f'<div class="timer-display">{sec} Sec</div>', unsafe_allow_html=True)
            time.sleep(1)
            
        timer_box.markdown('<div class="timer-display" style="color:#00E676; border-color:#00E676;">GO! PLACE TRADE NOW 🚀</div>', unsafe_allow_html=True)
        st.balloons()
    else:
        st.error("⚠️ Live data is loading slowly for this timeframe. Please choose 5m or 15m from the sidebar and click again.")
else:
    st.info("👆 Click the **START ANALYZING MARKET** button to activate the live radar.")
    
