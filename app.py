import streamlit as st
import pandas as pd
import pyotp
from SmartApi import SmartConnect
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import datetime

st.set_page_config(page_title="Angel One Pro Screener", layout="wide")
st.title("🚀 Angel One Pro Screener & Backtester")

# --- 1. SIDEBAR LOGIN ---
st.sidebar.header("🔐 Angel One Login")
api_key = st.sidebar.text_input("API Key")
client_code = st.sidebar.text_input("Client Code")
password = st.sidebar.text_input("Password", type="password")
totp_secret = st.sidebar.text_input("TOTP Secret")

# Initialize session state to remember the login
if 'smart_api' not in st.session_state:
    st.session_state.smart_api = None

if st.sidebar.button("Login"):
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
    obj = st.session_state.smart_api
    st.markdown("---")
    
    # --- BACKTESTING ENGINE (Using Angel One Data) ---
    st.header("📈 Backtesting Engine (Cloud Supported)")
    st.write("Uses Angel One historical data so it works perfectly on the internet!")
    
    symbol = st.text_input("Enter Trading Symbol (e.g., RELIANCE-EQ)", "RELIANCE-EQ")
    token = st.text_input("Enter Symbol Token (e.g., 2885 for Reliance)", "2885")
    
    if st.button("Run Backtest"):
        with st.spinner(f"Fetching historical data for {symbol}..."):
            try:
                # Angel One historical data format
                end_date = datetime.datetime.today()
                start_date = end_date - datetime.timedelta(days=365)
                
                # Format dates exactly how Angel One wants them
                start_str = start_date.strftime("%Y-%m-%d %H:%M")
                end_str = end_date.strftime("%Y-%m-%d %H:%M")
                
                # Use the NEW candleData function
                historicParam = {
                    "exchange": "NSE",
                    "symboltoken": token,
                    "interval": "ONE_DAY",
                    "fromdate": start_str,
                    "todate": end_str
                }
                hist = obj.candleData(historicParam)
                
                # Format the data into a Pandas DataFrame
                df = pd.DataFrame(hist['data'], columns=["timestamp", "open", "high", "low", "close", "volume"])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('timestamp', inplace=True)
                
                bt_data = pd.DataFrame({
                    'Open': df['open'].astype(float),
                    'High': df['high'].astype(float),
                    'Low': df['low'].astype(float),
                    'Close': df['close'].astype(float),
                    'Volume': df['volume'].astype(float)
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
                st.error(f"Error during backtesting: {e}. Check your Symbol and Token.")
