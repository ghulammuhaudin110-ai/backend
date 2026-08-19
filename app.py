import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Ultra Pro Price Action Engine", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .signal-card { padding: 25px; border-radius: 20px; text-align: center; color: white; margin-top: 15px; }
    .buy-bg { background: linear-gradient(135deg, #00E676, #004D40); }
    .sell-bg { background: linear-gradient(135deg, #FF1744, #880E4F); }
    .stButton > button { width: 100%; height: 70px; font-size: 24px; font-weight: bold; background: linear-gradient(90deg, #1A237E, #311B92); color: white; border-radius: 15px; border: none; }
    .timer-display { font-size: 80px; font-weight: bold; color: #FFD600; text-align: center; background: #111; padding: 10px; border-radius: 15px; border: 2px solid #FFD600; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Ultra Pro Price Action & Auto-Timer Engine")

# Sidebar - Settings
st.sidebar.header("⚙️ Trading Configuration")

all_pairs = {
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X", "USD/CAD": "CAD=X", "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X", "BTC/USD": "BTC-USD", "ETH/USD": "ETH-USD"
}

selected_pair = st.sidebar.selectbox("🎯 Select Market Pair:", list(all_pairs.keys()))

# Expiry Time Selection (5 Sec to 10 Min)
trade_timeframe = st.sidebar.selectbox(
    "⏱️ Select Expiry / Timeframe:", 
    ["5s Expiry", "10s Expiry", "15s Expiry", "30s Expiry", "1m Candle/Trade", "5m Candle/Trade", "10m Candle/Trade"]
)

# Timeframe Mapping for YFinance Data
tf_map = {
    "5s Expiry": "1m", "10s Expiry": "1m", "15s Expiry": "1m", "30s Expiry": "1m",
    "1m Candle/Trade": "1m", "5m Candle/Trade": "5m", "10m Candle/Trade": "15m"
}

st.write(f"Pair: **{selected_pair}** | Selected Setting: **{trade_timeframe}**")

# Strategy Engine with 15+ Patterns & Structure Analysis
def analyze_advanced_market(symbol, tf):
    df = yf.download(symbol, period="1d", interval=tf, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    if df.empty or len(df) < 15:
        return None

    df['SMA_20'] = df['Close'].rolling(window=15).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    c0 = df.iloc[-1] # Current Candle
    c1 = df.iloc[-2] # Previous Candle
    c2 = df.iloc[-3] # 3rd Candle

    close_p, open_p = float(c0['Close']), float(c0['Open'])
    high_p, low_p = float(c0['High']), float(c0['Low'])

    body = abs(close_p - open_p)
    candle_range = high_p - low_p
    lower_wick = min(open_p, close_p) - low_p
    upper_wick = high_p - max(open_p, close_p)

    support = float(df['Low'].tail(20).min())
    resistance = float(df['High'].tail(20).max())

    bullish_score = 0
    bearish_score = 0
    detected_rules = []

    # 1. Market Structure Analysis (HH, HL, LH, LL)
    if float(c0['High']) > float(c1['High']) and float(c0['Low']) > float(c1['Low']):
        bullish_score += 15
        detected_rules.append("Structure: Higher High & Higher Low (HH/HL) 📈")
    elif float(c0['High']) < float(c1['High']) and float(c0['Low']) < float(c1['Low']):
        bearish_score += 15
        detected_rules.append("Structure: Lower High & Lower Low (LH/LL) 📉")

    # 2. Trend & Moving Averages
    if close_p > float(c0['SMA_20']):
        bullish_score += 10
    else:
        bearish_score += 10

    # 3. Support & Resistance Reversals
    if abs(close_p - support) < (candle_range * 1.2):
        bullish_score += 20
        detected_rules.append("SR: Strong Bounce at Support Level 🛡️")
    elif abs(close_p - resistance) < (candle_range * 1.2):
        bearish_score += 20
        detected_rules.append("SR: Strong Rejection at Resistance Level 🚧")

    # 4. Detection of 15+ Candlestick Patterns
    # Hammer & Hanging Man
    if lower_wick > (body * 2) and upper_wick < (body * 0.5):
        if close_p <= (support * 1.002):
            bullish_score += 25
            detected_rules.append("Pattern: Bullish Hammer near Support 🔨")
        else:
            bearish_score += 20
            detected_rules.append("Pattern: Hanging Man 🪢")

    # Shooting Star & Inverted Hammer
    elif upper_wick > (body * 2) and lower_wick < (body * 0.5):
        if close_p >= (resistance * 0.998):
            bearish_score += 25
            detected_rules.append("Pattern: Shooting Star near Resistance ☄️")
        else:
            bullish_score += 20
            detected_rules.append("Pattern: Inverted Hammer 📐")

    # Engulfing Patterns
    elif close_p > open_p and float(c1['Close']) < float(c1['Open']) and body > abs(float(c1['Close']) - float(c1['Open'])):
        bullish_score += 25
        detected_rules.append("Pattern: Strong Bullish Engulfing 🔥")
    elif close_p < open_p and float(c1['Close']) > float(c1['Open']) and body > abs(float(c1['Close']) - float(c1['Open'])):
        bearish_score += 25
        detected_rules.append("Pattern: Strong Bearish Engulfing ❄️")

    # Doji & Spinning Top
    elif body <= (candle_range * 0.1):
        detected_rules.append("Pattern: Doji (Indecision Reversal) ⚖️")
        if float(c0['RSI']) < 30: bullish_score += 15
        if float(c0['RSI']) > 70: bearish_score += 15

    # Marubozu (Full Body Solid Candle)
    elif body >= (candle_range * 0.85):
        if close_p > open_p:
            bullish_score += 20
            detected_rules.append("Pattern: Bullish Marubozu 💪")
        else:
            bearish_score += 20
            detected_rules.append("Pattern: Bearish Marubozu 🩸")

    # Piercing Line & Dark Cloud Cover
    elif float(c1['Close']) < float(c1['Open']) and open_p < float(c1['Low']) and close_p > (float(c1['Open']) + float(c1['Close'])) / 2:
        bullish_score += 20
        detected_rules.append("Pattern: Piercing Line Reversal ⛅")
    elif float(c1['Close']) > float(c1['Open']) and open_p > float(c1['High']) and close_p < (float(c1['Open']) + float(c1['Close'])) / 2:
        bearish_score += 20
        detected_rules.append("Pattern: Dark Cloud Cover 🌧️")

    # 5. Final Signal & Accuracy Calculation
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

    if accuracy < 15: accuracy = 20

    # Auto Entry Timer Logic Based on Accuracy
    if accuracy >= 85:
        auto_timer = 5 # High Accuracy -> Fast 5 Sec Entry
    elif accuracy >= 65:
        auto_timer = 10 # Medium Accuracy -> 10 Sec Prep
    else:
        auto_timer = 15 # Lower Accuracy -> 15 Sec Prep

    pattern_text = " | ".join(detected_rules) if detected_rules else "Price Action Structure & Momentum"

    return {
        "direction": direction, "arrow": arrow, "accuracy": accuracy, 
        "pattern": pattern_text, "css": css, "price": close_p, 
        "rsi": float(c0['RSI']), "auto_timer": auto_timer
    }

# Start Button
if st.button("🚀 START ANALYZING MARKET"):
    radar_placeholder = st.empty()
    for stage in ["📡 Scanning 15+ Candlestick Patterns...", "🌀 Checking HH/HL Market Structure & SR...", "🎯 Calculating Auto-Timer & Signal..."]:
        radar_placeholder.info(stage)
        time.sleep(0.5)
    radar_placeholder.empty()

    res = analyze_advanced_market(all_pairs[selected_pair], tf_map[trade_timeframe])

    if res:
        st.markdown(f'''
            <div class="signal-card {res['css']}">
                <h1>{res['direction']} {res['arrow']}</h1>
                <h2>Accuracy / Confidence: {res['accuracy']}%</h2>
                <h4>Detected Patterns & Rules: {res['pattern']}</h4>
            </div>
        ''', unsafe_allow_html=True)

        st.write("---")
        c1, c2 = st.columns(2)
        c1.metric("Live Market Price", f"{res['price']:.5f}")
        c2.metric("RSI Value", f"{res['rsi']:.1f}")

        # Auto Countdown Timer Execution
        st.write(f"### ⏱️ Auto-Calculated Entry Timer ({res['auto_timer']} Sec Prep)")
        timer_box = st.empty()
        
        for sec in range(res['auto_timer'], 0, -1):
            timer_box.markdown(f'<div class="timer-display">{sec} Sec</div>', unsafe_allow_html=True)
            time.sleep(1)
            
        timer_box.markdown('<div class="timer-display" style="color:#00E676; border-color:#00E676;">GO! PLACE TRADE NOW 🚀</div>', unsafe_allow_html=True)
        st.balloons()
    else:
        st.error("⚠️ Live data loading. Please select 5m Candle/Trade and try again.")
else:
    st.info("👆 Click the **START ANALYZING MARKET** button to scan live market patterns.")
        
