import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime
import pytz
import streamlit.components.v1 as components

# --- Page Setup ---
st.page_config(page_title="HK PRECISE ENTRY BOT", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #121820; color: white; }
    .golden-header { font-size: 30px; font-weight: bold; color: #FFD700; text-align: center; }
    .sub-header { font-size: 13px; color: #AAAAAA; text-align: center; margin-bottom: 20px; }
    .signal-card { background-color: #1E293B; padding: 20px; border-radius: 12px; border: 2px solid #334155; text-align: center; margin-top: 15px; }
    .up-signal { color: #00FF00; font-size: 36px; font-weight: bold; }
    .down-signal { color: #FF3333; font-size: 36px; font-weight: bold; }
    .no-signal { color: #FACC15; font-size: 30px; font-weight: bold; }
    .timer-box { font-size: 24px; font-weight: bold; color: #FFD700; background: #0F172A; padding: 10px; border-radius: 8px; border: 1px dashed #FFD700; }
    .rule-box { background-color: #0F172A; padding: 10px; border-radius: 8px; text-align: left; margin-top: 10px; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

PAIR_MAP = {
    "EUR/USD": ("EURUSD=X", "FX:EURUSD"),
    "GBP/USD": ("GBPUSD=X", "FX:GBPUSD"),
    "USD/JPY": ("JPY=X", "FX:USDJPY"),
    "AUD/USD": ("AUDUSD=X", "FX:AUDUSD"),
    "USD/CAD": ("CAD=X", "FX:USDCAD"),
    "USD/CHF": ("CHF=X", "FX:USDCHF"),
    "EUR/GBP": ("EURGBP=X", "FX:EURGBP"),
    "EUR/JPY": ("EURJPY=X", "FX:EURJPY"),
    "GBP/JPY": ("GBPJPY=X", "FX:GBPJPY")
}

def render_live_pkt_clock():
    clock_html = """
    <div style="text-align: left; font-family: sans-serif; font-size: 15px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;">
        ⏰ System Live Time (PKT): <span id="pkt-clock" style="color:#00FF00; background-color:#222; padding:4px 10px; border-radius:6px;">--:--:--</span>
    </div>
    <script>
    function updatePKTClock() {
        const now = new Date();
        const options = { timeZone: 'Asia/Karachi', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' };
        document.getElementById('pkt-clock').innerText = new Intl.DateTimeFormat('en-GB', options).format(now);
    }
    setInterval(updatePKTClock, 1000);
    updatePKTClock();
    </script>
    """
    components.html(clock_html, height=45)

# --- PROFESSIONAL BINARY TRADER ALGORITHM ---
def analyze_binary_rules(df, mode):
    """
    4 Core Professional Confirmation Pillars for Binary Options Trading:
    1. Trend & Dynamic Support/Resistance (EMA 20/50 Alignment)
    2. Price Action & Rejection Wicks (Buyer/Seller Pressure)
    3. Candlestick Patterns (Engulfing / Pinbar Confirmation)
    4. RSI Momentum & Key Zones (Overbought/Oversold Reversal)
    """
    if len(df) < 50:
        return "NO TRADE ⚠️", 0, float(df['Close'].iloc[-1]), "NEUTRAL ⚪", ["مارکیٹ ڈیٹا ناکافی ہے"]

    close = df['Close']
    open_p = df['Open']
    high = df['High']
    low = df['Low']
    curr_price = float(close.iloc[-1])

    # Indicator Calculations
    ema_20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    ema_50 = close.ewm(span=50, adjust=False).mean().iloc[-1]

    # RSI Calculation (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs.iloc[-1]))

    # Candlestick Values (Last Closed Candle & Current Candle)
    c1_open, c1_close = open_p.iloc[-2], close.iloc[-2]
    c1_high, c1_low = high.iloc[-2], low.iloc[-2]
    c2_open, c2_close = open_p.iloc[-1], close.iloc[-1]

    bull_score = 0.0
    bear_score = 0.0
    total_confirmations = 4
    matched_reasons = []

    # 📌 CONFIRMATION 1: Trend Direction & Structure (EMA Alignment)
    if curr_price > ema_20 and ema_20 > ema_50:
        bull_score += 1.0
        matched_reasons.append("✅ [1/4] اپ ٹرینڈ کنفرمیشن (Price > EMA 20 > EMA 50)")
    elif curr_price < ema_20 and ema_20 < ema_50:
        bear_score += 1.0
        matched_reasons.append("✅ [1/4] ڈاؤن ٹرینڈ کنفرمیشن (Price < EMA 20 < EMA 50)")

    # 📌 CONFIRMATION 2: Price Action & Rejection Wick (SnR Pressure)
    c1_body = abs(c1_close - c1_open)
    c1_lower_wick = min(c1_open, c1_close) - c1_low
    c1_upper_wick = c1_high - max(c1_open, c1_close)

    recent_low = low.iloc[-20:-1].min()
    recent_high = high.iloc[-20:-1].max()

    if (c1_lower_wick > c1_body * 1.2) or (abs(curr_price - recent_low) / curr_price < 0.0008):
        bull_score += 1.0
        matched_reasons.append("✅ [2/4] سپورٹ لیول پر بولش ریجیکشن (Lower Wick Rejection / Support)")
    elif (c1_upper_wick > c1_body * 1.2) or (abs(curr_price - recent_high) / curr_price < 0.0008):
        bear_score += 1.0
        matched_reasons.append("✅ [2/4] ریزسٹنس لیول پر بیئرش ریجیکشن (Upper Wick Rejection / Resistance)")

    # 📌 CONFIRMATION 3: Candlestick Pattern (Momentum Engulfing/Pinbar)
    is_bullish_engulfing = (c1_close < c1_open) and (c2_close > c2_open) and (c2_close > c1_open)
    is_bearish_engulfing = (c1_close > c1_open) and (c2_close < c2_open) and (c2_close < c1_open)

    if is_bullish_engulfing:
        bull_score += 1.0
        matched_reasons.append("✅ [3/4] بولش اینگلفنگ پیٹرن (Bullish Engulfing Pattern)")
    elif is_bearish_engulfing:
        bear_score += 1.0
        matched_reasons.append("✅ [3/4] بیئرش اینگلفنگ پیٹرن (Bearish Engulfing Pattern)")

    # 📌 CONFIRMATION 4: RSI Momentum / Extremes
    if rsi <= 40:
        bull_score += 1.0
        matched_reasons.append(f"✅ [4/4] RSI بولش زون میں ہے ({rsi:.1f})")
    elif rsi >= 60:
        bear_score += 1.0
        matched_reasons.append(f"✅ [4/4] RSI بیئرش زون میں ہے ({rsi:.1f})")

    # --- DUAL MODE THRESHOLD FILTER ---
    # Normal Mode: 2 to 2.5 confirmations required out of 4
    # Premium Mode: 3 to 4 confirmations required out of 4
    if mode == "Normal Mode (Fast Signals)":
        min_required = 2.0
    else:  # Premium Mode
        min_required = 3.0

    if bull_score >= min_required and bull_score > bear_score:
        accuracy = int((bull_score / total_confirmations) * 100)
        return "UP ↑ (CALL)", accuracy, curr_price, "GREEN 🟢", matched_reasons
    elif bear_score >= min_required and bear_score > bull_score:
        accuracy = int((bear_score / total_confirmations) * 100)
        return "DOWN ↓ (PUT)", accuracy, curr_price, "RED 🔴", matched_reasons
    else:
        active_score = max(bull_score, bear_score)
        return "NO TRADE ⚠️ (WAIT)", 0, curr_price, "NEUTRAL ⚪", [
            f"⚠️ {mode} کے مطابق اس وقت صرف {active_score:.1f}/{total_confirmations} کنفرمیشنز میچ ہوئی ہیں جبکہ کم از کم {min_required} کنفرمیشنز ہونا ضروری ہیں۔ رسک سے بچنے کے لیے اینٹری اسکپ کر دی گئی ہے۔"
        ]

def fetch_and_analyze(ticker, candle_time_str, mode):
    try:
        data_ticker = yf.Ticker(ticker)
        interval = "1m" if "1" in candle_time_str else "5m"
        df = data_ticker.history(period="1d", interval=interval)
        if df.empty or len(df) < 50:
            return "NO TRADE ⚠️ (WAIT)", 0, 1.08500, "NEUTRAL ⚪", ["ڈیٹا لوڈ نہیں ہو سکا"]
        return analyze_binary_rules(df, mode)
    except Exception:
        return "NO TRADE ⚠️ (WAIT)", 0, 1.08500, "NEUTRAL ⚪", ["نیٹ ورک یا ڈیٹا میں مسئلہ"]

def render_tradingview_widget(tv_symbol, candle_time_str):
    interval_code = "1" if "1" in candle_time_str else "5"
    html_code = f"""
    <div class="tradingview-widget-container" style="height:350px;width:100%;">
      <div id="tradingview_chart" style="height:350px;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true, "symbol": "{tv_symbol}", "interval": "{interval_code}",
        "timezone": "Asia/Karachi", "theme": "dark", "style": "1", "locale": "en",
        "hide_top_toolbar": true, "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """
    components.html(html_code, height=360)

# --- UI Layout ---
st.markdown('<div class="golden-header">HK PRECISE ENTRY BOT</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">PRO BINARY OPTIONS DUAL-MODE SYSTEM (PROFESSIONAL TRADER STRATEGY)</div>', unsafe_allow_html=True)

render_live_pkt_clock()

col1, col2 = st.columns(2)
with col1: selected_pair_name = st.selectbox("Live Forex Asset", list(PAIR_MAP.keys()))
with col2: candle_time = st.selectbox("Candle Time", ["1 Min", "5 Min"])

col3, col4 = st.columns(2)
with col3: trade_time = st.selectbox("Trade Expiry Time", ["1 Min", "2 Min", "5 Min"])
with col4: bot_mode = st.selectbox("Select Strategy Mode", ["Normal Mode (Fast Signals)", "Premium Mode (High Precision)"])

yf_ticker, tv_symbol = PAIR_MAP[selected_pair_name]
st.divider()

if st.button("🚀 GET SIGNAL & EXACT ENTRY TIMER", use_container_width=True):
    with st.spinner(f"Analyzing Market in {bot_mode}..."):
        time.sleep(1)
        signal, accuracy, live_price, expected_candle, reasons = fetch_and_analyze(yf_ticker, candle_time, bot_mode)
        
        st.markdown('<div class="signal-card">', unsafe_allow_html=True)
        
        if "UP" in signal:
            st.markdown(f'<div class="up-signal">{signal}</div>', unsafe_allow_html=True)
        elif "DOWN" in signal:
            st.markdown(f'<div class="down-signal">{signal}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="no-signal">{signal}</div>', unsafe_allow_html=True)
            
        st.write(f"⚙️ **Mode:** `{bot_mode}` | 🎯 **Matched Accuracy:** `{accuracy}%`")
        st.write(f"💵 **Price:** `{live_price:.5f}` | 🕯️ **Expected Candle:** `{expected_candle}`")
        
        st.markdown('<div class="rule-box"><b>📋 Matched Trader Confirmations:</b><br>' + "<br>".join(reasons) + '</div>', unsafe_allow_html=True)
        
        st.write("---")
        
        pkt = pytz.timezone('Asia/Karachi')
        now_pkt = datetime.now(pkt)
        current_second = now_pkt.second
        
        seconds_to_wait = 60 - current_second
        if seconds_to_wait == 60:
            seconds_to_wait = 0

        st.markdown("### 🎯 **AUTOMATIC ENTRY COUNTDOWN**")
        timer_placeholder = st.empty()
        
        if "NO TRADE" not in signal:
            if seconds_to_wait > 0:
                for rem_sec in range(seconds_to_wait, 0, -1):
                    timer_placeholder.markdown(
                        f'<div class="timer-box">⏳ Wait for Next Candle (00s Open): <span style="color:#00FF00;">{rem_sec}s</span></div>', 
                        unsafe_allow_html=True
                    )
                    time.sleep(1)
            
            timer_placeholder.markdown(
                '<div class="timer-box" style="border: 2px solid #00FF00; color: #00FF00;">🔥 ENTER TRADE NOW (00th SEC ENTRY)! 🔥</div>', 
                unsafe_allow_html=True
            )
        else:
            timer_placeholder.markdown(
                '<div class="timer-box" style="border: 2px solid #FACC15; color: #FACC15;">⚠️ NO ENTRY - WAIT FOR NEXT SETUP</div>', 
                unsafe_allow_html=True
            )

        st.subheader("📊 Live TradingView Chart")
        render_tradingview_widget(tv_symbol, candle_time)
        st.markdown('</div>', unsafe_allow_html=True)
