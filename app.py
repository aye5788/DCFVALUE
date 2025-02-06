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
# Data Fetching Functions (FMP Endpoints)
# -----------------------------------------------------------------------------
def get_dcf(ticker):
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
    url = f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("sector", "").strip()
        elif isinstance(data, dict) and data:
            return data.get("sector", "").strip()
    return None

# Additional endpoints for computing growth metrics:
def get_income_statement(ticker, limit=2):
    url = f"{BASE_URL}/income-statement/{ticker}?limit={limit}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list):
            return data
    return None

def get_cash_flow_statement(ticker, limit=2):
    url = f"{BASE_URL}/cash-flow-statement/{ticker}?limit={limit}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list):
            return data
    return None

# -----------------------------------------------------------------------------
# Helper Functions to Compute Growth Metrics
# -----------------------------------------------------------------------------
def compute_revenue_growth(income_data):
    if income_data and len(income_data) >= 2:
        latest_revenue = float(income_data[0].get("totalRevenue", 0))
        previous_revenue = float(income_data[1].get("totalRevenue", 0))
        if previous_revenue > 0:
            return ((latest_revenue - previous_revenue) / previous_revenue) * 100
    return None

def compute_gross_profit_margin(income_data):
    if income_data and len(income_data) > 0:
        latest = income_data[0]
        total_revenue = float(latest.get("totalRevenue", 0))
        gross_profit = float(latest.get("grossProfit", 0))
        if total_revenue > 0:
            return (gross_profit / total_revenue) * 100
    return None

def compute_operating_cf_growth(cash_flow_data):
    if cash_flow_data and len(cash_flow_data) >= 2:
        latest_cf = float(cash_flow_data[0].get("operatingCashFlow", 0))
        previous_cf = float(cash_flow_data[1].get("operatingCashFlow", 0))
        if previous_cf > 0:
            return ((latest_cf - previous_cf) / previous_cf) * 100
    return None

# -----------------------------------------------------------------------------
# Guidance Dictionaries for Display
# -----------------------------------------------------------------------------
RATIO_GUIDANCE = {
    "priceEarningsRatio": ("Price-to-Earnings (P/E) Ratio", "Higher P/E suggests strong growth expectations. Below 15 = undervalued, 15-25 = fairly valued, above 25 = overvalued."),
    "currentRatio": ("Current Ratio", "Above 1.5 = strong liquidity, 1.0-1.5 = adequate, below 1 = potential liquidity issues."),
    "quickRatio": ("Quick Ratio", "Above 1.0 = strong liquidity, 0.5-1.0 = acceptable, below 0.5 = risky."),
    "debtEquityRatio": ("Debt to Equity Ratio", "Below 1.0 = conservative financing, 1.0-2.0 = moderate risk, above 2.0 = highly leveraged."),
    "returnOnEquity": ("Return on Equity (ROE)", "Above 15% = strong, 10-15% = average, below 10% = weak."),
}

GROWTH_GUIDANCE = {
    "revenueGrowth": ("Revenue Growth (YoY)", "Above 20% = strong, 10-20% = average, below 10% = weak."),
    "priceToSalesRatio": ("Price-to-Sales (P/S) Ratio", "Lower is better, but high P/S may be justified by strong growth."),
    "evToSales": ("EV/Revenue", "Used to value high-growth companies; compare to sector."),
    "grossProfitMargin": ("Gross Margin (%)", "Above 50% = strong pricing power and scalability."),
    "freeCashFlowPerShare": ("Free Cash Flow Per Share", "A positive and growing FCF is ideal for long-term sustainability."),
    "operatingCFGrowth": ("Operating Cash Flow Growth", "Consistent growth indicates strong business fundamentals."),
    "enterpriseValueOverEBITDA": ("EV/EBITDA", "Enterprise Value over EBITDA; lower values indicate undervaluation."),
    "evToOperatingCashFlow": ("EV/Operating Cash Flow", "Measures how expensive a company is relative to cash flow."),
    "freeCashFlowYield": ("Free Cash Flow Yield", "Higher values indicate strong free cash flow compared to market cap."),
}

# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Choose a Screener", ["Valuation Dashboard", "Growth Stock Screener"])

