import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- PAGE SETUP ---
st.set_page_config(page_title="Chart Pattern Scanner", layout="wide", page_icon="📊")
st.title("📊 Chart Pattern Scanner (Nifty 500)")
st.write("Scans 150+ top NSE stocks instantly to find Breakouts and Candlestick Patterns.")

# --- NIFTY 500 STOCK LIST (Top 150+ highly liquid) ---
STOCK_LIST = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","SBIN.NS","TATAMOTORS.NS",
    "ITC.NS","AXISBANK.NS","LT.NS","WIPRO.NS","MARUTI.NS","SUNPHARMA.NS","BAJFINANCE.NS",
    "HINDUNILVR.NS","KOTAKBANK.NS","ASIANPAINT.NS","HCLTECH.NS","BHARTIARTL.NS","TITAN.NS",
    "TATASTEEL.NS","ULTRACEMCO.NS","NESTLEIND.NS","ONGC.NS","NTPC.NS","POWERGRID.NS","M&M.NS",
    "TECHM.NS","COALINDIA.NS","BAJAJFINSV.NS","GRASIM.NS","HDFCLIFE.NS","SBILIFE.NS","JSWSTEEL.NS",
    "DIVISLAB.NS","DRREDDY.NS","CIPLA.NS","BRITANNIA.NS","EICHERMOT.NS","ADANIENT.NS","ADANIPORTS.NS",
    "HINDALCO.NS","HEROMOTOCO.NS","BAJAJ-AUTO.NS","VEDL.NS","TATACONSUM.NS","GAIL.NS","IOC.NS",
    "BPCL.NS","SHRIRAMFIN.NS","JINDALSTEL.NS","PNB.NS","BANKBARODA.NS","CANBK.NS","IDFCFIRSTB.NS",
    "INDUSINDBK.NS","AUBANK.NS","FEDERALBNK.NS","BANDHANBNK.NS","DMART.NS","TRENT.NS","ZOMATO.NS",
    "NYKAA.NS","PAYTM.NS","POLICYBZR.NS","BROS.NS","DMCC.NS","LAURUSLABS.NS","AUROPHARMA.NS",
    "LUPIN.NS","BIOCON.NS","SYNGENE.NS","CADILAHC.NS","TORNTPHARM.NS","PIIND.NS","UPL.NS",
    "APOLLOHOSP.NS","FORTIS.NS","MAXHEALTH.NS","GLOBALHEALTH.NS","LALPATHLAB.NS","METHEALTH.NS",
    "DABUR.NS","GODREJCP.NS","COLPAL.NS","MARICO.NS","UBL.NS","MCDOWELL-N.NS","PGHH.NS",
    "VSTIND.NS","HINDPETRO.NS","TATAPOWER.NS","ADANIPOWER.NS","JSWENERGY.NS","NHPC.NS","SJVN.NS",
    "SUZLON.NS","INOXWIND.NS","KPITTECH.NS","TATAELXSI.NS","BSE.NS","IEX.NS","IRCTC.NS",
    "INDHOTEL.NS","JUBLFOOD.NS","DEVYANI.NS","SAPPHIRE.NS","AMARAJABAT.NS","EXIDEIND.NS",
    "BOSCHLTD.NS","MOTHERSON.NS","BharatForge.NS","RAMCOCEM.NS","SHREECEM.NS","AMBUJACEM.NS",
    "ACC.NS","JKCEMENT.NS","DALBHARAT.NS","PIDILITIND.NS","SIEMENS.NS","ABB.NS","HAVELLS.NS",
    "POLYCAB.NS","DIXON.NS","AMBER.NS","KAYNES.NS","SYRMA.NS","HINDUSTANZINC.NS","BALCO.NS",
    "NMDC.NS","ATGL.NS","GTLINFRA.NS","INDIAMART.NS","INFOEDGE.NS","ABFRL.NS","PAGEIND.NS"
]

# --- BULK DATA FETCHING ---
@st.cache_data(ttl=300)
def fetch_bulk_data():
    # Fetch 3 months of data to calculate 20-day highs/lows
    data = yf.download(STOCK_LIST, period="3mo", progress=False, threads=True)
    return data

# --- PATTERN DETECTION LOGIC ---
def detect_patterns(data):
    results = []
    
    closes = data['Close']
    opens = data['Open']
    highs = data['High']
    lows = data['Low']
    
    for ticker in STOCK_LIST:
        if ticker not in closes.columns:
            continue
            
        # Get last 3 days of data
        hist_close = closes[ticker].dropna().tail(3)
        hist_open = opens[ticker].dropna().tail(3)
        hist_high = highs[ticker].dropna().tail(20)
        
        if len(hist_close) < 3 or len(hist_high) < 20:
            continue
            
        # Today's and Yesterday's data
        t_close = hist_close.iloc[-1]
        t_open = hist_open.iloc[-1]
        y_close = hist_close.iloc[-2]
        y_open = hist_open.iloc[-2]
        
        pattern = "None"
        
        # 1. Bullish Engulfing Pattern
        # Yesterday was Red (Close < Open) AND Today is Green (Close > Open)
        # Today's body completely covers Yesterday's body
        if (y_close < y_open) and (t_close > t_open):
            if (t_close >= y_open) and (t_open <= y_close):
                pattern = "Bullish Engulfing"
                
        # 2. 20-Day Breakout Pattern
        # Today's close is the highest in the last 20 days
        max_20_day_high = hist_high.iloc[:-1].max() # Max of last 19 days
        if t_close > max_20_day_high:
            pattern = "20-Day Breakout"
            
        if pattern != "None":
            results.append({
                "Symbol": ticker.replace(".NS", ""),
                "Pattern Detected": pattern,
                "Current Price (₹)": round(t_close, 2),
                "20-Day High (₹)": round(hist_high.max(), 2)
            })
            
    return pd.DataFrame(results)

# --- MAIN APP UI ---
st.sidebar.header("📊 Pattern Settings")
st.sidebar.write("The scanner checks the last 3 days of candles for patterns.")

if st.button("🔍 Scan Nifty 500 for Patterns"):
    with st.spinner("Fetching data for 150+ stocks and detecting patterns... (Takes ~10 seconds)"):
        try:
            raw_data = fetch_bulk_data()
            df_results = detect_patterns(raw_data)
            
            if df_results.empty:
                st.warning("No chart patterns found in the market today. Try again tomorrow!")
            else:
                st.success(f"🎯 Found {len(df_results)} stocks with chart patterns today!")
                
                # Split into two columns for better viewing
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🚀 Breakout Stocks")
                    breakout_df = df_results[df_results['Pattern Detected'] == '20-Day Breakout']
                    st.dataframe(breakout_df, use_container_width=True, hide_index=True)
                    
                with col2:
                    st.subheader("🟢 Bullish Engulfing Stocks")
                    engulfing_df = df_results[df_results['Pattern Detected'] == 'Bullish Engulfing']
                    st.dataframe(engulfing_df, use_container_width=True, hide_index=True)
                    
        except Exception as e:
            st.error(f"Error scanning market: {e}")
