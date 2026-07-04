import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import plotly.graph_objects as go

# --- PAGE SETUP ---
st.set_page_config(page_title="AI Strategy Backtester", layout="wide", page_icon="🧠")
st.title("🧠 AI Strategy Backtester & Optimizer")
st.write("This AI tests thousands of parameter combinations to find the most profitable trading strategy.")

# --- TABS ---
tab1, tab2 = st.tabs(["📈 AI Stock Optimizer", "🧩 Option Payoff Calculator"])

# ==========================================
# TAB 1: AI STOCK OPTIMIZER
# ==========================================
with tab1:
    st.header("AI Moving Average Optimizer")
    st.write("The AI will scan from 5-day to 50-day Moving Averages to find the best crossover strategy.")
    
    col1, col2 = st.columns(2)
    with col1:
        symbol = st.text_input("Enter Stock Symbol", "RELIANCE")
    with col2:
        capital = st.number_input("Starting Capital (₹)", value=100000)
        
    if st.button("🚀 Run AI Optimization"):
        with st.spinner("AI is testing thousands of strategies... This takes 10 seconds."):
            try:
                # 1. Fetch Data
                yf_sym = symbol.upper().strip() + ".NS"
                data = yf.Ticker(yf_sym).history(period="2y")
                
                if data.empty:
                    st.error("Could not find data.")
                else:
                    bt_data = pd.DataFrame({
                        'Open': data['Open'].astype(float),
                        'High': data['High'].astype(float),
                        'Low': data['Low'].astype(float),
                        'Close': data['Close'].astype(float),
                        'Volume': data['Volume'].astype(float)
                    })
                    
                    # 2. Define Strategy
                    class SmaCross(Strategy):
                        n1 = 10  # Default fast MA
                        n2 = 20  # Default slow MA
                        
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
                    
                    # 3. Run AI Optimization
                    bt = Backtest(bt_data, SmaCross, cash=capital, commission=.002)
                    
                    # AI tests n1 from 5 to 40, and n2 from 10 to 50
                    stats = bt.optimize(
                        n1=range(5, 40, 5),
                        n2=range(10, 50, 5),
                        maximize='Return [%]',  # Tell AI to find highest return
                        constraint=lambda p: p.n1 < p.n2  # Fast MA must be smaller than Slow MA
                    )
                    
                    # 4. Display AI Results
                    st.success("AI Optimization Complete!")
                    
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Best Fast MA (n1)", stats['_strategy'].n1)
                    col_b.metric("Best Slow MA (n2)", stats['_strategy'].n2)
                    col_c.metric("Total Return", f"{stats['Return [%]']}%")
                    
                    st.subheader("Detailed AI Statistics")
                    st.write(f"Final Equity: ₹{stats['Equity Final [$]']:,.2f}")
                    st.write(f"Win Rate: {stats['Win Rate [%]']}%")
                    st.write(f"Max Drawdown: {stats['Max. Drawdown [%]']}%")
                    st.write(f"Number of Trades: {stats['# Trades']}")
                    
                    st.subheader("AI Optimized Equity Curve")
                    bt.plot()
                    
            except Exception as e:
                st.error(f"Error: {e}")

# ==========================================
# TAB 2: OPTION PAYOFF CALCULATOR
# ==========================================
with tab2:
    st.header("Option Strategy Payoff Calculator")
    st.write("Visualize how much money an Option Strategy makes at different market prices.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        strategy = st.selectbox("Choose Strategy", ["Long Call", "Long Put", "Bull Call Spread"])
    with col2:
        spot_price = st.number_input("Current NIFTY/Stock Price", value=22000)
    with col3:
        target_range = st.number_input("Price Range to Test (+/-)", value=500)
        
    if strategy == "Long Call":
        strike = st.number_input("Strike Price Bought", value=22000)
        premium = st.number_input("Premium Paid", value=100)
        
        if st.button("Calculate Payoff"):
            # Generate prices from -range to +range
            prices = np.linspace(spot_price - target_range, spot_price + target_range, 100)
            payoffs = []
            
            for p in prices:
                # Long Call payoff: Max(0, Price - Strike) - Premium
                intrinsic = max(0, p - strike)
                payoff = (intrinsic - premium) * 50 # *50 for NIFTY lot size
                payoffs.append(payoff)
                
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=prices, y=payoffs, mode='lines', name='Payoff', line=dict(color='blue', width=3)))
            fig.add_hline(y=0, line_dash="dash", line_color="red")
            fig.update_layout(title=f"{strategy} Payoff Diagram", xaxis_title="Price at Expiry", yaxis_title="Profit / Loss (₹)")
            st.plotly_chart(fig, use_container_width=True)
            
            st.info(f"Breakeven Price: ₹{strike + premium} (Lot size assumed 50)")
