import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import pyotp
from SmartApi import SmartConnect
import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Pro Stock & Option Terminal", layout="wide", page_icon="🚀")
st.title("🚀 Pro Stock & Option Terminal")

# --- ANGEL ONE LOGIN (For Options) ---
st.sidebar.header("🔐 Angel One Login (For Options)")
api_key = st.sidebar.text_input("API Key")
client_code = st.sidebar.text_input("Client Code")
password = st.sidebar.text_input("Password", type="password")
totp_secret = st.sidebar.text_input("TOTP Secret")

if 'smart_api' not in st.session_state:
    st.session_state.smart_api = None

if st.sidebar.button("Login to Angel One"):
    if api_key and client_code and password and totp_secret:
        try:
            obj = SmartConnect(api_key=api_key)
            totp = pyotp.TOTP(totp_secret).now()
            data = obj.generateSession(client_code, password, totp)
            if data['status']:
                st.session_state.smart_api = obj
                st.sidebar.success("Login Successful! ✅")
            else:
                st.sidebar.error(f"Login Failed: {data['message']}")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# --- STOCK LIST (Top 100 NSE) ---
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
    "ACC.NS","JKCEMENT.NS","DALBHARAT.NS"
]

# --- TABS SETUP ---
tab1, tab2, tab3 = st.tabs(["📊 Stock Scanner", "📈 Chart Patterns", "🧩 Option Strategies"])

# --- TAB 1: SCANNER ---
with tab1:
    st.header("Bulk Stock Scanner")
    st.write("Scans 100+ NSE stocks in 2 seconds to find top gainers.")
    
    @st.cache_data(ttl=300)
    def fetch_bulk_data():
        data = yf.download(STOCK_LIST, period="5d", progress=False, threads=True)
        closes = data['Close']
        volumes = data['Volume']
        results = []
        for ticker in STOCK_LIST:
            if ticker in closes.columns:
                valid_closes = closes[ticker].dropna()
                if len(valid_closes) >= 2:
                    cp = valid_closes.iloc[-1]
                    pp = valid_closes.iloc[-2]
                    change = ((cp - pp) / pp) * 100
                    vol = volumes[ticker].dropna().iloc[-1]
                    results.append({"Symbol": ticker.replace(".NS",""), "Price": round(cp,2), "Change(%)": round(change,2), "Volume": int(vol)})
        return pd.DataFrame(results)

    if st.button("Scan Market 🔎", key="scan"):
        with st.spinner("Scanning..."):
            df = fetch_bulk_data()
            if not df.empty:
                st.dataframe(df.sort_values(by="Change(%)", ascending=False), use_container_width=True, hide_index=True)

# --- TAB 2: CHART PATTERNS ---
with tab2:
    st.header("Candlestick Chart Pattern Finder")
    st.write("Type any stock symbol to see live Candlesticks and Moving Averages.")
    
    chart_symbol = st.text_input("Enter Stock Symbol (e.g., RELIANCE)", "RELIANCE", key="chart_sym")
    
    if st.button("Draw Chart 📈", key="draw"):
        with st.spinner(f"Drawing chart for {chart_symbol}..."):
            try:
                yf_sym = chart_symbol.upper().strip() + ".NS"
                df = yf.Ticker(yf_sym).history(period="6mo")
                
                if not df.empty:
                    # Calculate Moving Averages
                    df['MA20'] = df['Close'].rolling(window=20).mean()
                    df['MA50'] = df['Close'].rolling(window=50).mean()
                    
                    # Create Plotly Candlestick Chart
                    fig = go.Figure(data=[go.Candlestick(
                        x=df.index,
                        open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'],
                        name="Candles"
                    )])
                    
                    # Add Moving Averages
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', name='MA 20', line=dict(color='blue', width=1)))
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='MA 50', line=dict(color='orange', width=1)))
                    
                    fig.update_layout(title=f"{chart_symbol} Live Chart", xaxis_rangeslider_visible=False, height=600)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Stock not found.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 3: OPTION STRATEGIES ---
with tab3:
    st.header("NIFTY Option Chain Strategy Finder")
    st.write("Finds Highest Open Interest (Support & Resistance) using Angel One.")
    
    if st.session_state.smart_api is None:
        st.warning("Please login to Angel One in the sidebar to use Option Strategies.")
    else:
        if st.button("Fetch Option Chain 🧩", key="opt"):
            with st.spinner("Fetching live NIFTY options..."):
                try:
                    obj = st.session_state.smart_api
                    # Angel One API for Option Chain
                    oc = obj.optionChain("NSE", "NIFTY")
                    
                    if oc['status']:
                        opt_data = oc['data']['oc']
                        records = []
                        for strike, chain in opt_data.items():
                            ce_oi = chain.get('ce', {}).get('oi', 0)
                            pe_oi = chain.get('pe', {}).get('oi', 0)
                            if ce_oi > 0 or pe_oi > 0:
                                records.append({
                                    "Strike Price": strike,
                                    "Call OI (Resistance)": ce_oi,
                                    "Put OI (Support)": pe_oi
                                })
                        
                        opt_df = pd.DataFrame(records)
                        opt_df['Total OI'] = opt_df['Call OI (Resistance)'] + opt_df['Put OI (Support)']
                        opt_df = opt_df.sort_values(by="Total OI", ascending=False).head(10)
                        
                        st.success("Top 10 Strikes with Highest Open Interest:")
                        st.dataframe(opt_df, use_container_width=True, hide_index=True)
                    else:
                        st.error("Failed to fetch option chain.")
                except Exception as e:
                    st.error(f"Error fetching options: {e}")
