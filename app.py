import streamlit as st
import requests
from datetime import datetime

API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")

# Function to fetch data
def get_dcf(ticker):
    url = f"{BASE_URL}/discounted-cash-flow/{ticker}?apikey={API_KEY}"
    return requests.get(url).json()[0]

def get_ratios(ticker):
    url = f"{BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={API_KEY}"
    return requests.get(url).json()[0]

def get_company_sector(ticker):
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    return requests.get(url).json()[0]["sector"].strip()

@st.cache_data(ttl=0)
def get_sector_pe(date=TODAY_DATE):
    url = f"https://financialmodelingprep.com/api/v4/sector_price_earning_ratio?date={date}&apikey={API_KEY}"
    response = requests.get(url)
    return {item["sector"].strip(): float(item["pe"]) for item in response.json()}

# Ratio explanations WITH benchmarks
RATIO_GUIDANCE = {
    "priceEarningsRatio": ("Price-to-Earnings (P/E) Ratio", 
                           "Higher P/E suggests strong growth expectations. Below 15 = undervalued, 15-25 = fairly valued, above 25 = overvalued."),
    "currentRatio": ("Current Ratio",
                     "Above 1.5 = strong liquidity, 1.0-1.5 = adequate, below 1 = potential liquidity issues."),
    "quickRatio": ("Quick Ratio", 
                   "Above 1.0 = strong liquidity, 0.5-1.0 = acceptable, below 0.5 = risky."),
    "debtEquityRatio": ("Debt to Equity Ratio",
                        "Below 1.0 = conservative financing, 1.0-2.0 = moderate risk, above 2.0 = highly leveraged."),
    "returnOnEquity": ("Return on Equity (ROE)", 
                       "Above 15% = strong, 10-15% = average, below 10% = weak.")
}

# Streamlit UI
st.title("📈 Stock Valuation Dashboard")

ticker = st.text_input("Enter stock ticker:").upper()

if st.button("Analyze") and ticker:
    sector = get_company_sector(ticker)
    dcf_data = get_dcf(ticker)
    ratios_data = get_ratios(ticker)
    sector_pe_data = get_sector_pe()

    st.subheader("📊 Debugging Info (Hidden in Final Deployment)")
    st.write(f"✅ **Stock Sector Identified:** `{sector}`")
    st.write(f"✅ **Available Sectors in P/E API:** `{list(sector_pe_data.keys())}`")

    # Normalize sector names for matching
    normalized_sector = sector.strip().lower()
    available_sectors = {key.strip().lower(): value for key, value in sector_pe_data.items()}
    sector_pe = available_sectors.get(normalized_sector)

    if dcf_data and ratios_data:
        st.subheader(f"Valuation Metrics for {ticker}")

        col1, col2 = st.columns(2)
        col1.metric("💰 DCF Valuation", f"${dcf_data['dcf']:.2f}")
        col2.metric("📊 Stock Price", f"${dcf_data['Stock Price']:.2f}")

        st.subheader("📊 Key Financial Ratios")
        for key, (title, guidance) in RATIO_GUIDANCE.items():
            if key in ratios_data:
                value = ratios_data[key]
                if key == "returnOnEquity":
                    value = f"{value * 100:.2f}%"  # Convert to percentage
                else:
                    value = f"{value:.2f}"
                st.markdown(f"**{title}:** {value}  \n*{guidance}*")

        stock_pe = ratios_data.get("priceEarningsRatio")

        if sector_pe:
            st.subheader("📊 P/E Ratio Comparison")
            col3, col4 = st.columns(2)
            col3.metric(f"{ticker} P/E", f"{stock_pe:.2f}")
            col4.metric(f"{sector} Sector P/E", f"{sector_pe:.2f}")

            if stock_pe > sector_pe:
                st.warning(f"⚠️ {ticker} has a higher P/E than its sector. It may be overvalued.")
            else:
                st.success(f"✅ {ticker} has a lower P/E than its sector. It may be undervalued.")
        else:
            st.error(f"⚠️ **Sector P/E not found for {sector}!** Check sector name matching above.")
    else:
        st.error("Could not fetch data for the given ticker.")

