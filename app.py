import streamlit as st
import requests
import pandas as pd

# Load API key from Streamlit secrets
API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"

# Mapping to ensure sector names match between APIs
SECTOR_MAPPING = {
    "Financial Services": "Financials",
    "Health Care": "Healthcare",
    "Technology": "Technology",
    "Consumer Cyclical": "Consumer Cyclical",
    "Consumer Defensive": "Consumer Defensive",
    "Industrials": "Industrials",
    "Basic Materials": "Basic Materials",
    "Energy": "Energy",
    "Utilities": "Utilities",
    "Real Estate": "Real Estate",
    "Communication Services": "Communication Services"
}

# Function to fetch DCF valuation
def get_dcf(ticker):
    url = f"{BASE_URL}/discounted-cash-flow/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data and isinstance(data, list) and len(data) > 0:
        return data[0]
    return None

# Function to fetch financial ratios
def get_ratios(ticker):
    url = f"{BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data and isinstance(data, list) and len(data) > 0:
        return data[0]
    return None

# Function to fetch company profile (sector info)
def get_company_sector(ticker):
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data and isinstance(data, list) and len(data) > 0:
        sector = data[0].get("sector", "").strip()
        mapped_sector = SECTOR_MAPPING.get(sector, sector)  # Map sector correctly
        return mapped_sector
    return "Unknown"

# Function to fetch ALL sector P/E ratios at once
def get_sector_pe():
    url = f"https://financialmodelingprep.com/api/v4/sector_price_earning_ratio?date=latest&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data and isinstance(data, list):
        return {item["sector"].strip(): float(item["pe"]) for item in data}  # Store all P/E ratios in a dict
    return {}

# Streamlit UI
st.title("Stock Valuation Dashboard")

# User input for stock ticker
ticker = st.text_input("Enter stock ticker:").upper()

# "Analyze" button to prevent auto-loading data
if st.button("Analyze"):
    if ticker:
        # Fetch the correct sector
        sector = get_company_sector(ticker)

        # Fetch data
        dcf_data = get_dcf(ticker)
        ratios_data = get_ratios(ticker)
        sector_pe_data = get_sector_pe()  # Fetch all sector P/E ratios

        if dcf_data and ratios_data:
            st.subheader(f"Valuation Metrics for {ticker}")

            # Display DCF Valuation
            col1, col2 = st.columns(2)
            with col1:
                st.metric("DCF Valuation", f"${dcf_data['dcf']:.2f}")
            with col2:
                st.metric("Stock Price", f"${dcf_data['Stock Price']:.2f}")

            # Display financial ratios
            st.subheader("Key Financial Ratios")
            stock_pe = ratios_data.get("priceEarningsRatio")
            st.write(f"**P/E Ratio**: {stock_pe}")
            st.write(f"**Current Ratio**: {ratios_data.get('currentRatio', 'N/A')}")
            st.write(f"**Quick Ratio**: {ratios_data.get('quickRatio', 'N/A')}")
            st.write(f"**Debt to Equity**: {ratios_data.get('debtEquityRatio', 'N/A')}")
            st.write(f"**Return on Equity (ROE)**: {ratios_data.get('returnOnEquity', 'N/A')}")

            # Get the sector P/E
            sector_pe = sector_pe_data.get(sector)

            if sector_pe:
                st.subheader("P/E Ratio Comparison")
                col3, col4 = st.columns(2)
                with col3:
                    st.metric(f"{ticker} P/E", f"{stock_pe:.2f}")
                with col4:
                    st.metric(f"{sector} Sector P/E", f"{sector_pe:.2f}")

                if stock_pe > sector_pe:
                    st.warning(f"{ticker} has a higher P/E than its sector average. It may be overvalued.")
                else:
                    st.success(f"{ticker} has a lower P/E than its sector average. It may be undervalued.")
            else:
                st.error(f"Sector P/E ratio for **{sector}** not available for comparison.")
        else:
            st.error("Could not fetch data for the given ticker. Please check and try again.")
