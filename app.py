import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import altair as alt

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
FMP_API_KEY = st.secrets["fmp"]["api_key"]
AV_API_KEY = st.secrets["av"]["api_key"]

FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

# -----------------------------------------------------------------------------
# FMP Data Fetching Functions
# -----------------------------------------------------------------------------
def get_dcf(ticker):
    url = f"{FMP_BASE_URL}/discounted-cash-flow/{ticker}?apikey={FMP_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        elif isinstance(data, dict) and data:
            return data
    return None

def get_ratios(ticker):
    url = f"{FMP_BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={FMP_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        elif isinstance(data, dict) and data:
            return data
    return None

def get_company_sector(ticker):
    url = f"{FMP_BASE_URL}/profile/{ticker}?apikey={FMP_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("sector", "").strip()
        elif isinstance(data, dict) and data:
            return data.get("sector", "").strip()
    return None

def get_income_statement_fmp(ticker, limit=3):
    url = f"{FMP_BASE_URL}/income-statement/{ticker}?limit={limit}&apikey={FMP_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list):
            return data
    return None

def get_cash_flow_statement_fmp(ticker, limit=3):
    url = f"{FMP_BASE_URL}/cash-flow-statement/{ticker}?limit={limit}&apikey={FMP_API_KEY}"
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
    """
    Compute YoY revenue growth using the first two valid (nonzero) revenue values.
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
    "priceEarningsRatio": ("Price-to-Earnings (P/E) Ratio", 
                           "Higher P/E suggests strong growth expectations. Below 15 = undervalued, 15-25 = fairly valued, above 25 = overvalued."),
    "currentRatio": ("Current Ratio", 
                     "Above 1.5 = strong liquidity, 1.0-1.5 = adequate, below 1 = potential liquidity issues."),
    "quickRatio": ("Quick Ratio", 
                   "Above 1.0 = strong liquidity, 0.5-1.0 = acceptable, below 0.5 = risky."),
    "debtEquityRatio": ("Debt to Equity Ratio", 
                        "Below 1.0 = conservative financing, 1.0-2.0 = moderate risk, above 2.0 = highly leveraged."),
    "returnOnEquity": ("Return on Equity (ROE)", 
                       "Above 15% = strong, 10-15% = average, below 10% = weak."),
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
# Alpha Vantage Integration
# -----------------------------------------------------------------------------
def fetch_income_statement_av(symbol: str, api_key: str) -> dict:
    """
    Fetch annual income statement data from Alpha Vantage.
    """
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "INCOME_STATEMENT",
        "symbol": symbol,
        "apikey": api_key
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    return {}

def fetch_balance_sheet_av(symbol: str, api_key: str) -> dict:
    """
    Fetch annual balance sheet data from Alpha Vantage.
    """
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "BALANCE_SHEET",
        "symbol": symbol,
        "apikey": api_key
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    return {}

def fetch_cash_flow_av(symbol: str, api_key: str) -> dict:
    """
    Fetch annual cash flow data from Alpha Vantage.
    """
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "CASH_FLOW",
        "symbol": symbol,
        "apikey": api_key
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    return {}

# -----------------------------------------------------------------------------
# Updated Plot Functions
# -----------------------------------------------------------------------------
def plot_annual_bars(df: pd.DataFrame, metric_col: str, title: str, scale=1e9):
    """
    Plots an Altair bar chart of the given metric over time, scaling large values
    to billions by default (scale=1e9).

    Args:
        df (pd.DataFrame): Must contain columns ["fiscalDateEnding", metric_col].
        metric_col (str): The column name for the numeric metric to plot.
        title (str): The descriptive title of the metric (e.g., "Total Revenue").
        scale (float): Factor to divide the raw numbers by (1e9 for billions, 1e6 for millions, etc.).
    """
    df["Year"] = df["fiscalDateEnding"].str[:4]

    # Convert to numeric and scale
    df[metric_col] = pd.to_numeric(df[metric_col], errors="coerce") / scale

    # Drop NaNs and sort
    df = df.dropna(subset=[metric_col])
    df = df.sort_values("Year")

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Year:N", sort=None),
            y=alt.Y(
                f"{metric_col}:Q",
                title=f"{title} (Billions USD)",
                axis=alt.Axis(format=",.2f")
            ),
            tooltip=[
                alt.Tooltip("Year:N", title="Year"),
                alt.Tooltip(
                    f"{metric_col}:Q",
                    title=f"{title} (Billions USD)",
                    format=",.2f"
                ),
            ],
        )
        .properties(width=500, height=300, title=title)
    )
    st.altair_chart(chart, use_container_width=True)

def plot_assets_vs_liabilities(bal_df: pd.DataFrame):
    """
    Overlays a bar chart for Liabilities and a yellow line chart for Assets
    so you can see whether Assets exceed Liabilities each year.
    Values are scaled to billions.
    """
    bal_df["Year"] = bal_df["fiscalDateEnding"].str[:4]
    
    # Convert to numeric and scale to billions
    bal_df["totalAssets"] = pd.to_numeric(bal_df["totalAssets"], errors="coerce") / 1e9
    bal_df["totalLiabilities"] = pd.to_numeric(bal_df["totalLiabilities"], errors="coerce") / 1e9
    
    # Drop rows where either is NaN
    bal_df = bal_df.dropna(subset=["totalAssets", "totalLiabilities"])
    bal_df = bal_df.sort_values("Year")

    # Bars for Liabilities
    bars = alt.Chart(bal_df).mark_bar(color="#1f77b4").encode(
        x=alt.X("Year:N", sort=None),
        y=alt.Y(
            "totalLiabilities:Q",
            title="(Billions USD)",
            axis=alt.Axis(format=",.2f")
        ),
        tooltip=[
            alt.Tooltip("Year:N", title="Year"),
            alt.Tooltip("totalLiabilities:Q", title="Liabilities (Billions USD)", format=",.2f"),
            alt.Tooltip("totalAssets:Q", title="Assets (Billions USD)", format=",.2f"),
        ]
    )

    # Yellow line for Assets
    line = alt.Chart(bal_df).mark_line(color="yellow", strokeWidth=3).encode(
        x="Year:N",
        y="totalAssets:Q"
    )

    # Layer them together on the same y-scale
    chart = alt.layer(bars, line).properties(
        width=500,
        height=300,
        title="Liabilities (Bars) vs. Assets (Line)"
    )
    
    st.altair_chart(chart, use_container_width=True)

# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Choose a Screener", ["Valuation Dashboard", "Growth Stock Screener"])

# -----------------------------------------------------------------------------
# Valuation Dashboard (No Sector P/E)
# -----------------------------------------------------------------------------
if page == "Valuation Dashboard":
    st.title("📈 Stock Valuation Dashboard")
    ticker = st.text_input("Enter stock ticker:").upper()
    
    if st.button("Analyze") and ticker:
        # -----------------------------
        # FMP: DCF & Ratios
        # -----------------------------
        dcf_data = get_dcf(ticker)
        ratios_data = get_ratios(ticker)
        
        if not dcf_data and not ratios_data:
            st.error(f"Could not retrieve any required data for ticker {ticker}. "
                     "Please verify the ticker symbol or try again later.")
        else:
            st.subheader(f"Valuation Metrics for {ticker}")
            col1, col2 = st.columns(2)
            if dcf_data:
                col1.metric("💰 DCF Valuation", f"${float(dcf_data.get('dcf', 0)):.2f}")
                col2.metric("📊 Stock Price", f"${float(dcf_data.get('Stock Price', 0)):.2f}")
            else:
                st.warning("DCF data not available.")
            
            if ratios_data:
                st.subheader("📊 Key Financial Ratios")
                for key, (title, guidance) in RATIO_GUIDANCE.items():
                    if key in ratios_data:
                        try:
                            value = float(ratios_data[key])
                            st.markdown(f"**{title}:** {value:.2f}  \n*{guidance}*")
                        except Exception:
                            st.markdown(f"**{title}:** {ratios_data[key]}  \n*{guidance}*")
            else:
                st.warning("Ratios data not available.")

            # -----------------------------
            # Alpha Vantage: Annual Trends
            # -----------------------------
            st.subheader("🔎 Annual Trends (via Alpha Vantage)")
            av_income = fetch_income_statement_av(ticker, AV_API_KEY)
            av_balance = fetch_balance_sheet_av(ticker, AV_API_KEY)
            av_cashfl = fetch_cash_flow_av(ticker, AV_API_KEY)
            
            # Income Statement Bar Charts
            income_reports = av_income.get("annualReports", [])
            if income_reports:
                st.markdown("**Income Statement**")
                inc_df = pd.DataFrame(income_reports)
                
                # Plot totalRevenue & netIncome
                if "totalRevenue" in inc_df.columns:
                    plot_annual_bars(
                        inc_df[["fiscalDateEnding","totalRevenue"]].copy(),
                        "totalRevenue",
                        "Total Revenue"
                    )
                if "netIncome" in inc_df.columns:
                    plot_annual_bars(
                        inc_df[["fiscalDateEnding","netIncome"]].copy(),
                        "netIncome",
                        "Net Income"
                    )
            else:
                st.info("No annual income statement data from Alpha Vantage.")

            # Balance Sheet: Overlay Liabilities (bars) & Assets (line)
            balance_reports = av_balance.get("annualReports", [])
            if balance_reports:
                st.markdown("**Balance Sheet**")
                bal_df = pd.DataFrame(balance_reports)
                
                # If both columns exist, overlay them
                if "totalAssets" in bal_df.columns and "totalLiabilities" in bal_df.columns:
                    plot_assets_vs_liabilities(
                        bal_df[["fiscalDateEnding","totalAssets","totalLiabilities"]].copy()
                    )
                else:
                    st.info("Missing 'totalAssets' or 'totalLiabilities' data for overlay chart.")
            else:
                st.info("No annual balance sheet data from Alpha Vantage.")

            # Cash Flow Statement Bar Charts
            cashflow_reports = av_cashfl.get("annualReports", [])
            if cashflow_reports:
                st.markdown("**Cash Flow Statement**")
                cf_df = pd.DataFrame(cashflow_reports)
                
                # Operating Cash Flow
                if "operatingCashflow" in cf_df.columns:
                    plot_annual_bars(
                        cf_df[["fiscalDateEnding","operatingCashflow"]].copy(),
                        "operatingCashflow",
                        "Operating Cash Flow"
                    )
                # Capital Expenditures
                if "capitalExpenditures" in cf_df.columns:
                    plot_annual_bars(
                        cf_df[["fiscalDateEnding","capitalExpenditures"]].copy(),
                        "capitalExpenditures",
                        "Capital Expenditures"
                    )
            else:
                st.info("No annual cash flow data from Alpha Vantage.")

# -----------------------------------------------------------------------------
# Growth Stock Screener
# -----------------------------------------------------------------------------
elif page == "Growth Stock Screener":
    st.title("🚀 Growth Stock Screener")
    ticker = st.text_input("Enter stock ticker for growth analysis:").upper()
    
    if st.button("Analyze Growth") and ticker:
        # Fetch ratios from the Key Metrics endpoint
        ratios_url = f"{FMP_BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={FMP_API_KEY}"
        ratios_response = requests.get(ratios_url)
        ratios_data = None
        if ratios_response.status_code == 200:
            data = ratios_response.json()
            if data and isinstance(data, list) and len(data) > 0:
                ratios_data = data[0]
        
        # Fetch historical income statement and cash flow data (using up to 3 periods) from FMP
        income_data = get_income_statement_fmp(ticker, limit=3)
        cash_flow_data = get_cash_flow_statement_fmp(ticker, limit=3)
        
        # Compute the missing growth metrics
        revenue_growth = compute_revenue_growth(income_data)
        gross_profit_margin = compute_gross_profit_margin(income_data)
        operating_cf_growth = compute_operating_cf_growth(cash_flow_data)
        
        # Use evToSales from the ratios endpoint as EV/Revenue
        ev_revenue = ratios_data.get("evToSales") if ratios_data else None
        ev_revenue_display = f"{float(ev_revenue):.2f}" if ev_revenue not in [None, "N/A"] else "N/A"
        
        # Build a dictionary of metrics to display
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

