import streamlit as st
import requests
from datetime import datetime

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")

# -----------------------------------------------------------------------------
# Data Fetching Functions
# -----------------------------------------------------------------------------
def get_dcf(ticker):
    """
    Fetch discounted cash flow data for the given ticker.
    The API response may be a list or a dictionary.
    """
    url = f"{BASE_URL}/discounted-cash-flow/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        elif isinstance(data, dict) and data:
            return data
    return None

def get_ratios(ticker):
    """Fetch key ratios for the given ticker."""
    url = f"{BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        elif isinstance(data, dict) and data:
            return data
    return None

def get_company_sector(ticker):
    """Fetch the company profile to determine its sector."""
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("sector", "").strip()
        elif isinstance(data, dict) and data:
            return data.get("sector", "").strip()
    return None

@st.cache_data(ttl=0)
def get_sector_pe_for(sector, date=TODAY_DATE):
    """
    Fetch the P/E ratio for a specific sector for the given date.
    The API returns all sectors' data, so we filter out only the one that
    matches the provided sector.
    """
    url = f"https://financialmodelingprep.com/api/v4/sector_price_earning_ratio?date={date}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            for item in data:
                if item.get("sector", "").strip() == sector:
                    return float(item["pe"])
    return None

def get_key_metrics(ticker, years=5):
    """Fetch key metrics for the given ticker over the past `years` years."""
    url = f"{BASE_URL}/key-metrics/{ticker}?limit={years}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data
    return None

def compute_revenue_growth(metrics):
    """Compute Year-over-Year revenue growth from key metrics."""
    if metrics and len(metrics) > 1:
        revenue_latest = metrics[0].get("revenuePerShare")
        revenue_previous = metrics[1].get("revenuePerShare")
        if revenue_latest and revenue_previous:
            return ((revenue_latest - revenue_previous) / revenue_previous) * 100
    return None

# -----------------------------------------------------------------------------
# Guidance Dictionaries
# -----------------------------------------------------------------------------
RATIO_GUIDANCE = {
    "priceEarningsRatio": (
        "Price-to-Earnings (P/E) Ratio",
        "Higher P/E suggests strong growth expectations. Below 15 = undervalued, 15-25 = fairly valued, above 25 = overvalued."
    ),
    "currentRatio": (
        "Current Ratio",
        "Above 1.5 = strong liquidity, 1.0-1.5 = adequate, below 1 = potential liquidity issues."
    ),
    "quickRatio": (
        "Quick Ratio",
        "Above 1.0 = strong liquidity, 0.5-1.0 = acceptable, below 0.5 = risky."
    ),
    "debtEquityRatio": (
        "Debt to Equity Ratio",
        "Below 1.0 = conservative financing, 1.0-2.0 = moderate risk, above 2.0 = highly leveraged."
    ),
    "returnOnEquity": (
        "Return on Equity (ROE)",
        "Above 15% = strong, 10-15% = average, below 10% = weak."
    ),
}

GROWTH_GUIDANCE = {
    "revenueGrowth": (
        "Revenue Growth (YoY)",
        "Above 20% = strong, 10-20% = average, below 10% = weak."
    ),
    "priceToSalesRatio": (
        "Price-to-Sales (P/S) Ratio",
        "Lower is better, but high P/S may be justified by strong growth."
    ),
    "enterpriseValueOverRevenue": (
        "EV/Revenue",
        "Used to value high-growth companies; compare to sector."
    ),
    "grossProfitMargin": (
        "Gross Margin (%)",
        "Above 50% = strong pricing power and scalability."
    ),
    "freeCashFlowPerShare": (
        "Free Cash Flow Per Share",
        "A positive and growing FCF is ideal for long-term sustainability."
    ),
    "operatingCashFlowGrowth": (
        "Operating Cash Flow Growth",
        "Consistent growth indicates strong business fundamentals."
    ),
    "evToSales": (
        "EV/Sales",
        "Enterprise Value divided by Revenue; lower is better for undervaluation."
    ),
    "enterpriseValueOverEBITDA": (
        "EV/EBITDA",
        "Enterprise Value over EBITDA; lower values indicate undervaluation."
    ),
    "evToOperatingCashFlow": (
        "EV/Operating Cash Flow",
        "Measures how expensive a company is relative to cash flow."
    ),
    "freeCashFlowYield": (
        "Free Cash Flow Yield",
        "Higher values indicate strong free cash flow compared to market cap."
    ),
}

# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Choose a Screener", ["Valuation Dashboard", "Growth Stock Screener"])

# -----------------------------------------------------------------------------
# Valuation Dashboard
# -----------------------------------------------------------------------------
if page == "Valuation Dashboard":
    st.title("📈 Stock Valuation Dashboard")
    ticker = st.text_input("Enter stock ticker:").upper()

    if st.button("Analyze") and ticker:
        # Fetch data from the APIs
        sector = get_company_sector(ticker)
        dcf_data = get_dcf(ticker)
        ratios_data = get_ratios(ticker)
        sector_pe = get_sector_pe_for(sector) if sector else None

        # -----------------------------
        # Debug Information (optional)
        # -----------------------------
        st.write("**Debug Info:**")
        st.write("Ticker:", ticker)
        st.write("Sector:", sector)
        st.write("DCF Data:", dcf_data)
        st.write("Ratios Data:", ratios_data)
        st.write(f"{sector} Sector P/E:", sector_pe)

        # Check if we got the required data
        if not dcf_data or not ratios_data:
            st.error(
                f"Could not retrieve all required data for ticker **{ticker}**. "
                "Please verify the ticker symbol or try again later."
            )
        else:
            st.subheader(f"Valuation Metrics for {ticker}")

            col1, col2 = st.columns(2)
            # Adjust the keys if needed; here we assume the keys 'dcf' and 'Stock Price'
            col1.metric("💰 DCF Valuation", f"${float(dcf_data.get('dcf', 0)):.2f}")
            col2.metric("📊 Stock Price", f"${float(dcf_data.get('Stock Price', 0)):.2f}")

            st.subheader("📊 Key Financial Ratios")
            for key, (title, guidance) in RATIO_GUIDANCE.items():
                if key in ratios_data:
                    try:
                        value = float(ratios_data[key])
                        st.markdown(f"**{title}:** {value:.2f}  \n*{guidance}*")
                    except Exception:
                        st.markdown(f"**{title}:** {ratios_data[key]}  \n*{guidance}*")

            # Compare the stock's P/E to its sector's P/E (if available)
            stock_pe = ratios_data.get("priceEarningsRatio", None)
            if sector and sector_pe is not None and stock_pe is not None:
                st.subheader("📊 P/E Ratio Comparison")
                col3, col4 = st.columns(2)
                col3.metric(f"{ticker} P/E", f"{float(stock_pe):.2f}")
                col4.metric(f"{sector} Sector P/E", f"{float(sector_pe):.2f}")

                if float(stock_pe) > float(sector_pe):
                    st.warning(f"⚠️ {ticker} has a higher P/E than its sector. It may be overvalued.")
                else:
                    st.success(f"✅ {ticker} has a lower P/E than its sector. It may be undervalued.")
            else:
                st.error(f"Sector P/E ratio for **{sector}** is not available.")

# -----------------------------------------------------------------------------
# Growth Stock Screener
# -----------------------------------------------------------------------------
elif page == "Growth Stock Screener":
    st.title("🚀 Growth Stock Screener")
    ticker = st.text_input("Enter stock ticker for growth analysis:").upper()

    if st.button("Analyze Growth") and ticker:
        key_metrics = get_key_metrics(ticker)
        revenue_growth = compute_revenue_growth(key_metrics)

        # -----------------------------
        # Debug Information (optional)
        # -----------------------------
        st.write("**Debug Info:**")
        st.write("Ticker:", ticker)
        st.write("Key Metrics:", key_metrics)

        if not key_metrics:
            st.error(
                f"Could not retrieve key metrics for ticker **{ticker}**. "
                "Please verify the ticker symbol or try again later."
            )
        else:
            st.subheader(f"📈 Growth Metrics for {ticker}")

            for key, (title, guidance) in GROWTH_GUIDANCE.items():
                if key == "revenueGrowth":
                    value = f"{revenue_growth:.2f}%" if revenue_growth is not None else "N/A"
                else:
                    value = key_metrics[0].get(key, "N/A")
                st.markdown(f"**{title}:** {value}  \n*{guidance}*")

