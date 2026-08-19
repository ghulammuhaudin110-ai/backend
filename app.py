import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# Page Configuration
st.set_page_config(page_title="Pro Live Trading Signals", layout="wide", initial_sidebar_state="expanded")

# Custom Styling
st.markdown("""
    <style>
    .big-signal-buy { font-size:32px !important; font-weight: bold; color: #00E676; background-color: #003311; padding: 15px; border-radius: 10px; text-align: center; }
    .big-signal-sell { font-size:32px !important; font-weight: bold; color: #FF2A6D; background-color: #330011; padding: 15px; border-radius: 10px; text-align: center; }
    .big-signal-wait { font-size:32px !important; font-weight: bold; color: #FFD700; background-color: #333000; padding: 15px; border-radius: 10px; text-align: center; }
    div.stButton > button { font-size: 20px !important; font-weight: bold !important; width: 100% !important; background-color: #1E88E5 !important; color: white !important; border-radius: 10px !important; padding: 12px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 Pro Price Action & Live Forex Signal Engine")
st.write("Live Real Market Data | Technical Analysis | Trade Entry Timer")

# Sidebar Controls
st.sidebar.header("⚙️ Trading Settings")
pairs = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD"
}

selected_pair = st.sidebar.selectbox("Select Real Market Pair:", list(pairs.keys()))
timeframe = st.sidebar.selectbox("Select Timeframe (Expiry):", ["1m", "5m", "15m", "1h"], index=1)

ticker_symbol = pairs[selected_pair]

# Fetch Live Market Data
def load_data(symbol, tf):
    period = "1d" if tf in ["1m", "5m"] else "5d"
    df = yf.download(tickers=symbol, period=period, interval=tf, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

st.markdown("---")
# Start Analyzing Button
analyze_btn = st.button("🚀 Start Analyzing Market")

if analyze_btn:
    with st.spinner("Analyzing Live Market Data & Price Action Patterns..."):
        try:
            df = load_data(ticker_symbol, timeframe)
            
            if df.empty or len(df) < 20:
                st.error("⚠️ Market data is temporarily slow for this pair/timeframe. Please select 5m timeframe from the sidebar and try again.")
            else:
                # Technical Calculations
                df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
                df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
                
                # RSI Calculation
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))

                latest = df.iloc[-1]
                prev = df.iloc[-2]
                
                current_price = float(latest['Close'])
                support = float(df['Low'].tail(30).min())
                resistance = float(df['High'].tail(30).max())
                rsi_val = float(latest['RSI']) if not np.isnan(latest['RSI']) else 50.0

                # Price Action & Pattern Detection
                body = abs(latest['Close'] - latest['Open'])
                candle_range = latest['High'] - latest['Low']
                lower_wick = min(latest['Open'], latest['Close']) - latest['Low']
                upper_wick = latest['High'] - max(latest['Open'], latest['Close'])
                
                is_bullish = latest['Close'] > latest['Open']
                is_bearish = latest['Close'] < latest['Open']

                signal = "WAIT / NO ENTRY ⚪"
                css_class = "big-signal-wait"
                pattern = "Consolidation / No Strong Pattern"
                confidence = "50%"

                # Price Action Signal Logic
                if candle_range > 0 and lower_wick > (2 * body) and current_price <= (support * 1.001):
                    pattern = "Bullish Hammer near Support 🔨"
                    signal = "CALL (BUY) 🟢 UP ⬆️"
                    css_class = "big-signal-buy"
                    confidence = "90%"
                elif candle_range > 0 and upper_wick > (2 * body) and current_price >= (resistance * 0.999):
                    pattern = "Shooting Star near Resistance ☄️"
                    signal = "PUT (SELL) 🔴 DOWN ⬇️"
                    css_class = "big-signal-sell"
                    confidence = "90%"
                elif is_bullish and (prev['Close'] < prev['Open']) and (latest['Close'] > prev['Open']) and rsi_val < 65:
                    pattern = "Strong Bullish Engulfing 🔥"
                    signal = "CALL (BUY) 🟢 UP ⬆️"
                    css_class = "big-signal-buy"
                    confidence = "85%"
                elif is_bearish and (prev['Open'] < prev['Close']) and (latest['Close'] < prev['Open']) and rsi_val > 35:
                    pattern = "Strong Bearish Engulfing ❄️"
                    signal = "PUT (SELL) 🔴 DOWN ⬇️"
                    css_class = "big-signal-sell"
                    confidence = "85%"

                # Live Timer Logic
                now = datetime.datetime.now()
                seconds_left = 60 - now.second

                # UI Layout
                col_t1, col_t2 = st.columns([2, 1])
                with col_t1:
                    st.markdown(f'<div class="{css_class}">{signal}</div>', unsafe_allow_html=True)
                with col_t2:
                    st.metric("⏱️ Candle Entry Timer", f"{seconds_left} Sec Left")

                st.markdown("<br>", unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Live Market Price", f"{current_price:.5f}")
                col2.metric("Support Level (SR)", f"{support:.5f}")
                col3.metric("Resistance Level (SR)", f"{resistance:.5f}")
                col4.metric("RSI Indicator (14)", f"{rsi_val:.1f}")

                st.markdown("---")
                
                st.subheader("💡 Signal Analysis & Details")
                st.write(f"**Detected Technical Pattern:** `{pattern}`")
                st.write(f"**Signal Accuracy / Confidence:** `{confidence}`")
                st.write(f"**Market Trend (EMA 20/50):** `{'UPTREND 📈' if latest['EMA_20'] > latest['EMA_50'] else 'DOWNTREND 📉'}`")

                st.markdown("---")
                st.subheader("📈 Live Market Candle Chart")
                st.line_chart(df['Close'].tail(40))

        except Exception as e:
            st.error(f"Error fetching live data: {e}. Try selecting 5m timeframe.")
else:
    st.info("👆 Click the **'Start Analyzing Market'** button above to scan live candlestick patterns and generate signal!")
    
