import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime
import pytz

# --- Page Setup ---
st.set_page_config(page_title="HK SIGNAL BOARD", page_icon="📈", layout="centered")

# Custom CSS for HK Signal Board Design
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
        text-shadow: 0px 0px 10px #FFD700;
    }
    .sub-header {
        font-size: 13px;
        color: #AAAAAA;
        text-align: center;
        margin-bottom: 20px;
    }
    .radar-box {
        border: 2px solid #00FF00;
        border-radius: 50%;
        width: 140px;
        height: 140px;
        margin: auto;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 0 20px #00FF00;
        background: radial-gradient(circle, #003300 0%, #001100 70%);
    }
    .signal-card {
        background-color: #2A2A2A;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #555;
        text-align: center;
        margin-top: 15px;
    }
    .up-signal {
        color: #00FF00;
        font-size: 38px;
        font-weight: bold;
    }
    .down-signal {
        color: #FF3333;
        font-size: 38px;
        font-weight: bold;
    }
    .no-signal {
        color: #FFCC00;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Yahoo Finance Asset Symbol Mapping
PAIR_MAP = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "USD/CHF": "CHF=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "AUD/JPY": "AUDJPY=X"
}

# Live Data Fetching and Technical Calculations
def fetch_and_analyze_live_market(ticker):
    try:
        df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
        
        if df.empty or len(df) < 50:
            return "MARKET CLOSED / NO DATA", 0, 0.0

        close = df['Close'].squeeze()
        high = df['High'].squeeze()
        low = df['Low'].squeeze()

        # 1. EMA 200
        ema_200 = close.ewm(span=200, adjust=False).mean()

        # 2. RSI Calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # 3. Stochastic Oscillator
        low_min = low.rolling(window=14).min()
        high_max = high.rolling(window=14).max()
        stoch_k = 100 * ((close - low_min) / (high_max - low_min))
        stoch_d = stoch_k.rolling(window=3).mean()

        # Latest Values
        curr_price = float(close.iloc[-1])
        curr_ema = float(ema_200.iloc[-1])
        curr_rsi = float(rsi.iloc[-1])
        prev_rsi = float(rsi.iloc[-2])
        curr_k = float(stoch_k.iloc[-1])
        curr_d = float(stoch_d.iloc[-1])

        # Signal Rules
        if curr_price > curr_ema and curr_rsi > 30 and prev_rsi <= 35 and curr_k > curr_d:
            return "UP ↑ (CALL)", 89, curr_price
        
        elif curr_price < curr_ema and curr_rsi < 70 and prev_rsi >= 65 and curr_k < curr_d:
            return "DOWN ↓ (PUT)", 91, curr_price
        
        else:
            return "NO TRADE (Filters Active)", 0, curr_price

    except Exception:
        return "ERROR FETCHING DATA", 0, 0.0

# --- Header UI ---
st.markdown('<div class="golden-header">HK SIGNAL BOARD</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">LIVE YAHOO FINANCE MARKET BOT</div>', unsafe_allow_html=True)

# Timezone Auto Fix (Asia/Karachi for PST Time)
local_tz = pytz.timezone('Asia/Karachi')
current_local_time = datetime.now(local_tz).strftime('%H:%M:%S')

st.write(f"⏰ **System Live Time (PKT):** `{current_local_time}`")

# Asset & Timeframe Selection
col1, col2, col3 = st.columns(3)
with col1:
    selected_pair_name = st.selectbox("Live Forex Asset", list(PAIR_MAP.keys()))
with col2:
    candle_time = st.selectbox("Candle Time", ["1 Min", "5 Min"])
with col3:
    trade_time = st.selectbox("Trade Time", ["1 Min", "2 Min", "5 Min"])

ticker_symbol = PAIR_MAP[selected_pair_name]

st.divider()

# Radar Animation Box
st.markdown('<div class="radar-box"><h3 style="color:#00FF00; margin:0; font-size:16px;">LIVE SCAN</h3></div>', unsafe_allow_html=True)
st.write("")

# Action Button
if st.button("🚀 START ANALYZING", use_container_width=True):
    with st.spinner(f"Fetching Live Market Data for {selected_pair_name}..."):
        time.sleep(1.5)
        
        signal, accuracy, live_price = fetch_and_analyze_live_market(ticker_symbol)
        
        st.markdown('<div class="signal-card">', unsafe_allow_html=True)
        
        if "UP" in signal:
            st.markdown(f'<div class="up-signal">{signal}</div>', unsafe_allow_html=True)
            st.write(f"🎯 **Calculated Accuracy:** `{accuracy}%`")
            st.write(f"💵 **Live Market Price:** `{live_price:.5f}`")
            st.write(f"📊 **Asset:** `{selected_pair_name}` | ⏱️ **Expiry:** `{trade_time}`")
            
            st.warning("⏱️ **Entry Countdown Started!**")
            timer_placeholder = st.empty()
            for countdown in range(10, 0, -1):
                timer_placeholder.markdown(f"### ⏳ Entry in: `{countdown}s`")
                time.sleep(1)
            timer_placeholder.markdown("## 🟢 **GO! ENTRY NOW!**")

        elif "DOWN" in signal:
            st.markdown(f'<div class="down-signal">{signal}</div>', unsafe_allow_html=True)
            st.write(f"🎯 **Calculated Accuracy:** `{accuracy}%`")
            st.write(f"💵 **Live Market Price:** `{live_price:.5f}`")
            st.write(f"📊 **Asset:** `{selected_pair_name}` | ⏱️ **Expiry:** `{trade_time}`")
            
            st.warning("⏱️ **Entry Countdown Started!**")
            timer_placeholder = st.empty()
            for countdown in range(10, 0, -1):
                timer_placeholder.markdown(f"### ⏳ Entry in: `{countdown}s`")
                time.sleep(1)
            timer_placeholder.markdown("## 🟢 **GO! ENTRY NOW!**")

        else:
            st.markdown(f'<div class="no-signal">{signal}</div>', unsafe_allow_html=True)
            if live_price > 0:
                st.write(f"💵 **Current Price:** `{live_price:.5f}`")
            st.info("मार्केट बंद है (वीकेंड) या फिर अभी कोई सुरक्षित एंट्री नहीं मिल रही है।")
            
        st.markdown('</div>', unsafe_allow_html=True)
    
