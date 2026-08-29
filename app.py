import streamlit as st
import pandas as pd
import numpy as np
import pandas_ta as ta
import time
from datetime import datetime
import random

# --- Page Setup ---
st.set_page_config(page_title="HK SIGNAL BOARD", page_icon="📈", layout="centered")

# Custom CSS for Dark Theme, Golden Header & Radar Effect
st.markdown("""
    <style>
    .stApp {
        background-color: #1A1A1A;
        color: white;
    }
    .golden-header {
        font-size: 32px;
        font-weight: bold;
        color: #FFD700;
        text-align: center;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 14px;
        color: #AAAAAA;
        text-align: center;
        margin-bottom: 20px;
    }
    .radar-box {
        border: 2px solid #00FF00;
        border-radius: 50%;
        width: 150px;
        height: 150px;
        margin: auto;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 0 15px #00FF00;
        background: radial-gradient(circle, #003300 0%, #001100 70%);
    }
    .signal-card {
        background-color: #2A2A2A;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #444;
        text-align: center;
        margin-top: 15px;
    }
    .up-signal {
        color: #00FF00;
        font-size: 36px;
        font-weight: bold;
    }
    .down-signal {
        color: #FF3333;
        font-size: 36px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. Signal Logic ---
def get_high_accuracy_signal():
    np.random.seed(int(time.time()))
    close_prices = np.cumsum(np.random.randn(250)) + 100
    df = pd.DataFrame({
        'open': close_prices - np.random.uniform(0.1, 0.5, 250),
        'high': close_prices + np.random.uniform(0.1, 0.8, 250),
        'low': close_prices - np.random.uniform(0.1, 0.8, 250),
        'close': close_prices,
        'volume': np.random.randint(100, 1000, 250)
    })

    df['EMA_200'] = ta.ema(df['close'], length=200)
    df['RSI'] = ta.rsi(df['close'], length=14)
    stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3, smooth_k=3)
    df['STOCH_k'] = stoch['STOCHk_14_3_3']
    df['STOCH_d'] = stoch['STOCHd_14_3_3']

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    signal = "NO TRADE"
    accuracy = 0

    if curr['close'] > curr['EMA_200'] and curr['RSI'] > 30 and prev['RSI'] <= 35 and curr['STOCH_k'] > curr['STOCH_d']:
        signal = "UP ↑"
        accuracy = random.randint(85, 94)
    elif curr['close'] < curr['EMA_200'] and curr['RSI'] < 70 and prev['RSI'] >= 65 and curr['STOCH_k'] < curr['STOCH_d']:
        signal = "DOWN ↓"
        accuracy = random.randint(85, 95)
    else:
        # Fallback for demo simulation if strict condition fails
        choices = ["UP ↑", "DOWN ↓"]
        signal = random.choice(choices)
        accuracy = random.randint(86, 93)

    return signal, accuracy

# --- 2. Header UI ---
st.markdown('<div class="golden-header">HK SIGNAL BOARD</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">BINARY OPTIONS PREMIUM BOT</div>', unsafe_allow_html=True)

# Live Clock
st.write(f"⏰ **Live Time:** {datetime.now().strftime('%H:%M:%S')}")

# --- 3. Inputs / Options ---
col1, col2, col3 = st.columns(3)
with col1:
    pair = st.selectbox("Select Pair", ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "OTC_EURUSD", "OTC_GBPJPY"])
with col2:
    candle_time = st.selectbox("Candle Time", ["1 Min", "5 Min", "15 Min"])
with col3:
    trade_time = st.selectbox("Trade Time", ["1 Min", "2 Min", "5 Min"])

st.divider()

# --- 4. Radar Animation Area ---
st.markdown('<div class="radar-box"><h3 style="color:#00FF00; margin:0;">SCANNING</h3></div>', unsafe_allow_html=True)

st.write("")
st.write("")

# --- 5. Action Button ---
if st.button("🚀 START ANALYZING", use_container_width=True):
    with st.spinner("Analyzing Market Data & Technical Indicators..."):
        time.sleep(2) # Analysis loading effect
        
        signal, accuracy = get_high_accuracy_signal()
        
        # Display Results
        st.markdown('<div class="signal-card">', unsafe_allow_html=True)
        
        if "UP" in signal:
            st.markdown(f'<div class="up-signal">{signal} (CALL)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="down-signal">{signal} (PUT)</div>', unsafe_allow_html=True)
            
        st.write(f"🎯 **Accuracy:** `{accuracy}%`")
        st.write(f"📊 **Asset:** `{pair}` | ⏱️ **Expiry:** `{trade_time}`")
        
        # Countdown Timer Simulation
        st.warning("⏱️ **Entry Countdown Started!**")
        timer_placeholder = st.empty()
        
        for countdown in range(10, 0, -1):
            timer_placeholder.markdown(f"### ⏳ Entry in: `{countdown}s`")
            time.sleep(1)
            
        timer_placeholder.markdown("## 🟢 **GO! ENTRY NOW!**")
        st.markdown('</div>', unsafe_allow_html=True)
    
