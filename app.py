import streamlit as st
import requests
from datetime import datetime

API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")

# 📌 Function to Fetch Growth Metrics
def get_growth_metrics(ticker):
    url = f"{BASE_URL}/key-metrics/{ticker}?limit=1&apikey={API_KEY}"
    response = requests.get(url)
    return response.json()[0] if response.status_code == 200 else None

# 📌 Growth Screener Benchmarks
GROWTH_GUIDANCE = {
    "revenueGrowth": ("Revenue Growth (YoY)", "Above 20% = strong, 10-20% = average, below 10% = weak."),
    "priceToSalesRatio": ("Price-to-Sales (P/S) Ratio", "Lower is better, but high P/S may be justified by strong growth."),
    "enterpriseValueOverRevenue": ("EV/Revenue", "Used to value high-growth companies; compare to sector."),
    "grossProfitMargin": ("Gross Margin (%)", "Above 50% = strong pricing power and scalability."),
    "freeCashFlowPerShare": ("Free Cash Flow Per Share", "A positive and growing FCF is ideal for long-term sustainability."),
}

# 📌 Streamlit Navigation Menu
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Choose a Screener", ["Valuation Dashboard", "Growth Stock Screener"])

# ===========================================
# 📌 STOCK VALUATION DASHBOARD (Your Original Code)
# ===========================================
if page == "Valuation Dashboard":
    st.title("📈 Stock Valuation Dashboard")

    ticker = st.text_input("Enter stock ticker:").upper()

    if st.button("Analyze") and ticker:
        url = f"{BASE_URL}/discounted-cash-flow/{ticker}?apikey={API_KEY}"
        dcf_data = requests.get(url).json()[0]

        url = f"{BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={API_KEY}"
        ratios_data = requests.get(url).json()[0]

        if dcf_data and ratios_data:
            st.subheader(f"Valuation Metrics for {ticker}")
            col1, col2 = st.columns(2)
            col1.metric("💰 DCF Valuation", f"${dcf_data['dcf']:.2f}")
            col2.metric("📊 Stock Price", f"${dcf_data['Stock Price']:.2f}")

            st.subheader("📊 Key Financial Ratios")
            for key, (title, guidance) in {
                "priceEarningsRatio": ("Price-to-Earnings (P/E) Ratio", "Below 15 = undervalued, above 25 = overvalued."),
                "currentRatio": ("Current Ratio", "Above 1.5 = strong liquidity."),
                "quickRatio": ("Quick Ratio", "Above 1.0 = strong liquidity."),
                "debtEquityRatio": ("Debt to Equity Ratio", "Below 1.0 = conservative financing."),
                "returnOnEquity": ("Return on Equity (ROE)", "Above 15% = strong."),
            }.items():
                if key in ratios_data:
                    value = f"{ratios_data[key]:.2f}"
                    st.markdown(f"**{title}:** {value}  \n*{guidance}*")

        else:
            st.error("Could not fetch data for the given ticker.")

# ===========================================
# 📌 GROWTH STOCK SCREENER (New Separate Page)
# ===========================================
elif page == "Growth Stock Screener":
    st.title("🚀 Growth Stock Screener")

    ticker = st.text_input("Enter stock ticker for growth analysis:").upper()

    if st.button("Analyze Growth") and ticker:
        growth_data = get_growth_metrics(ticker)

        if growth_data:
            st.subheader(f"📈 Growth Metrics for {ticker}")

            for key, (title, guidance) in GROWTH_GUIDANCE.items():
                if key in growth_data:
                    value = growth_data[key]
                    if "Margin" in title or "Growth" in title:
                        value = f"{value * 100:.2f}%"  # Convert to percentage
                    else:
                        value = f"{value:.2f}"
                    st.markdown(f"**{title}:** {value}  \n*{guidance}*")

        else:
            st.error("❌ Growth metrics not available for this stock.")

