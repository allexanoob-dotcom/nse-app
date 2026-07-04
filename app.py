import streamlit as st
from streamlit.cache_data import cache_data # Add this
import streamlit as st
import pandas as pd
from nsepython import nse_eq, nse_optionchain_scrapper, equity_history
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="NSE Screener & Backtester", layout="wide")
st.title("📈 NSE Stock & Options Screener + Backtester")

# --- 1. STOCK SCREENER ---
# Cache the data for 5 minutes (300 seconds)
@st.cache_data(ttl=300)
def fetch_nse_stocks():
    nse_data = nse_eq("NIFTY 50")
    stocks = []
    for item in nse_data['data']:
        stocks.append({
            'Symbol': item['symbol'],
            'Last Price': item['lastPrice'],
            'Day Change (%)': round(item['perChange'], 2),
            'Volume': item['totalTradedVolume']
        })
    return pd.DataFrame(stocks)

if st.button("Run Stock Screener"):
    with st.spinner("Fetching live NSE data..."):
        try:
            df = fetch_nse_stocks()
            # ... rest of your filtering code ...# --- 2. OPTIONS SCREENER ---
# Cache the data for 5 minutes (300 seconds)
@st.cache_data(ttl=300)
def fetch_nse_stocks():
    nse_data = nse_eq("NIFTY 50")
    stocks = []
    for item in nse_data['data']:
        stocks.append({
            'Symbol': item['symbol'],
            'Last Price': item['lastPrice'],
            'Day Change (%)': round(item['perChange'], 2),
            'Volume': item['totalTradedVolume']
        })
    return pd.DataFrame(stocks)

if st.button("Run Stock Screener"):
    with st.spinner("Fetching live NSE data..."):
        try:
            df = fetch_nse_stocks()
            # ... rest of your filtering code ...# --- 3. BACKTESTING ENGINE ---
st.header("3. Backtesting Engine (SMA Crossover)")
symbol = st.text_input("Enter NSE Stock Symbol (e.g., SBIN, RELIANCE, TCS)", "SBIN")

if st.button("Run Backtest"):
    with st.spinner(f"Fetching historical data for {symbol}..."):
        try:
            end_date = datetime.datetime.today().strftime('%d-%m-%Y')
            start_date = (datetime.datetime.today() - datetime.timedelta(days=365)).strftime('%d-%m-%Y')
            hist_data = equity_history(symbol, start_date, end_date)
            
            bt_data = pd.DataFrame({
                'Open': hist_data['CH_OPENING_PRICE'].astype(float),
                'High': hist_data['CH_TRADE_HIGH_PRICE'].astype(float),
                'Low': hist_data['CH_TRADE_LOW_PRICE'].astype(float),
                'Close': hist_data['CH_CLOSING_PRICE'].astype(float),
                'Volume': hist_data['CH_TOT_TRADED_QTY'].astype(float)
            }, index=pd.to_datetime(hist_data['mTIMESTAMP']))
            bt_data = bt_data[~bt_data.index.duplicated(keep='first')].sort_index()

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
            st.error(f"Error during backtesting: {e}. Check the stock symbol.")
import mibian

def calculate_greeks(spot, strike, days_to_expiry, iv, option_type='CE'):
    if days_to_expiry <= 0 or iv <= 0:
        return None, None
    
    # mibian.BS([Spot, Strike, InterestRate, DaysToExpiry], volatility=IV)
    bs = mibian.BS([spot, strike, 10, days_to_expiry], volatility=iv*100)
    
    if option_type == 'CE':
        return bs.callDelta, bs.callTheta
    else:
        return bs.putDelta, bs.putTheta