import streamlit as st
import requests
from datetime import datetime

API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")

# Function to fetch data
def get_dcf(ticker):
    url = f"{BASE_URL}/discounted-cash-flow/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    return response.json()[0] if response.status_code == 200 and response.json() else None

def get_ratios(ticker):
    url = f"{BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={API_KEY}"
    response = requests.get(url)
    return response.json()[0] if response.status_code == 200 and response.json() else None

def get_company_sector(ticker):
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    return response.json()[0]["sector"].strip() if response.status_code == 200 and response.json() else None

@st.cache_data(ttl=0)
def get_sector_pe(date=TODAY_DATE):
    url = f"https://financialmodelingprep.com/api/v4/sector_price_earning_ratio?date={date}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200 and response.json():
        return {item["sector"].strip(): float(item["pe"]) for item in response.json()}
    return {}

# Function to fetch last 5 years of key metrics
def get_key_metrics(ticker, years=5):
    url = f"{BASE_URL}/key-metrics/{ticker}?limit={years}&apikey={API_KEY}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 and response.json() else None

# Function to compute Revenue Growth (YoY)
def compute_revenue_growth(metrics):
    if metrics and len(metrics) > 1:
        revenue_per_share_latest = metrics[0].get("revenuePerShare")
        revenue_per_share_previous = metrics[1].get("revenuePerShare")

        if revenue_per_share_latest and revenue_per_share_previous:
            return ((revenue_per_share_latest - revenue_per_share_previous) / revenue_per_share_previous) * 100
    return None

# 📌 Ratio explanations WITH benchmarks
RATIO_GUIDANCE = {
    "priceEarningsRatio": ("Price-to-Earnings (P/E) Ratio", "Higher P/E suggests strong growth expectations. Below 15 = undervalued, 15-25 = fairly valued, above 25 = overvalued."),
    "currentRatio": ("Current Ratio", "Above 1.5 = strong liquidity, 1.0-1.5 = adequate, below 1 = potential liquidity issues."),
    "quickRatio": ("Quick Ratio", "Above 1.0 = strong liquidity, 0.5-1.0 = acceptable, below 0.5 = risky."),
    "debtEquityRatio": ("Debt to Equity Ratio", "Below 1.0 = conservative financing, 1.0-2.0 = moderate risk, above 2.0 = highly leveraged."),
    "returnOnEquity": ("Return on Equity (ROE)", "Above 15% = strong, 10-15% = average, below 10% = weak."),
}

# 📌 Growth Screener Benchmarks (Updated)
GROWTH_GUIDANCE = {
    "revenueGrowth": ("Revenue Growth (YoY)", "Above 20% = strong, 10-20% = average, below 10% = weak."),
    "priceToSalesRatio": ("Price-to-Sales (P/S) Ratio", "Lower is better, but high P/S may be justified by strong growth."),
    "enterpriseValueOverRevenue": ("EV/Revenue", "Used to value high-growth companies; compare to sector."),
    "grossProfitMargin": ("Gross Margin (%)", "Above 50% = strong pricing power and scalability."),
    "freeCashFlowPerShare": ("Free Cash Flow Per Share", "A positive and growing FCF is ideal for long-term sustainability."),
    "operatingCashFlowGrowth": ("Operating Cash Flow Growth", "Consistent growth indicates strong business fundamentals."),
    "evToSales": ("EV/Sales", "Enterprise Value divided by Revenue; lower is better for undervaluation."),
    "enterpriseValueOverEBITDA": ("EV/EBITDA", "Enterprise Value over EBITDA; lower values indicate undervaluation."),
    "evToOperatingCashFlow": ("EV/Operating Cash Flow", "Measures how expensive a company is relative to cash flow."),
    "freeCashFlowYield": ("Free Cash Flow Yield", "Higher values indicate strong free cash flow compared to market cap."),
}

# 📌 Sidebar Navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Choose a Screener", ["Valuation Dashboard", "Growth Stock Screener"])

# ===========================================
# 📌 STOCK VALUATION DASHBOARD (RESTORED)
# ===========================================
if page == "Valuation Dashboard":
    st.title("📈 Stock Valuation Dashboard")

    ticker = st.text_input("Enter stock ticker:").upper()

    if st.button("Analyze") and ticker:
        sector = get_company_sector(ticker)
        dcf_data = get_dcf(ticker)
        ratios_data = get_ratios(ticker)
        sector_pe_data = get_sector_pe()

        if dcf_data and ratios_data:
            st.subheader(f"Valuation Metrics for {ticker}")

            col1, col2 = st.columns(2)
            col1.metric("💰 DCF Valuation", f"${dcf_data['dcf']:.2f}")
            col2.metric("📊 Stock Price", f"${dcf_data['Stock Price']:.2f}")

            st.subheader("📊 Key Financial Ratios")
            for key, (title, guidance) in RATIO_GUIDANCE.items():
                if key in ratios_data:
                    value = f"{ratios_data[key]:.2f}"
                    st.markdown(f"**{title}:** {value}  \n*{guidance}*")

            sector_pe = sector_pe_data.get(sector, None)
            stock_pe = ratios_data.get("priceEarningsRatio")

            if sector_pe is not None:
                st.subheader("📊 P/E Ratio Comparison")
                col3, col4 = st.columns(2)
                col3.metric(f"{ticker} P/E", f"{stock_pe:.2f}")
                col4.metric(f"{sector} Sector P/E", f"{sector_pe:.2f}")

                if stock_pe > sector_pe:
                    st.warning(f"⚠️ {ticker} has a higher P/E than its sector. It may be overvalued.")
                else:
                    st.success(f"✅ {ticker} has a lower P/E than its sector. It may be undervalued.")
            else:
                st.error(f"Sector P/E ratio for **{sector}** not available.")

# ===========================================
# 📌 GROWTH STOCK SCREENER (Fixed & Restored)
# ===========================================
elif page == "Growth Stock Screener":
    st.title("🚀 Growth Stock Screener")

    ticker = st.text_input("Enter stock ticker for growth analysis:").upper()

    if st.button("Analyze Growth") and ticker:
        key_metrics = get_key_metrics(ticker)
        revenue_growth = compute_revenue_growth(key_metrics)

        if key_metrics:
            st.subheader(f"📈 Growth Metrics for {ticker}")

            for key, (title, guidance) in GROWTH_GUIDANCE.items():
                value = key_metrics[0].get(key, "N/A")
                if key == "revenueGrowth":
                    value = f"{revenue_growth:.2f}%" if revenue_growth is not None else "N/A"

                st.markdown(f"**{title}:** {value}  \n*{guidance}*")



