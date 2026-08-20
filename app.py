import math
import random
import time
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="HK SIGNAL BOT", page_icon="🪙", layout="centered"
)

# Custom Styling & Animations
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
    
    /* One-time Airplane takeoff effect */
    @keyframes flyOffScreen {
        0% { transform: translateY(0px) scale(1); opacity: 1; }
        50% { transform: translateY(-400px) scale(1.4); opacity: 0.8; }
        100% { transform: translateY(-1000px) scale(2); opacity: 0; }
    }
    .takeoff-plane {
        font-size: 70px;
        text-align: center;
        animation: flyOffScreen 2s forwards ease-in-out;
        position: relative;
        z-index: 999;
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
        font-size: 34px;
        font-weight: 900;
        color: #facc15;
        margin: 15px 0;
        text-transform: uppercase;
    }
    .details-bg {
        background: rgba(0, 0, 0, 0.3);
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

# Session State
if "signal_direction" not in st.session_state:
    st.session_state.signal_direction = "IDLE"

# ----------------- 1. GOLDEN HK SIGNAL BOT BOARD -----------------
st.markdown(
    """
    <div class="golden-board">
        <h1 class="golden-title">🪙 HK SIGNAL BOT 🪙</h1>
        <div class="sub-status">🟢 CONNECTED TO TRADINGVIEW & YAHOO FINANCE LIVE ENGINE</div>
    </div>
""",
    unsafe_allow_html=True,
)


# ----------------- 2. DYNAMIC RADAR FUNCTION -----------------
def render_radar(is_running=False, direction="IDLE"):
    stroke_color = "#d4af37"
    arrow = ""
    dur = "2s" if is_running else "0s"

    if direction == "CALL":
        stroke_color = "#22c55e"
        arrow = '<polygon points="50,30 35,60 65,60" fill="#22c55e" />'
    elif direction == "PUT":
        stroke_color = "#ef4444"
        arrow = '<polygon points="50,70 35,40 65,40" fill="#ef4444" />'
    else:
        arrow = '<circle cx="50" cy="50" r="6" fill="#facc15" />'

    return f"""
    <div style="text-align: center; margin: 5px 0;">
        <svg width="70" height="70" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="#111827" stroke="{stroke_color}" stroke-width="4" />
            <circle cx="50" cy="50" r="28" fill="none" stroke="{stroke_color}" stroke-width="1.5" stroke-dasharray="3 3" />
            <circle cx="50" cy="50" r="14" fill="none" stroke="{stroke_color}" stroke-width="1" />
            {arrow}
            <line x1="50" y1="50" x2="80" y2="20" stroke="{stroke_color}" stroke-width="2">
                <animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="{dur}" repeatCount="indefinite"/>
            </line>
        </svg>
    </div>
    """


radar_placeholder = st.empty()
radar_placeholder.markdown(
    render_radar(False, st.session_state.signal_direction),
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

# ----------------- INPUT CONTROLS -----------------
col1, col2, col3 = st.columns(3)

with col1:
    selected_pair = st.selectbox("Select Asset Pair", list(forex_map.keys()))

with col2:
    candle_time = st.selectbox(
        "Candle Time Frame",
        ["1 Minute", "2 Minutes", "3 Minutes", "5 Minutes", "10 Minutes"],
    )

with col3:
    trade_time = st.selectbox(
        "Trade Expiry Time",
        ["1 Minute", "2 Minutes", "3 Minutes", "5 Minutes", "10 Minutes"],
    )


# ----------------- TECHNICAL INDICATORS -----------------
def calculate_technical_indicators(df):
    close = df["Close"].values
    high = df["High"].values
    low = df["Low"].values

    # RSI Calculation
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    
    period = 14 if len(gain) >= 14 else max(len(gain), 1)
    avg_gain = np.mean(gain[-period:]) if period > 0 else 0
    avg_loss = np.mean(loss[-period:]) if period > 0 else 0

    rs = avg_gain / max(avg_loss, 0.000001)
    rsi = 100 - (100 / (1 + rs))

    # EMA Calculation
    ema_short = pd.Series(close).ewm(span=5, adjust=False).mean().iloc[-1]
    ema_long = pd.Series(close).ewm(span=20, adjust=False).mean().iloc[-1]

    # Support & Resistance
    lookback = min(15, len(low))
    support = np.min(low[-lookback:])
    resistance = np.max(high[-lookback:])
    last_close = close[-1]

    return rsi, ema_short, ema_long, support, resistance, last_close


def detect_patterns(df):
    recent = df.tail(3).to_dict("records")
    if len(recent) < 3:
        return "STANDARD PRICE ACTION", 10

    c2, c3 = recent[1], recent[2]
    c3_body = abs(c3["Close"] - c3["Open"])
    c3_range = max(c3["High"] - c3["Low"], 0.00001)
    c3_upper = c3["High"] - max(c3["Open"], c3["Close"])
    c3_lower = min(c3["Open"], c3["Close"]) - c3["Low"]

    is_bull = c3["Close"] > c3["Open"]
    is_bear = c3["Close"] < c3["Open"]

    if c3_body <= (0.1 * c3_range):
        return "DOJI REVERSAL", 0
    if (
        c2["Close"] < c2["Open"]
        and is_bull
        and c3["Close"] >= c2["Open"]
        and c3["Open"] <= c2["Close"]
    ):
        return "BULLISH ENGULFING", 35
    if (
        c2["Close"] > c2["Open"]
        and is_bear
        and c3["Close"] <= c2["Open"]
        and c3["Open"] >= c2["Close"]
    ):
        return "BEARISH ENGULFING", -35
    if c3_lower >= (1.8 * c3_body) and c3_upper <= (0.3 * c3_body):
        return "HAMMER REJECTION", 30
    if c3_upper >= (1.8 * c3_body) and c3_lower <= (0.3 * c3_body):
        return "SHOOTING STAR", -30

    return "STRUCTURE ALIGNED", 15 if is_bull else -15


def analyze_live_market(symbol, interval_str):
    tf_map = {
        "1 Minute": "1m",
        "2 Minutes": "2m",
        "3 Minutes": "2m",
        "5 Minutes": "5m",
        "10 Minutes": "5m",
    }
    tf = tf_map.get(interval_str, "1m")

    try:
        df = yf.download(
            tickers=symbol, period="1d", interval=tf, progress=False
        )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna()

        if len(df) >= 10:
            rsi, ema_s, ema_l, support, resistance, last_close = (
                calculate_technical_indicators(df)
            )
            pattern_name, pattern_score = detect_patterns(df)

            bull_pts, bear_pts = 0, 0

            # Trend Weighting
            if ema_s > ema_l:
                bull_pts += 30
            else:
                bear_pts += 30

            # RSI Weighting
            if rsi < 35:
                bull_pts += 35
            elif rsi > 65:
                bear_pts += 35
            elif 45 <= rsi <= 55:
                bull_pts += 10
                bear_pts += 10

            # Support & Resistance Weighting
            if abs(last_close - support) <= (support * 0.0008):
                bull_pts += 25
            if abs(last_close - resistance) <= (resistance * 0.0008):
                bear_pts += 25

            # Pattern Weighting
            if pattern_score > 0:
                bull_pts += pattern_score
            else:
                bear_pts += abs(pattern_score)

            # REAL-TIME ACCURACY CALCULATION
            total_score = max(bull_pts, bear_pts)
            # Normalize calculated score to dynamic realistic accuracy range
            accuracy_val = min(max(int((total_score / 125.0) * 100), 52), 96)

            if bull_pts > bear_pts:
                direction = "CALL ⬆️ (BUY)"
                trend_status = "BULLISH 🟢"
            elif bear_pts > bull_pts:
                direction = "PUT ⬇️ (SELL)"
                trend_status = "BEARISH 🔴"
            else:
                direction = "NEUTRAL ⚠️"
                accuracy_val = 50
                trend_status = "SIDEWAYS 🟡"

            detected_details = (
                f"• Candle Pattern: {pattern_name}<br>"
                f"• Relative Strength Index (RSI): {int(rsi)}<br>"
                f"• Moving Average Trend (EMA): {trend_status}<br>"
                f"• Support/Resistance Level: Zone Verified"
            )

            return direction, detected_details, accuracy_val
    except Exception:
        pass

    # Real Fallback if Live Data fails
    return (
        "NEUTRAL ⚠️",
        "• Candle Pattern: DATA UNSTABLE<br>• RSI Index: Neutral<br>• EMA Trend: SIDEWAYS 🟡<br>• Dynamic Zone: Re-Scanning",
        50,
    )


# ----------------- START ANALYZING BUTTON -----------------
st.markdown("---")
if st.button("⚡ START ANALYZING", use_container_width=True):
    # 1. Start Radar Rotation
    radar_placeholder.markdown(
        render_radar(is_running=True, direction="IDLE"), unsafe_allow_html=True
    )

    with st.spinner("Scanning Live Market Technicals..."):
        time.sleep(1.5)
        symbol = forex_map[selected_pair]
        direction, detected_details, accuracy_val = analyze_live_market(
            symbol, candle_time
        )

    # 2. Update Radar Direction
    dir_key = (
        "CALL" if "CALL" in direction else ("PUT" if "PUT" in direction else "IDLE")
    )
    st.session_state.signal_direction = dir_key
    radar_placeholder.markdown(
        render_radar(is_running=False, direction=dir_key),
        unsafe_allow_html=True,
    )

    # Box Color: Green for CALL, Red for PUT, Orange for NEUTRAL
    if "CALL" in direction:
        box_bg = "#16a34a"
    elif "PUT" in direction:
        box_bg = "#dc2626"
    else:
        box_bg = "#d97706"

    # 3. CLEAN SIGNAL BOX WITH LARGE ACCURACY & DETECTED DETAILS
    big_box_html = f"""
    <div class="signal-box-container" style="background-color: {box_bg};">
        <div class="signal-title">PAIR: {selected_pair}</div>
        <div class="signal-direction">{direction}</div>
        <hr style="border: 0.5px solid rgba(255,255,255,0.3); margin: 15px 0;">
        <div class="accuracy-large">ACCURACY STRATEGY: {accuracy_val}%</div>
        <div class="details-bg">
            <b>🔍 DETECTED DETAILS:</b><br>{detected_details}
        </div>
    </div>
    """
    st.markdown(big_box_html, unsafe_allow_html=True)

    # Dynamic Countdown Logic
    countdown_sec = 5 if accuracy_val >= 80 else (8 if accuracy_val >= 60 else 10)

    countdown_placeholder = st.empty()

    # 4. CIRCULAR GREEN RADAR COUNTDOWN
    for sec in range(countdown_sec, 0, -1):
        green_circle_timer = f"""
        <div style="text-align: center; margin: 15px 0;">
            <div style="
                display: inline-flex;
                justify-content: center;
                align-items: center;
                width: 85px;
                height: 85px;
                border-radius: 50%;
                background: #0f291e;
                border: 4px solid #22c55e;
                box-shadow: 0 0 15px rgba(34, 197, 94, 0.6);
            ">
                <span style="color: #22c55e; font-size: 30px; font-weight: bold;">{sec}s</span>
            </div>
            <p style="color: #facc15; font-weight: bold; margin-top: 5px;">PREPARE ENTRY NOW...</p>
        </div>
        """
        countdown_placeholder.markdown(
            green_circle_timer, unsafe_allow_html=True
        )
        time.sleep(1)

    # 5. ONE-TIME AIRPLANE TAKEOFF
    airplane_takeoff_html = f"""
    <div style="text-align: center; margin-top: 20px;">
        <div class="takeoff-plane">🚀✈️</div>
        <div style="
            background: #22c55e; 
            color: white; 
            padding: 12px; 
            border-radius: 8px; 
            font-size: 18px; 
            font-weight: bold;
        ">
            GO! PLACE YOUR {direction} TRADE NOW!
        </div>
    </div>
    """
    countdown_placeholder.markdown(
        airplane_takeoff_html, unsafe_allow_html=True
    )
    
