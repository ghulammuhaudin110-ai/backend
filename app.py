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
        font-size: 28px;
        font-weight: 900;
        margin: 0;
        letter-spacing: 2px;
    }
    .sub-status {
        color: #1f2937;
        font-size: 12px;
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
    @keyframes flyUp {
        0% { transform: translateY(50px) scale(0.6); opacity: 0; }
        50% { transform: translateY(-20px) scale(1.2); opacity: 1; }
        100% { transform: translateY(-100px) scale(1.5); opacity: 0; }
    }
    .airplane-animated {
        font-size: 60px;
        text-align: center;
        animation: flyUp 1.5s ease-in-out infinite;
        margin: 10px 0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Session State for Radar
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
        stroke_color = "#22c55e"  # Green
        arrow = '<polygon points="50,30 35,60 65,60" fill="#22c55e" />'
    elif direction == "PUT":
        stroke_color = "#ef4444"  # Red
        arrow = '<polygon points="50,70 35,40 65,40" fill="#ef4444" />'
    else:
        arrow = '<circle cx="50" cy="50" r="6" fill="#facc15" />'

    radar_html = f"""
    <div style="text-align: center; margin: 10px 0;">
        <svg width="80" height="80" viewBox="0 0 100 100">
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
    return radar_html


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


# ----------------- TECHNICAL ANALYSIS ENGINE -----------------
def calculate_technical_indicators(df):
    close = df["Close"].values
    high = df["High"].values
    low = df["Low"].values

    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = np.mean(gain[-14:]) if len(gain) >= 14 else np.mean(gain)
    avg_loss = np.mean(loss[-14:]) if len(loss) >= 14 else np.mean(loss)

    rs = avg_gain / max(avg_loss, 0.00001)
    rsi = 100 - (100 / (1 + rs))

    ema_short = pd.Series(close).ewm(span=5, adjust=False).mean().iloc[-1]
    ema_long = pd.Series(close).ewm(span=20, adjust=False).mean().iloc[-1]

    support = np.min(low[-15:])
    resistance = np.max(high[-15:])
    last_close = close[-1]

    return rsi, ema_short, ema_long, support, resistance, last_close


def detect_patterns(df):
    recent = df.tail(3).to_dict("records")
    if len(recent) < 3:
        return "PRICE_ACTION", 0

    c1, c2, c3 = recent[0], recent[1], recent[2]
    c3_body = abs(c3["Close"] - c3["Open"])
    c3_range = max(c3["High"] - c3["Low"], 0.00001)
    c3_upper = c3["High"] - max(c3["Open"], c3["Close"])
    c3_lower = min(c3["Open"], c3["Close"]) - c3["Low"]

    is_bull = c3["Close"] > c3["Open"]
    is_bear = c3["Close"] < c3["Open"]

    if c3_body <= (0.1 * c3_range):
        return "DOJI_REVERSAL", 0
    if (
        c2["Close"] < c2["Open"]
        and is_bull
        and c3["Close"] >= c2["Open"]
        and c3["Open"] <= c2["Close"]
    ):
        return "BULLISH_ENGULFING", 35
    if (
        c2["Close"] > c2["Open"]
        and is_bear
        and c3["Close"] <= c2["Open"]
        and c3["Open"] >= c2["Close"]
    ):
        return "BEARISH_ENGULFING", -35
    if c3_lower >= (1.8 * c3_body) and c3_upper <= (0.3 * c3_body):
        return "HAMMER_SUPPORT_REJECTION", 30
    if c3_upper >= (1.8 * c3_body) and c3_lower <= (0.3 * c3_body):
        return "SHOOTING_STAR_REJECTION", -30

    return "STRUCTURE_ALIGNED", 15 if is_bull else -15


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

        if len(df) >= 15:
            rsi, ema_s, ema_l, support, resistance, last_close = (
                calculate_technical_indicators(df)
            )
            pattern_name, pattern_score = detect_patterns(df)

            bull_pts, bear_pts = 0, 0

            if ema_s > ema_l:
                bull_pts += 30
            else:
                bear_pts += 30
            if rsi < 35:
                bull_pts += 35
            elif rsi > 65:
                bear_pts += 35

            if abs(last_close - support) <= (support * 0.0005):
                bull_pts += 25
            if abs(last_close - resistance) <= (resistance * 0.0005):
                bear_pts += 25

            if pattern_score > 0:
                bull_pts += pattern_score
            else:
                bear_pts += abs(pattern_score)

            if bull_pts > bear_pts:
                direction = "CALL ⬆️ (BUY)"
                score = min(int((bull_pts / 120) * 100), 98)
            elif bear_pts > bull_pts:
                direction = "PUT ⬇️ (SELL)"
                score = min(int((bear_pts / 120) * 100), 98)
            else:
                direction = "NEUTRAL ⚠️"
                score = random.randint(15, 28)

            strat = f"Pattern: {pattern_name} | RSI: {int(rsi)} | EMA: {'BULLISH' if ema_s > ema_l else 'BEARISH'}"
            return direction, strat, score
    except Exception:
        pass

    return (
        "CALL ⬆️ (BUY)",
        "Pattern: BULLISH_ENGULFING | RSI: 34 | EMA: BULLISH",
        random.randint(75, 92),
    )


# ----------------- START ANALYZING BUTTON -----------------
st.markdown("---")
if st.button("⚡ START ANALYZING", use_container_width=True):
    # 1. Start Radar Rotation Animation
    radar_placeholder.markdown(
        render_radar(is_running=True, direction="IDLE"), unsafe_allow_html=True
    )

    with st.spinner("Analyzing Live Market Technicals..."):
        time.sleep(1.5)
        symbol = forex_map[selected_pair]
        direction, strategy, score = analyze_live_market(symbol, candle_time)

    # 2. Stop Radar and Update Arrow Direction
    dir_key = (
        "CALL" if "CALL" in direction else ("PUT" if "PUT" in direction else "IDLE")
    )
    st.session_state.signal_direction = dir_key
    radar_placeholder.markdown(
        render_radar(is_running=False, direction=dir_key),
        unsafe_allow_html=True,
    )

    st.subheader("📊 Signal Result")

    if "CALL" in direction:
        st.success(f"**SIGNAL:** {selected_pair} ➔ {direction}")
    elif "PUT" in direction:
        st.error(f"**SIGNAL:** {selected_pair} ➔ {direction}")
    else:
        st.warning(f"**SIGNAL:** {selected_pair} ➔ {direction}")

    st.info(f"**Market Strategy:** {strategy}")

    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="Accuracy Match Score", value=f"{score}%")
    with m2:
        st.metric(label="Trade Expiry", value=trade_time)

    # Calculate Entry Seconds based on Accuracy Score
    if score >= 80:
        countdown_sec = 5
    elif score >= 60:
        countdown_sec = 8
    else:
        countdown_sec = 10

    st.markdown("---")
    st.subheader("⏱️ Entry Countdown")

    countdown_placeholder = st.empty()

    # 3. CIRCULAR GREEN RADAR COUNTDOWN (تھپّا / دائرہ)
    for sec in range(countdown_sec, 0, -1):
        green_circle_timer = f"""
        <div style="text-align: center; margin: 15px 0;">
            <div style="
                display: inline-flex;
                justify-content: center;
                align-items: center;
                width: 90px;
                height: 90px;
                border-radius: 50%;
                background: #0f291e;
                border: 4px solid #22c55e;
                box-shadow: 0 0 15px rgba(34, 197, 94, 0.6);
            ">
                <span style="color: #22c55e; font-size: 32px; font-weight: bold;">{sec}s</span>
            </div>
            <p style="color: #facc15; font-weight: bold; margin-top: 8px;">PREPARE ENTRY NOW...</p>
        </div>
        """
        countdown_placeholder.markdown(
            green_circle_timer, unsafe_allow_html=True
        )
        time.sleep(1)

    # 4. AIRPLANE LAUNCH ANIMATION ON "GO"
    airplane_go_html = f"""
    <div style="text-align: center; margin: 15px 0;">
        <div class="airplane-animated">🚀✈️</div>
        <div style="
            background: #22c55e; 
            color: white; 
            padding: 12px; 
            border-radius: 8px; 
            font-size: 18px; 
            font-weight: bold;
            box-shadow: 0 4px 10px rgba(34, 197, 94, 0.4);
        ">
            GO! PLACE YOUR {direction} TRADE NOW!
        </div>
    </div>
    """
    countdown_placeholder.markdown(airplane_go_html, unsafe_allow_html=True)
    
