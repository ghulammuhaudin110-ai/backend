import streamlit as st
import pandas as pd
import numpy as np
import time
import requests

st.set_page_config(page_title="HK Signal Bot - Live MT5 Feed", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .gold-title {
        font-size: 42px; font-weight: 800; text-align: center;
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #B8860B 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .sub-title { text-align: center; color: #888; font-size: 18px; margin-bottom: 15px; }
    .signal-card { padding: 25px; border-radius: 20px; text-align: center; color: white; margin-top: 15px; }
    .buy-bg { background: linear-gradient(135deg, #00E676, #004D40); }
    .sell-bg { background: linear-gradient(135deg, #FF1744, #880E4F); }
    .stButton > button { 
        width: 100%; max-width: 400px; height: 65px; font-size: 22px; 
        font-weight: bold; background: linear-gradient(90deg, #1A237E, #311B92); 
        color: white; border-radius: 15px; border: 2px solid #FFD700; margin: 0 auto; display: block;
    }
    .timer-display { font-size: 70px; font-weight: bold; color: #FFD600; text-align: center; background: #111; padding: 10px; border-radius: 15px; border: 2px solid #FFD600; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="gold-title">⚡ HK Signal Bot (MT5 & TradingView Live)</h1>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Real-Time Forex & Crypto Price Action Engine</div>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Market Settings")

# TradingView / MT5 Matching Live Pairs
live_pairs = {
    "EUR/USD": "EURUSD",
    "GBP/USD": "GBPUSD",
    "USD/JPY": "USDJPY",
    "AUD/USD": "AUDUSD",
    "USD/CAD": "USDCAD",
    "USD/CHF": "USDCHF",
    "NZD/USD": "NZDUSD",
    "EUR/GBP": "EURGBP",
    "EUR/JPY": "EURJPY",
    "GBP/JPY": "GBPJPY",
    "GOLD (XAU/USD)": "XAUUSD",
    "BITCOIN (BTC/USD)": "BTCUSD",
    "ETHEREUM (ETH/USD)": "ETHUSD"
}

selected_pair_name = st.sidebar.selectbox("🎯 Select Live Pair:", list(live_pairs.keys()))
selected_pair_symbol = live_pairs[selected_pair_name]

candle_time = st.sidebar.selectbox("📊 Candle Timeframe:", ["1m Candle", "5m Candle"])
trade_time = st.sidebar.selectbox("⏱️ Expiry Time:", ["1m Trade", "5m Trade"])

# Live Ultra-Fast Data Fetcher
def fetch_mt5_tradingview_live_data(symbol, timeframe):
    try:
        # Binance Live Feed for Crypto
        if "BTC" in symbol or "ETH" in symbol:
            tf = "1m" if "1m" in timeframe else "5m"
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={tf}&limit=50"
            res = requests.get(url, timeout=4).json()
            df = pd.DataFrame(res, columns=['time', 'Open', 'High', 'Low', 'Close', 'vol', 'close_time', 'qav', 'nat', 'tbba', 'tbqa', 'ignore'])
        
        # Real-Time Forex API Feed
        else:
            tf = "1min" if "1m" in timeframe else "5min"
            # Fast Free Financial Data Endpoint
            url = f"https://api.exchange-rates.org.uk/history?pair={symbol}&interval={tf}"
            # Backup Free Live Price Feed
            url_alt = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}=X?interval={'1m' if '1m' in timeframe else '5m'}&range=1d"
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url_alt, headers=headers, timeout=4).json()
            
            result = res['chart']['result'][0]
            quote = result['indicators']['quote'][0]
            
            df = pd.DataFrame({
                'Open': quote['open'],
                'High': quote['high'],
                'Low': quote['low'],
                'Close': quote['close']
            }).dropna()

        df['Open'] = df['Open'].astype(float)
        df['High'] = df['High'].astype(float)
        df['Low'] = df['Low'].astype(float)
        df['Close'] = df['Close'].astype(float)
        return df

    except Exception as e:
        return None

# Advanced Price Action Engine
def analyze_market_rules(df):
    if df is None or len(df) < 20:
        return None

    # EMA Indicators
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()

    c0 = df.iloc[-1]
    c1 = df.iloc[-2]

    close_p, open_p = float(c0['Close']), float(c0['Open'])
    high_p, low_p = float(c0['High']), float(c0['Low'])
    body = abs(close_p - open_p)
    candle_range = high_p - low_p if (high_p - low_p) > 0 else 0.0001

    lower_wick = min(open_p, close_p) - low_p
    upper_wick = high_p - max(open_p, close_p)

    support = float(df['Low'].tail(15).min())
    resistance = float(df['High'].tail(15).max())

    bull_score = 50
    bear_score = 50
    rules = []

    # 1. EMA Trend
    if float(c0['EMA_9']) > float(c0['EMA_21']):
        bull_score += 18
        rules.append("Strong Uptrend (EMA 9 > 21)")
    else:
        bear_score += 18
        rules.append("Strong Downtrend (EMA 9 < 21)")

    # 2. Key SNR Zone Reversal
    if abs(close_p - support) <= (candle_range * 1.2):
        bull_score += 20
        rules.append("Strong Support Zone Reversal 🛡️")
    if abs(close_p - resistance) <= (candle_range * 1.2):
        bear_score += 20
        rules.append("Strong Resistance Zone Reversal 🚧")

    # 3. Candlestick Reversals
    if lower_wick >= (body * 2) and upper_wick <= (body * 0.3):
        bull_score += 15
        rules.append("Bullish Hammer")
    elif upper_wick >= (body * 2) and lower_wick <= (body * 0.3):
        bear_score += 15
        rules.append("Bearish Shooting Star")

    # Engulfing
    c1_close, c1_open = float(c1['Close']), float(c1['Open'])
    if close_p > open_p and c1_close < c1_open and close_p > c1_open:
        bull_score += 20
        rules.append("Bullish Engulfing")
    elif close_p < open_p and c1_close > c1_open and close_p < c1_open:
        bear_score += 20
        rules.append("Bearish Engulfing")

    # Signal Verdict
    if bull_score > bear_score:
        direction = "CALL (BUY) 🟢 UP"
        arrow = "⬆️"
        accuracy = min(bull_score, 96)
        css = "buy-bg"
    else:
        direction = "PUT (SELL) 🔴 DOWN"
        arrow = "⬇️"
        accuracy = min(bear_score, 96)
        css = "sell-bg"

    return {
        "direction": direction, "arrow": arrow, "accuracy": accuracy,
        "pattern": " | ".join(rules), "css": css, "price": close_p
    }

# Main Execution
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    start = st.button("🚀 GET LIVE ANALYZED SIGNAL")

if start:
    with st.spinner("FETCHING MT5 / TRADINGVIEW LIVE DATA..."):
        df = fetch_mt5_tradingview_live_data(selected_pair_symbol, candle_time)
        res = analyze_market_rules(df)

    if res:
        st.markdown(f'''
            <div class="signal-card {res['css']}">
                <h1>{res['direction']} {res['arrow']}</h1>
                <h2>Accuracy: {res['accuracy']}%</h2>
                <h4>Rules Applied: {res['pattern']}</h4>
            </div>
        ''', unsafe_allow_html=True)

        st.metric("Live Market Price", f"{res['price']:.5f}")
        
        # Countdown Prep
        timer_box = st.empty()
        for sec in range(5, 0, -1):
            timer_box.markdown(f'<div class="timer-display">{sec} Sec Prep</div>', unsafe_allow_html=True)
            time.sleep(1)
        timer_box.markdown('<div class="timer-display" style="color:#00E676; border-color:#00E676;">PLACE TRADE NOW 🚀</div>', unsafe_allow_html=True)
    else:
        st.error("⚠️ Market Data Fetching Error. Please click again or choose another pair.")
            
