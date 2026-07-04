import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. GROWW-STYLE UI & THEME ---
st.set_page_config(page_title="Groww Style Screener", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .stButton>button {
            background-color: #5367ff; color: white; border-radius: 8px;
            border: none; padding: 10px 24px; font-weight: bold; width: 100%;
        }
        .stButton>button:hover {
            background-color: #00d09c; color: white;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Groww-Style Bulk Stock Screener")
st.write("Scans 150+ top NSE stocks in seconds using bulk download.")

# --- 2. STOCK LIST (Top 150+ NSE Stocks across sectors) ---
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
    "DABUR.NS","GODREJCP.NS","COLPAL.NS","MARICO.NS","BRITANNIA.NS","UBL.NS","MCDOWELL-N.NS",
    "TATACONSUM.NS","PGHH.NS","VSTIND.NS","NESTLEIND.NS","HINDPETRO.NS","BPCL.NS","ONGC.NS",
    "GAIL.NS","NTPC.NS","POWERGRID.NS","TATAPOWER.NS","ADANIPOWER.NS","JSWENERGY.NS","NHPC.NS",
    "SJVN.NS","SUZLON.NS","INOXWIND.NS","KPITTECH.NS","TATAELXSI.NS","BSE.NS","IEX.NS",
    "IRCTC.NS","INDHOTEL.NS","JUBLFOOD.NS","DEVYANI.NS","SAPPHIRE.NS","TRENT.NS","ABEL.NS",
    "AMARAJABAT.NS","EXIDEIND.NS","BOSCHLTD.NS","MOTHERSON.NS","BharatForge.NS","RAMCOCEM.NS",
    "ULTRACEMCO.NS","SHREECEM.NS","AMBUJACEM.NS","ACC.NS","GRASIM.NS","JKCEMENT.NS","DALBHARAT.NS"
]

# --- 3. BULK DATA FETCHING (Super Fast) ---
@st.cache_data(ttl=300)
def fetch_bulk_stock_data():
    # 1. Download all stocks at once! (period="5d" to ensure we have yesterday's close)
    data = yf.download(STOCK_LIST, period="5d", progress=False, threads=True)
    
    if data.empty:
        return pd.DataFrame()
        
    # 2. Extract Close prices and Volumes
    closes = data['Close']
    volumes = data['Volume']
    
    # 3. Calculate Changes
    results = []
    for ticker in STOCK_LIST:
        if ticker in closes.columns:
            # Get last valid (today) and second to last (yesterday) prices
            valid_closes = closes[ticker].dropna()
            if len(valid_closes) >= 2:
                current_price = valid_closes.iloc[-1]
                prev_price = valid_closes.iloc[-2]
                day_change_pct = ((current_price - prev_price) / prev_price) * 100
                volume = volumes[ticker].dropna().iloc[-1]
                
                results.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "Current Price (₹)": round(current_price, 2),
                    "Day Change (%)": round(day_change_pct, 2),
                    "Volume": int(volume)
                })
                
    return pd.DataFrame(results)

# --- 4. SIDEBAR FILTERS (Groww Style) ---
st.sidebar.header("🔍 Screener Filters")
st.sidebar.write("Adjust sliders to filter stocks.")

min_price = st.sidebar.slider("Minimum Price (₹)", 0.0, 5000.0, 0.0, 50.0)
max_price = st.sidebar.slider("Maximum Price (₹)", 0.0, 10000.0, 10000.0, 50.0)
min_change = st.sidebar.slider("Minimum Day Change (%)", -10.0, 10.0, 0.0, 0.5)
min_volume = st.sidebar.slider("Minimum Volume", 0, 50000000, 0, 100000)

# --- 5. MAIN APP LOGIC ---
if st.button("Scan 150+ Stocks 🔎"):
    with st.spinner("Fetching bulk live market data... (2 seconds)"):
        df = fetch_bulk_stock_data()
        
        if df.empty:
            st.error("Could not fetch data. Market might be closed or API blocked.")
        else:
            # Apply Filters
            filtered_df = df[
                (df['Current Price (₹)'] >= min_price) &
                (df['Current Price (₹)'] <= max_price) &
                (df['Day Change (%)'] >= min_change) &
                (df['Volume'] >= min_volume)
            ].sort_values(by="Day Change (%)", ascending=False)
            
            if filtered_df.empty:
                st.warning("No stocks found matching your filters. Try widening your search.")
            else:
                st.success(f"Found {len(filtered_df)} stocks matching your criteria.")
                # Display clean table
                st.dataframe(
                    filtered_df, 
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Day Change (%)": st.column_config.NumberColumn(format="%.2f%%")
                    }
                )
