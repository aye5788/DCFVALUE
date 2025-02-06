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

# New function: Get Sector P/E for a given sector (using case-insensitive matching)
@st.cache_data(ttl=0)
def get_sector_pe_for(sector, date=TODAY_DATE):
    """
    Fetch the P/E ratio for a specific sector for the given date.
    The endpoint returns data for all sectors; we return the one matching the given sector (case-insensitive).
    """
    url = f"https://financialmodelingprep.com/api/v4/sector_price_earning_ratio?date={date}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            for item in data:
                # Use case-insensitive comparison
                if item.get("sector", "").strip().lower() == sector.lower():
                    try:
                        return float(item["pe"])
                    except (TypeError, ValueError):
                        return None
    return None

# Additional endpoints for computing growth metrics:
def get_income_statement(ticker, limit=3):
    url = f"{BASE_URL}/income-statement/{ticker}?limit={limit}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list):
            return data
    return None

def get_cash_flow_statement(ticker, limit=3):
    url = f"{BASE_URL}/cash-flow-statement/{ticker}?limit={limit}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list):
            return data
    return None

# -----------------------------------------------------------------------------
# Helper Functions to Compute Growth Metrics (Updated)
# -----------------------------------------------------------------------------
def compute_revenue_growth(income_data):
    """
    Compute YoY revenue growth using the first two valid (nonzero) revenue values.
    Note: The income statement returns revenue under the key 'revenue'.
    """
    if income_data:
        valid_revenues = []
        for period in income_data:
            rev = period.get("revenue", None)
            try:
                rev_val = float(rev)
            except (TypeError, ValueError):
                rev_val = 0
            if rev_val > 0:
                valid_revenues.append(rev_val)
            if len(valid_revenues) >= 2:
                break
        if len(valid_revenues) >= 2:
            latest = valid_revenues[0]
            previous = valid_revenues[1]
            return ((latest - previous) / previous) * 100
    return None

def compute_gross_profit_margin(income_data):
    """
    Compute the gross profit margin (%) from the latest income statement data.
    Uses the keys 'revenue' and 'grossProfit'.
    """
    if income_data and len(income_data) > 0:
        latest = income_data[0]
        try:
            revenue_val = float(latest.get("revenue", 0))
            gross_profit = float(latest.get("grossProfit", 0))
        except (TypeError, ValueError):
            return None
        if revenue_val > 0:
            return (gross_profit / revenue_val) * 100
    return None

def compute_operating_cf_growth(cash_flow_data):
    """
    Compute YoY operating cash flow growth using the first two valid operatingCashFlow values.
    """
    if cash_flow_data:
        valid_cf = []
        for period in cash_flow_data:
            cf = period.get("operatingCashFlow", None)
            try:
                cf_val = float(cf)
            except (TypeError, ValueError):
                cf_val = 0
            if cf_val > 0:
                valid_cf.append(cf_val)
            if len(valid_cf) >= 2:
                break
        if len(valid_cf) >= 2:
            return ((valid_cf[0] - valid_cf[1]) / valid_cf[1]) * 100
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
    "operatingCFGrowth": ("Operating Cash Flow Growth", "Consistent growth indicates strong business fundamentals.")
}

# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Choose a Screener", ["Valuation Dashboard", "Growth Stock Screener"])

# -----------------------------------------------------------------------------
# Valuation Dashboard (Unchanged, with Sector P/E Comparison restored)
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
            
            # Sector P/E comparison:
            if sector:
                sector_pe = get_sector_pe_for(sector)
                stock_pe = ratios_data.get("priceEarningsRatio", None)
                if sector_pe is not None and stock_pe is not None:
                    st.subheader("📊 P/E Ratio Comparison")
                    col3, col4 = st.columns(2)
                    col3.metric(f"{ticker} P/E", f"{float(stock_pe):.2f}")
                    col4.metric(f"{sector} Sector P/E", f"{float(sector_pe):.2f}")
                    if float(stock_pe) > float(sector_pe):
                        st.warning(f"⚠️ {ticker} has a higher P/E than its sector ({sector}). It may be overvalued.")
                    else:
                        st.success(f"✅ {ticker} has a lower P/E than its sector ({sector}). It may be undervalued.")
                else:
                    st.error(f"Sector P/E ratio for {sector} is not available.")
            else:
                st.error("Sector information is not available for this ticker.")

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
        
        # Fetch historical income statement and cash flow data (using up to 3 periods)
        income_data = get_income_statement(ticker, limit=3)
        cash_flow_data = get_cash_flow_statement(ticker, limit=3)
        
        # Compute the missing growth metrics
        revenue_growth = compute_revenue_growth(income_data)
        gross_profit_margin = compute_gross_profit_margin(income_data)
        operating_cf_growth = compute_operating_cf_growth(cash_flow_data)
        
        # Use evToSales from the ratios endpoint as EV/Revenue (alias)
        ev_revenue = ratios_data.get("evToSales") if ratios_data else None
        ev_revenue_display = f"{float(ev_revenue):.2f}" if ev_revenue not in [None, "N/A"] else "N/A"
        
        # Build a dictionary of metrics to display only if available
        metrics = {}
        if revenue_growth is not None:
            metrics["Revenue Growth (YoY)"] = f"{revenue_growth:.2f}%"
        if ratios_data and ratios_data.get("priceToSalesRatio"):
            metrics["Price-to-Sales (P/S) Ratio"] = f"{float(ratios_data.get('priceToSalesRatio')):.2f}"
        if ev_revenue_display != "N/A":
            metrics["EV/Revenue"] = ev_revenue_display
        if gross_profit_margin is not None:
            metrics["Gross Margin (%)"] = f"{gross_profit_margin:.2f}"
        if ratios_data and ratios_data.get("freeCashFlowPerShare"):
            metrics["Free Cash Flow Per Share"] = f"{float(ratios_data.get('freeCashFlowPerShare')):.2f}"
        if operating_cf_growth is not None:
            metrics["Operating Cash Flow Growth"] = f"{operating_cf_growth:.2f}%"
        
        # Guidance text for each metric
        guidance_text = {
            "Revenue Growth (YoY)": "Above 20% = strong, 10-20% = average, below 10% = weak.",
            "Price-to-Sales (P/S) Ratio": "Lower is better, but high P/S may be justified by strong growth.",
            "EV/Revenue": "Used to value high-growth companies; compare to sector.",
            "Gross Margin (%)": "Above 50% = strong pricing power and scalability.",
            "Free Cash Flow Per Share": "A positive and growing FCF is ideal for long-term sustainability.",
            "Operating Cash Flow Growth": "Consistent growth indicates strong business fundamentals."
        }
        
        for label, value in metrics.items():
            st.markdown(f"**{label}:** {value}  \n*{guidance_text.get(label, '')}*")

