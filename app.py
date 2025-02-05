import streamlit as st
import requests
import datetime

# Load API Key from Streamlit Secrets
API_KEY = st.secrets["fmp"]["api_key"]

# Base URLs for FMP API
BASE_URL = "https://financialmodelingprep.com/api/v3"

# Function to get Discounted Cash Flow (DCF) Valuation
def get_dcf(ticker):
    url = f"{BASE_URL}/discounted-cash-flow/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200 and response.json():
        return response.json()[0]
    return {}

# Function to get Financial Ratios (Ensures Annual Data)
def get_financial_ratios(ticker):
    url = f"{BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200 and response.json():
        return response.json()[0]  # Extract most recent annual ratios
    return {}

# Function to get Sector P/E Ratio
def get_sector_pe():
    today = datetime.date.today().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/sector_price_earning_ratio?date={today}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200 and response.json():
        return {entry["sector"]: entry["pe"] for entry in response.json()}
    return {}

# Function to get Stock Profile (Sector Info)
def get_stock_profile(ticker):
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200 and response.json():
        return response.json()[0]
    return {}

# Streamlit App UI
st.title("📈 Stock Valuation & Financial Metrics")

ticker = st.text_input("Enter stock ticker:", "AAPL")

if st.button("Analyze"):
    # Fetch Data
    dcf_data = get_dcf(ticker)
    ratios = get_financial_ratios(ticker)
    sector_data = get_sector_pe()
    stock_profile = get_stock_profile(ticker)

    # Extract Relevant Data
    stock_price = dcf_data.get("Stock Price", "N/A")
    dcf_valuation = dcf_data.get("dcf", "N/A")
    stock_sector = stock_profile.get("sector", "Unknown")

    # Financial Ratios
    pe_ratio = ratios.get("priceEarnings", "N/A")
    current_ratio = ratios.get("currentRatio", "N/A")
    quick_ratio = ratios.get("quickRatio", "N/A")
    debt_to_equity = ratios.get("debtEquityRatio", "N/A")
    roe = ratios.get("returnOnEquity", "N/A")

    # Format ROE as a percentage
    roe_display = f"{roe*100:.2f}%" if isinstance(roe, (int, float)) else "N/A"

    # Get Sector P/E
    sector_pe = sector_data.get(stock_sector, "N/A")

    # Display Data
    st.subheader(f"Valuation Metrics for {ticker}")
    col1, col2 = st.columns(2)
    col1.metric("💰 DCF Valuation", f"${dcf_valuation}")
    col2.metric("📊 Stock Price", f"${stock_price}")

    # Financial Ratios
    st.subheader("📊 Key Financial Ratios")
    st.markdown(f"""
    **Price-to-Earnings (P/E) Ratio:** {pe_ratio}  
    *Higher P/E suggests strong growth expectations. Below 15 = undervalued, 15-25 = fair, above 25 = overvalued.*  

    **Current Ratio:** {current_ratio}  
    *Above 1.5 = strong liquidity, 1.0-1.5 = adequate, below 1 = potential liquidity issues.*  

    **Quick Ratio:** {quick_ratio}  
    *Above 1.0 = strong liquidity, 0.5-1.0 = acceptable, below 0.5 = risky.*  

    **Debt to Equity Ratio:** {debt_to_equity}  
    *Below 1.0 = conservative financing, 1.0-2.0 = moderate risk, above 2.0 = highly leveraged.*  

    **Return on Equity (ROE):** {roe_display}  
    *Above 15% = strong, 10-15% = average, below 10% = weak.*  
    """)

    # P/E Ratio Comparison
    st.subheader("📈 P/E Ratio Comparison")
    col1, col2 = st.columns(2)
    col1.metric(f"{ticker} P/E", pe_ratio)
    col2.metric(f"{stock_sector} Sector P/E", sector_pe)

    # Interpretation of P/E Comparison
    if isinstance(pe_ratio, (int, float)) and isinstance(sector_pe, (int, float)):
        if pe_ratio > sector_pe:
            st.success(f"{ticker} has a higher P/E than its sector average. It may be overvalued.")
        else:
            st.info(f"{ticker} has a lower P/E than its sector average. It may be undervalued.")
    else:
        st.warning(f"⚠️ Sector P/E ratio for {stock_sector} not found. Check sector name matching above.")

