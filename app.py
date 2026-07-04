import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- PAGE SETUP ---
st.set_page_config(page_title="AI Strategy Scanner", layout="wide", page_icon="🎯")
st.title("🎯 Custom Strategy Scanner")
st.write("Build your own trading strategy using the sidebar, and scan 50+ NSE stocks instantly to find matches.")

# --- STOCK LIST (Top 50 NSE) ---
STOCK_LIST = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","SBIN.NS","TATAMOTORS.NS",
    "ITC.NS","AXISBANK.NS","LT.NS","WIPRO.NS","MARUTI.NS","SUNPHARMA.NS","BAJFINANCE.NS",
    "HINDUNILVR.NS","KOTAKBANK.NS","ASIANPAINT.NS","HCLTECH.NS","BHARTIARTL.NS","TITAN.NS",
    "TATASTEEL.NS","ULTRACEMCO.NS","NESTLEIND.NS","ONGC.NS","NTPC.NS","POWERGRID.NS","M&M.NS",
    "TECHM.NS","COALINDIA.NS","BAJAJFINSV.NS","GRASIM.NS","HDFCLIFE.NS","SBILIFE.NS","JSWSTEEL.NS",
    "DIVISLAB.NS","DRREDDY.NS","CIPLA.NS","BRITANNIA.NS","EICHERMOT.NS","ADANIENT.NS","ADANIPORTS.NS",
    "HINDALCO.NS","HEROMOTOCO.NS","BAJAJ-AUTO.NS","VEDL.NS","TATACONSUM.NS","GAIL.NS","IOC.NS",
    "BPCL.NS","SHRIRAMFIN.NS"
]

# --- HELPER FUNCTIONS TO CALCULATE INDICATORS ---
def calculate_rsi(series, period=14):
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1.0 + rs))

def calculate_sma(series, period):
    return series.rolling(window=period).mean()

# --- SIDEBAR: STRATEGY BUILDER ---
st.sidebar.header("🛠️ Build Your Strategy")
st.sidebar.write("Select up to 2 conditions to find matching stocks.")

# Condition 1
st.sidebar.subheader("Condition 1")
ind1 = st.sidebar.selectbox("Indicator 1", ["Close Price", "SMA 20", "SMA 50", "RSI 14"])
op1 = st.sidebar.selectbox("Operator", [">", "<"])
val1_type = st.sidebar.selectbox("Compare against", ["A Number", "Another Indicator"])
if val1_type == "A Number":
    val1 = st.sidebar.number_input("Value", value=100.0)
else:
    val1 = st.sidebar.selectbox("Indicator 2", ["Close Price", "SMA 20", "SMA 50", "RSI 14"])

# Condition 2 (Optional)
use_cond2 = st.sidebar.checkbox("Add Condition 2 (AND)")
if use_cond2:
    st.sidebar.subheader("Condition 2")
    ind2 = st.sidebar.selectbox("Indicator A", ["Close Price", "SMA 20", "SMA 50", "RSI 14"], key="ind2")
    op2 = st.sidebar.selectbox("Operator", [">", "<"], key="op2")
    val2_type = st.sidebar.selectbox("Compare against", ["A Number", "Another Indicator"], key="val2_type")
    if val2_type == "A Number":
        val2 = st.sidebar.number_input("Value", value=50.0, key="val2")
    else:
        val2 = st.sidebar.selectbox("Indicator B", ["Close Price", "SMA 20", "SMA 50", "RSI 14"], key="val2_sel")

# --- MAIN APP LOGIC ---
if st.button("🔍 Scan Market for Matches"):
    with st.spinner("Scanning 50+ stocks against your strategy... (Takes ~10 seconds)"):
        
        # Download all data at once for speed
        data = yf.download(STOCK_LIST, period="3mo", progress=False, threads=True)
        
        matching_stocks = []
        
        for ticker in STOCK_LIST:
            try:
                if ticker not in data['Close'].columns:
                    continue
                    
                df = pd.DataFrame({
                    'Close': data['Close'][ticker].dropna(),
                    'High': data['High'][ticker].dropna(),
                    'Low': data['Low'][ticker].dropna()
                })
                
                if len(df) < 50:
                    continue
                
                # Calculate Indicators
                df['SMA 20'] = calculate_sma(df['Close'], 20)
                df['SMA 50'] = calculate_sma(df['Close'], 50)
                df['RSI 14'] = calculate_rsi(df['Close'], 14)
                
                # Get today's values (last row)
                today = df.iloc[-1]
                
                # Helper to get value
                def get_val(name):
                    if name == "Close Price": return today['Close']
                    elif name == "SMA 20": return today['SMA 20']
                    elif name == "SMA 50": return today['SMA 50']
                    elif name == "RSI 14": return today['RSI 14']
                    else: return float(name)
                
                # Check Condition 1
                left1 = get_val(ind1)
                right1 = get_val(val1) if val1_type == "Another Indicator" else val1
                cond1_met = (left1 > right1) if op1 == ">" else (left1 < right1)
                
                # Check Condition 2 (if used)
                cond2_met = True
                if use_cond2:
                    left2 = get_val(ind2)
                    right2 = get_val(val2) if val2_type == "Another Indicator" else val2
                    cond2_met = (left2 > right2) if op2 == ">" else (left2 < right2)
                
                # If both conditions are met, add to list
                if cond1_met and cond2_met:
                    matching_stocks.append({
                        "Symbol": ticker.replace(".NS", ""),
                        "Close Price (₹)": round(today['Close'], 2),
                        "SMA 20 (₹)": round(today['SMA 20'], 2) if not np.isnan(today['SMA 20']) else "N/A",
                        "RSI 14": round(today['RSI 14'], 2) if not np.isnan(today['RSI 14']) else "N/A"
                    })
                    
            except Exception as e:
                pass
                
        # Display Results
        if matching_stocks:
            st.success(f"🎯 Found {len(matching_stocks)} stocks matching your strategy!")
            result_df = pd.DataFrame(matching_stocks)
            st.dataframe(result_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No stocks found matching your strategy today. Try changing your conditions.")
