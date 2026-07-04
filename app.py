import streamlit as st
import pandas as pd
from nsepython import nse_get_top_gainers, nse_optionchain_scrapper, equity_history
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import datetime

st.set_page_config(page_title="NSE Screener & Backtester", layout="wide")
st.title("📈 NSE Stock & Options Screener + Backtester")

st.header("1. Live Stock Screener")
st.write("Fetches live NSE Top Gainers data.")

@st.cache_data(ttl=300)
def fetch_nse_stocks():
    # Using the correct function to get a list of stocks
    gainers = nse_get_top_gainers()
    stocks = []
    for item in gainers:
        stocks.append({
            'Symbol': item['symbol'],
            'Last Price': item['ltp'],
            'Day Change (%)': round(float(item['pChange']), 2),
        })
    return pd.DataFrame(stocks)

if st.button("Run Stock Screener"):
    with st.spinner("Fetching live NSE data..."):
        try:
            df = fetch_nse_stocks()
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error fetching NSE data: {e}")

st.markdown("---")

st.header("2. Live Options Chain Screener (NIFTY)")
st.write("Filters NIFTY options based on Open Interest (OI).")

@st.cache_data(ttl=300)
def fetch_nse_options():
    oi_data = nse_optionchain_scrapper("NIFTY")
    options_list = []
    for record in oi_data['records']['data']:
        strike = record.get('strikePrice')
        expiry = record.get('expiryDate')
        if 'CE' in record:
            options_list.append({'Strike': strike, 'Type': 'CE', 'Expiry': expiry, 'OI': record['CE'].get('openInterest'), 'IV': record['CE'].get('impliedVolatility')})
        if 'PE' in record:
            options_list.append({'Strike': strike, 'Type': 'PE', 'Expiry': expiry, 'OI': record['PE'].get('openInterest'), 'IV': record['PE'].get('impliedVolatility')})
    return pd.DataFrame(options_list)

if st.button("Run Options Screener"):
    with st.spinner("Fetching NSE Options Chain..."):
        try:
            opt_df = fetch_nse_options()
            high_oi_df = opt_df.sort_values(by='OI', ascending=False).head(10)
            st.dataframe(high_oi_df, use_container_width=True)
        except Exception as e:
            st.error(f"NSE blocked the cloud server or market is closed. Error: {e}")

st.markdown("---")

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