# -----------------------------------------------------------------------------
# Valuation Dashboard (Unchanged)
# -----------------------------------------------------------------------------
if page == "Valuation Dashboard":
    st.title("📈 Stock Valuation Dashboard")
    ticker = st.text_input("Enter stock ticker:").upper()

    if st.button("Analyze") and ticker:
        sector = get_company_sector(ticker)
        dcf_data = get_dcf(ticker)
        ratios_data = get_ratios(ticker)

        if not dcf_data or not ratios_data:
            st.error(f"Could not retrieve all required data for ticker {ticker}. Please verify the ticker symbol or try again later.")
        else:
            st.subheader(f"Valuation Metrics for {ticker}")
            col1, col2 = st.columns(2)
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

            stock_pe = ratios_data.get("priceEarningsRatio")
            if stock_pe is not None:
                st.subheader("📊 P/E Ratio")
                st.metric(f"{ticker} P/E", f"{float(stock_pe):.2f}")
            else:
                st.error(f"P/E Ratio data not available for {ticker}.")

# -----------------------------------------------------------------------------
# Growth Stock Screener (Modified for Growth Metrics)
# -----------------------------------------------------------------------------
elif page == "Growth Stock Screener":
    st.title("🚀 Growth Stock Screener")
    ticker = st.text_input("Enter stock ticker for growth analysis:").upper()

    if st.button("Analyze Growth") and ticker:
        # Fetch ratios from the Key Metrics endpoint
        ratios_url = f"{BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={API_KEY}"
        ratios_response = requests.get(ratios_url)
        ratios_data = None
        if ratios_response.status_code == 200:
            data = ratios_response.json()
            if data and isinstance(data, list) and len(data) > 0:
                ratios_data = data[0]

        # Fetch historical income statement and cash flow data (using 2 periods)
        income_data = get_income_statement(ticker, limit=2)
        cash_flow_data = get_cash_flow_statement(ticker, limit=2)

        # Compute the missing growth metrics
        revenue_growth = compute_revenue_growth(income_data)
        gross_profit_margin = compute_gross_profit_margin(income_data)
        operating_cf_growth = compute_operating_cf_growth(cash_flow_data)

        # Use evToSales from the ratios endpoint as EV/Revenue (alias)
        ev_revenue = ratios_data.get("evToSales") if ratios_data else None

        # Prepare display value for EV/Revenue to avoid TypeError
        ev_revenue_display = f"{float(ev_revenue):.2f}" if ev_revenue not in [None, "N/A"] else "N/A"

        # Display the computed and available metrics:
        st.markdown(f"**Revenue Growth (YoY):** {f'{revenue_growth:.2f}%' if revenue_growth is not None else 'N/A'}  \n*Above 20% = strong, 10-20% = average, below 10% = weak.*")
        st.markdown(f"**Price-to-Sales (P/S) Ratio:** {ratios_data.get('priceToSalesRatio', 'N/A') if ratios_data else 'N/A'}  \n*Lower is better, but high P/S may be justified by strong growth.*")
        st.markdown(f"**EV/Revenue:** {ev_revenue_display}  \n*Used to value high-growth companies; compare to sector.*")
        st.markdown(f"**Gross Margin (%):** {f'{gross_profit_margin:.2f}' if gross_profit_margin is not None else 'N/A'}  \n*Above 50% = strong pricing power and scalability.*")
        st.markdown(f"**Free Cash Flow Per Share:** {ratios_data.get('freeCashFlowPerShare', 'N/A') if ratios_data else 'N/A'}  \n*A positive and growing FCF is ideal for long-term sustainability.*")
        st.markdown(f"**Operating Cash Flow Growth:** {f'{operating_cf_growth:.2f}%' if operating_cf_growth is not None else 'N/A'}  \n*Consistent growth indicates strong business fundamentals.*")
        st.markdown(f"**EV/Sales:** {ratios_data.get('evToSales', 'N/A') if ratios_data else 'N/A'}  \n*Enterprise Value divided by Revenue; lower is better for undervaluation.*")
        st.markdown(f"**EV/EBITDA:** {ratios_data.get('enterpriseValueOverEBITDA', 'N/A') if ratios_data else 'N/A'}  \n*Enterprise Value over EBITDA; lower values indicate undervaluation.*")
        st.markdown(f"**EV/Operating Cash Flow:** {ratios_data.get('evToOperatingCashFlow', 'N/A') if ratios_data else 'N/A'}  \n*Measures how expensive a company is relative to cash flow.*")
        st.markdown(f"**Free Cash Flow Yield:** {ratios_data.get('freeCashFlowYield', 'N/A') if ratios_data else 'N/A'}  \n*Higher values indicate strong free cash flow compared to market cap.*")
