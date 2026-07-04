import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. GROWW-STYLE UI & THEME ---
st.set_page_config(page_title="Groww Style Screener", layout="wide", page_icon="📈")

# Custom CSS to make it look like Groww
st.markdown("""
    <style>
        /* Groww Purple & Green Theme */
        .stButton>button {
            background-color: #5367ff;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 24px;
            font-weight: bold;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #00d09c;
            color: white;
        }
        /* Clean up Streamlit defaults */
        .css-1d391kg { padding-top: 2rem; }
        .st-b7 { color: #5367ff; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Groww-Style Stock Screener")
st.write("Scan top NSE stocks based on live price, daily movement, and volume.")

# --- 2. STOCK LIST (Top 15 NSE Stocks) ---
# In a real app, you would fetch all 2000+ stocks, but we use top 15 for speed
STOCK_LIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "SBIN.NS", "TATAMOTORS.NS", "ITC.NS", "AXISBANK.NS", "LT.NS",
    "WIPRO.NS", "MARUTI.NS", "SUNPHARMA.NS", "BAJFINANCE.NS", "HINDUNILVR.NS"
]

# --- 3. DATA FETCHING (Cached for 5 minutes) ---
@st.cache_data(ttl=300)
def fetch_stock_data():
    data = []
    for ticker_symbol in STOCK_LIST:
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="5d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                day_change_pct = ((current_price - prev_price) / prev_price) * 100
                volume = hist['Volume'].iloc[-1]
                
                data.append({
                    "Symbol": ticker_symbol.replace(".NS", ""),
                    "Current Price (₹)": round(current_price, 2),
                    "Day Change (%)": round(day_change_pct, 2),
                    "Volume": int(volume)
                })
        except:
            pass
    return pd.DataFrame(data)

# --- 4. SIDEBAR FILTERS (Groww Style) ---
st.sidebar.header("🔍 Screener Filters")
st.sidebar.write("Adjust the sliders to filter stocks.")

# We set default ranges wide enough to capture everything
min_price = st.sidebar.slider("Minimum Price (₹)", 0.0, 5000.0, 0.0, 50.0)
max_price = st.sidebar.slider("Maximum Price (₹)", 0.0, 5000.0, 5000.0, 50.0)
min_change = st.sidebar.slider("Minimum Day Change (%)", -10.0, 10.0, 0.0, 0.5)
min_volume = st.sidebar.slider("Minimum Volume", 0, 10000000, 0, 100000)

# --- 5. MAIN APP LOGIC ---
if st.button("Scan Stocks 🔎"):
    with st.spinner("Fetching live market data..."):
        df = fetch_stock_data()
        
        if df.empty:
            st.error("Could not fetch data. Try again later.")
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
                        "Day Change (%)": st.column_config.NumberColumn(
                            format="%.2f%%"
                        )
                    }
                )
