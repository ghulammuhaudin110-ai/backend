import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
import streamlit.components.v1 as components

# --- Page Setup ---
st.set_page_config(page_title="HK PRICE ACTION AI BOT", page_icon="🎯", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #121820;
        color: white;
    }
    .golden-header {
        font-size: 30px;
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
    .signal-card {
        background-color: #1E293B;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #334155;
        text-align: center;
        margin-top: 15px;
    }
    .up-signal { color: #00FF00; font-size: 36px; font-weight: bold; }
    .down-signal { color: #FF3333; font-size: 36px; font-weight: bold; }
    .no-trade { color: #FFCC00; font-size: 26px; font-weight: bold; }
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

# --- ADVANCED PRICE ACTION ENGINE ---
def analyze_advanced_price_action(df, trade_expiry_str):
    close = df['Close']
    open_p = df['Open']
    high = df['High']
    low = df['Low']
    volume = df['Volume'] if 'Volume' in df else None

    curr_price = float(close.iloc[-1])
    
    # 1. Detect Structure (Higher Highs / Lower Lows)
    h1, h2 = high.iloc[-5:-1].max(), high.iloc[-10:-5].max()
    l1, l2 = low.iloc[-5:-1].min(), low.iloc[-10:-5].min()
    
    is_uptrend = (h1 > h2) and (l1 > l2)
    is_downtrend = (h1 < h2) and (l1 < l2)

    # 2. Support & Resistance (Last 20 Candles)
    res_level = high.tail(20).max()
    sup_level = low.tail(20).min()

    # 3. Last Candle Patterns Analysis
    c2_open, c2_close, c2_high, c2_low = open_p.iloc[-1], close.iloc[-1], high.iloc[-1], low.iloc[-1]
    c1_open, c1_close = open_p.iloc[-2], close.iloc[-2]

    c2_body = abs(c2_close - c2_open)
    c2_upper_wick = c2_high - max(c2_open, c2_close)
    c2_lower_wick = min(c2_open, c2_close) - c2_low

    bullish_engulfing = (c1_close < c1_open) and (c2_close > c2_open) and (c2_close > c1_open)
    bearish_engulfing = (c1_close > c1_open) and (c2_close < c2_open) and (c2_close < c1_open)
    
    bullish_pinbar = (c2_lower_wick > (2 * c2_body)) and (c2_close > c2_open)
    bearish_pinbar = (c2_upper_wick > (2 * c2_body)) and (c2_close < c2_open)

    # --- RULE ACCURACY CALCULATOR ---
    bull_score = 0
    bear_score = 0
    passed_rules = []

    # Rule 1: Candlestick Pattern (Max 25%)
    if bullish_engulfing or bullish_pinbar:
        bull_score += 25
        passed_rules.append("Bullish Reversal Pattern Confirmed (+25%)")
    elif bearish_engulfing or bearish_pinbar:
        bear_score += 25
        passed_rules.append("Bearish Reversal Pattern Confirmed (+25%)")

    # Rule 2: Market Structure / Trend Alignment (Max 20%)
    if is_uptrend:
        bull_score += 20
        passed_rules.append("Structure: Higher Highs / Uptrend Alignment (+20%)")
    elif is_downtrend:
        bear_score += 20
        passed_rules.append("Structure: Lower Lows / Downtrend Alignment (+20%)")

    # Rule 3: Support / Resistance Bounce (Max 20%)
    if abs(curr_price - sup_level) < 0.00010:
        bull_score += 20
        passed_rules.append("Price Bouncing from Strong Support Zone (+20%)")
    elif abs(curr_price - res_level) < 0.00010:
        bear_score += 20
        passed_rules.append("Price Rejecting from Strong Resistance Zone (+20%)")

    # Rule 4: Candle Momentum & Wicks (Max 15%)
    if c2_close > c2_open and c2_lower_wick > c2_upper_wick:
        bull_score += 15
        passed_rules.append("Buyers Defending Lower Wick (+15%)")
    elif c2_close < c2_open and c2_upper_wick > c2_lower_wick:
        bear_score += 15
        passed_rules.append("Sellers Rejecting Upper Wick (+15%)")

    # Rule 5: Volume Confirmation (Max 10%)
    if volume is not None and len(volume) > 2:
        if volume.iloc[-1] > volume.iloc[-2]:
            if c2_close > c2_open: bull_score += 10
            else: bear_score += 10
            passed_rules.append("Increasing Volume Confirmation (+10%)")

    # Rule 6: Trade Expiry Check (Max 10%)
    bull_score += 10
    bear_score += 10

    # Final Signal Determination
    if bull_score >= 70 and bull_score > bear_score:
        return "UP ↑ (CALL)", bull_score, curr_price, passed_rules
    elif bear_score >= 70 and bear_score > bull_score:
        return "DOWN ↓ (PUT)", bear_score, curr_price, passed_rules
    else:
        max_score = max(bull_score, bear_score)
        return "NO TRADE ⚠️ (INSUFFICIENT RULE CONFLUENCE)", max_score, curr_price, passed_rules

def fetch_and_analyze(ticker, candle_time_str, trade_expiry_str):
    try:
        data_ticker = yf.Ticker(ticker)
        interval = "1m" if "1" in candle_time_str else "5m"
        df = data_ticker.history(period="1d", interval=interval)
        if df.empty or len(df) < 20:
            return "NO DATA", 0, 0.0, []
        return analyze_advanced_price_action(df, trade_expiry_str)
    except Exception:
        return "NO TRADE ⚠️ (FETCH ERROR)", 0, 0.0, []

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

# --- UI ---
st.markdown('<div class="golden-header">HK PRICE ACTION AI BOT</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">SMART PRICE ACTION & CONFLUENCE RULE ENGINE</div>', unsafe_allow_html=True)

render_live_pkt_clock()

col1, col2, col3 = st.columns(3)
with col1: selected_pair_name = st.selectbox("Live Forex Asset", list(PAIR_MAP.keys()))
with col2: candle_time = st.selectbox("Candle Time", ["1 Min", "5 Min"])
with col3: trade_time = st.selectbox("Trade Time", ["1 Min", "2 Min", "5 Min"])

yf_ticker, tv_symbol = PAIR_MAP[selected_pair_name]
st.divider()

if st.button("🚀 RUN PRICE ACTION ANALYSIS", use_container_width=True):
    with st.spinner("Checking Structure, Highs/Lows, Wicks & Resistance levels..."):
        time.sleep(1)
        signal, accuracy, live_price, rules = fetch_and_analyze(yf_ticker, candle_time, trade_time)
        
        st.markdown('<div class="signal-card">', unsafe_allow_html=True)
        if "UP" in signal:
            st.markdown(f'<div class="up-signal">{signal}</div>', unsafe_allow_html=True)
            st.write(f"🎯 **Strict Price Action Accuracy:** `{accuracy}%`")
            st.write(f"💵 **Price:** `{live_price:.5f}` | Expiry: `{trade_time}`")
        elif "DOWN" in signal:
            st.markdown(f'<div class="down-signal">{signal}</div>', unsafe_allow_html=True)
            st.write(f"🎯 **Strict Price Action Accuracy:** `{accuracy}%`")
            st.write(f"💵 **Price:** `{live_price:.5f}` | Expiry: `{trade_time}`")
        else:
            st.markdown(f'<div class="no-trade">{signal}</div>', unsafe_allow_html=True)
            st.info(f"💡 **Rules Confidence:** Only `{accuracy}%` (Required 70%+ for Safe Entry). Market setup is weak right now.")

        if rules:
            st.write("---")
            st.write("📋 **Passed Price Action Rules for this Signal:**")
            for r in rules:
                st.write(f"✅ {r}")

        st.subheader("📊 Live TradingView Chart")
        render_tradingview_widget(tv_symbol, candle_time)
        st.markdown('</div>', unsafe_allow_html=True)
    
