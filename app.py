import math
import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="HK SIGNAL BOT - REAL ENGINE", page_icon="🪙", layout="centered"
)

# Custom Styling
st.markdown(
    """
    <style>
    .golden-board {
        background: linear-gradient(135deg, #bf953f, #fcf6ba, #b38728, #fbf5b7, #aa771c);
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0px 4px 15px rgba(212, 175, 55, 0.4);
        margin-bottom: 15px;
    }
    .golden-title {
        color: #111827;
        font-size: 26px;
        font-weight: 900;
        margin: 0;
        letter-spacing: 1px;
    }
    .sub-status {
        color: #1f2937;
        font-size: 11px;
        font-weight: bold;
        margin-top: 5px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0284c7, #0369a1);
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px;
        border: none;
    }
    .signal-box-container {
        padding: 25px 15px;
        border-radius: 16px;
        text-align: center;
        color: white;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.5);
        margin: 15px 0;
    }
    .signal-title {
        font-size: 20px;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .signal-direction {
        font-size: 38px;
        font-weight: 900;
        margin: 10px 0;
    }
    .accuracy-large {
        font-size: 28px;
        font-weight: 900;
        color: #facc15;
        margin: 15px 0;
        text-transform: uppercase;
    }
    .details-bg {
        background: rgba(0, 0, 0, 0.4);
        padding: 12px;
        border-radius: 10px;
        text-align: left;
        font-size: 14px;
        font-weight: 600;
        line-height: 1.6;
    }
    </style>
""",
    unsafe_allow_html=True,
)

if "signal_direction" not in st.session_state:
    st.session_state.signal_direction = "IDLE"

# ----------------- 1. HEADER -----------------
st.markdown(
    """
    <div class="golden-board">
        <h1 class="golden-title">🪙 HK SIGNAL BOT (REAL ENGINE) 🪙</h1>
        <div class="sub-status">🟢 VERIFIED TECHNICAL BACKTESTING & INDICATOR ENGINE</div>
    </div>
""",
    unsafe_allow_html=True,
)

# ----------------- ASSET MAPPING -----------------
forex_map = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
}

col1, col2, col3 = st.columns(3)
with col1:
    selected_pair = st.selectbox("Select Asset Pair", list(forex_map.keys()))
with col2:
    candle_time = st.selectbox("Candle Time Frame", ["1 Minute", "2 Minutes", "5 Minutes"])
with col3:
    trade_time = st.selectbox("Trade Expiry Time", ["1 Minute", "2 Minutes", "5 Minutes"])


# ----------------- REAL ANALYSIS & BACKTESTING ENGINE -----------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 0.00001)
    return 100 - (100 / (1 + rs))


def analyze_real_market(symbol, interval_str):
    tf_map = {"1 Minute": "1m", "2 Minutes": "2m", "5 Minutes": "5m"}
    tf = tf_map.get(interval_str, "1m")

    try:
        df = yf.Ticker(symbol).history(period="1d", interval=tf)
        if df.empty or len(df) < 30:
            df = yf.download(tickers=symbol, period="1d", interval=tf, progress=False)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna()

        if len(df) < 30:
            return "NEUTRAL", "ڈیٹا ناکافی ہے، برائے مہربانی مارکیٹ کھلنے کا انتظار کریں۔", 0, "NO SIGNAL"

        # Indicators Calculation
        df["EMA5"] = df["Close"].ewm(span=5, adjust=False).mean()
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["RSI"] = calculate_rsi(df["Close"], 14)

        # Calculate Signals for Backtesting (Past 20 Candles)
        wins = 0
        total_signals = 0

        for i in range(len(df) - 21, len(df) - 1):
            prev_close = df["Close"].iloc[i]
            next_close = df["Close"].iloc[i + 1]
            ema5_val = df["EMA5"].iloc[i]
            ema20_val = df["EMA20"].iloc[i]
            rsi_val = df["RSI"].iloc[i]

            # Signal Logic
            hist_signal = None
            if ema5_val > ema20_val and rsi_val > 50:
                hist_signal = "CALL"
            elif ema5_val < ema20_val and rsi_val < 50:
                hist_signal = "PUT"

            if hist_signal:
                total_signals += 1
                if hist_signal == "CALL" and next_close > prev_close:
                    wins += 1
                elif hist_signal == "PUT" and next_close < prev_close:
                    wins += 1

        # Real Historical Win Rate
        win_rate = int((wins / total_signals) * 100) if total_signals > 0 else 50

        # Current Live Signal Analysis
        last_close = df["Close"].iloc[-1]
        last_ema5 = df["EMA5"].iloc[-1]
        last_ema20 = df["EMA20"].iloc[-1]
        last_rsi = df["RSI"].iloc[-1]

        direction = "WAIT / NO SIGNAL ⏳"
        if last_ema5 > last_ema20 and last_rsi > 52:
            direction = "CALL ⬆️ (BUY)"
        elif last_ema5 < last_ema20 and last_rsi < 48:
            direction = "PUT ⬇️ (SELL)"

        details = (
            f"• <b>Live EMA Trend:</b> {'BULLISH 🟢' if last_ema5 > last_ema20 else 'BEARISH 🔴'}<br>"
            f"• <b>RSI Indicator:</b> {int(last_rsi)} ({'Oversold/Bullish' if last_rsi < 40 else 'Overbought/Bearish' if last_rsi > 60 else 'Neutral'})<br>"
            f"• <b>Backtest Sample:</b> {wins}/{total_signals} Wins in last 20 candles"
        )

        return direction, details, win_rate, "SUCCESS"

    except Exception as e:
        return "ERROR", f"مارکیٹ ڈیٹا سے کنکشن حاصل نہیں ہو سکا۔ وجہ: {str(e)}", 0, "FAILED"


# ----------------- BUTTON LOGIC -----------------
st.markdown("---")
if st.button("⚡ START ANALYZING (REAL BACKTEST)", use_container_width=True):
    with st.spinner("Analyzing Live Yahoo Engine & Calculating Real Backtest Win Rate..."):
        time.sleep(1)
        symbol = forex_map[selected_pair]
        direction, details, win_rate, status = analyze_real_market(symbol, candle_time)

    if status == "FAILED":
        st.error(details)
    else:
        box_bg = "#16a34a" if "CALL" in direction else ("#dc2626" if "PUT" in direction else "#4b5563")

        big_box_html = f"""
        <div class="signal-box-container" style="background-color: {box_bg};">
            <div class="signal-title">PAIR: {selected_pair}</div>
            <div class="signal-direction">{direction}</div>
            <hr style="border: 0.5px solid rgba(255,255,255,0.3); margin: 15px 0;">
            <div class="accuracy-large">HISTORICAL WIN RATE: {win_rate}%</div>
            <div class="details-bg">
                <b>🔍 REAL MARKET ANALYSIS:</b><br>{details}
            </div>
        </div>
        """
        st.markdown(big_box_html, unsafe_allow_html=True)
            
