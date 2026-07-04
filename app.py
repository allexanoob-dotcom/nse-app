import streamlit as st
import pandas as pd
import pyotp
from SmartApi import SmartConnect
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import datetime
import yfinance as yf

st.set_page_config(page_title="Angel One Pro Screener", layout="wide")
st.title("🚀 Pro Screener & Backtester")

# --- 1. SIDEBAR LOGIN (Angel One) ---
st.sidebar.header("🔐 Angel One Login")
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
    else:
        st.sidebar.warning("Please fill all fields.")

# --- 2. MAIN APP ---
if st.session_state.smart_api is None:
    st.info("👈 Please login using your Angel One credentials in the sidebar to continue.")
else:
    st.markdown("---")
    
    # --- BACKTESTING ENGINE (Using Yahoo Finance Data) ---
    st.header("📈 Backtesting Engine")
    st.write("Uses Yahoo Finance historical data. Works perfectly on the cloud!")
    
    symbol = st.text_input("Enter NSE Stock Symbol (e.g., RELIANCE, TCS, SBIN)", "RELIANCE")
    
    if st.button("Run Backtest"):
        with st.spinner(f"Fetching historical data for {symbol}..."):
            try:
                # Yahoo Finance uses ".NS" at the end for NSE stocks
                yf_symbol = symbol.upper().strip() + ".NS"
                
                # Using Ticker().history() is more stable than download()
                ticker = yf.Ticker(yf_symbol)
                data = ticker.history(period="1y")
                
                if data.empty:
                    st.error("Could not find data. Please check the stock symbol.")
                else:
                    # Format for Backtesting library
                    bt_data = pd.DataFrame({
                        'Open': data['Open'].astype(float),
                        'High': data['High'].astype(float),
                        'Low': data['Low'].astype(float),
                        'Close': data['Close'].astype(float),
                        'Volume': data['Volume'].astype(float)
                    })
                    
                    # Strategy
                    class SmaCross(Strategy):
                        n1 = 10
                        n2 = 20
                        def init(self):
                            self.sma1 = self.I(lambda x: pd.Series(x).rolling(self.n1).mean(), self.data.Close)
                            self.sma2 = self.I(lambda x: pd.Series(x).rolling(self.n2).mean(), self.data.Close)
                        def next(self):
                            if crossover(self.sma1, self.sma2):
                                self.position.close()
                                self.buy()
                            elif crossover(self.sma2, self.sma1):
                                self.position.close()
                                self.sell()

                    bt = Backtest(bt_data, SmaCross, cash=100000, commission=.002)
                    stats = bt.run()

                    st.subheader("Backtest Statistics")
                    st.write(f"Final Equity: ₹{stats['Equity Final [$]']:,.2f}")
                    st.write(f"Total Return: {stats['Return [%]']}%")
                    st.write(f"Win Rate: {stats['Win Rate [%]']}%")
                    st.write(f"Max Drawdown: {stats['Max. Drawdown [%]']}%")
                    st.subheader("Equity Curve & Trades")
                    bt.plot()

            except Exception as e:
                st.error(f"Error during backtesting: {e}")
