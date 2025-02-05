import streamlit as st
import requests
from datetime import datetime

# Load API key from Streamlit secrets
API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"

# Get today's date dynamically
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")

# Function to fetch DCF valuation
def get_dcf(ticker):
    url = f"{BASE_URL}/discounted-cash-flow/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data[0] if data and isinstance(data, list) else None

# Function to fetch financial ratios
def get_ratios(ticker):
    url = f"{BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data[0] if data and isinstance(data, list) else None

# Function to fetch company profile (sector info)
def get_company_sector(ticker):
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data[0].get("sector", "").strip() if data and isinstance(data, list) else "Unknown"

# Function to fetch ALL sector P/E ratios using today's date
@st.cache_data(ttl=0)
def get_sector_pe(date=TODAY_DATE):
    url = f"https://financialmodelingprep.com/api/v4/sector_price_earning_ratio?date={date}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return {item["sector"].strip(): float(item["pe"]) for item in data} if data and isinstance(data, list) else {}

# Updated explanations with interpretation guidance
RATIO_EXPLANATIONS = {
    "priceEarningsRatio": ("Price-to-Earnings (P/E) Ratio", "Indicates how much investors are willing to pay per dollar of earnings. "
                           "A higher P/E suggests growth expectations, while a lower P/E may indicate undervaluation."),
    "currentRatio": ("Current Ratio", "Measures a company's ability to pay short-term obligations. "
                     "A ratio above 1 suggests good short-term financial health, while below 1 may indicate liquidity issues."),
    "quickRatio": ("Quick Ratio", "Assesses liquidity by excluding inventory. A ratio above 1 means a company can meet short-term liabilities "
                   "without selling inventory, a lower ratio may signal cash flow concerns."),
    "debtEquityRatio": ("Debt to Equity Ratio", "Compares total liabilities to shareholder equity. "
                       "A high ratio indicates reliance on debt financing, while a lower ratio suggests financial stability."),
    "returnOnEquity": ("Return on Equity (ROE)", "Shows how efficiently a company generates profits from shareholders' equity. "
                      "Higher ROE is preferred, indicating strong profitability and efficient use of capital.")
}

# Streamlit UI
st.title("📈 Stock Valuation Dashboard")

# User input for stock ticker
ticker = st.text_input("Enter stock ticker:").upper()

# "Analyze" button to trigger calculations
if st.button("Analyze") and ticker:
    sector = get_company_sector(ticker)
    dcf_data = get_dcf(ticker)
    ratios_data = get_ratios(ticker)
    sector_pe_data = get_sector_pe()

    if dcf_data and ratios_data:
        st.subheader(f"Valuation Metrics for {ticker}")

        # Display DCF Valuation
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 DCF Valuation", f"${dcf_data['dcf']:.2f}")
        with col2:
            st.metric("📊 Stock Price", f"${dcf_data['Stock Price']:.2f}")

        # Display financial ratios with explanations
        st.subheader("📊 Key Financial Ratios")
        for key, (title, explanation) in RATIO_EXPLANATIONS.items():
            if key in ratios_data:
                value = ratios_data[key]
                if key == "returnOnEquity":
                    value = f"{value * 100:.2f}%"  # Convert to percentage
                else:
                    value = f"{value:.2f}"
                st.markdown(f"**{title}:** {value}  \n*{explanation}*")

        # Get sector P/E and compare
        sector_pe = sector_pe_data.get(sector)
        stock_pe = ratios_data.get("priceEarningsRatio")

        if sector_pe:
            st.subheader("📊 P/E Ratio Comparison")
            col3, col4 = st.columns(2)
            with col3:
                st.metric(f"{ticker} P/E", f"{stock_pe:.2f}")
            with col4:
                st.metric(f"{sector} Sector P/E", f"{sector_pe:.2f}")

            if stock_pe > sector_pe:
                st.warning(f"⚠️ {ticker} has a higher P/E than its sector average. It may be overvalued.")
            else:
                st.success(f"✅ {ticker} has a lower P/E than its sector average. It may be undervalued.")
        else:
            st.error(f"Sector P/E ratio for **{sector}** not available for comparison.")
    else:
        st.error("Could not fetch data for the given ticker. Please check and try again.")
