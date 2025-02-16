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

# -----------------------------------------------------------------------------
# Alpha Vantage Fetching (Annual Statements)
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
# Valuation Dashboard Chart Helpers (Same as Before)
# -----------------------------------------------------------------------------
def plot_annual_bars(df: pd.DataFrame, metric_col: str, title: str, scale=1e9):
    """
    Plots an Altair bar chart of the given metric over time, scaling large values
    to billions by default (scale=1e9).
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
    """
    bal_df["Year"] = bal_df["fiscalDateEnding"].str[:4]
    
    bal_df["totalAssets"] = pd.to_numeric(bal_df["totalAssets"], errors="coerce") / 1e9
    bal_df["totalLiabilities"] = pd.to_numeric(bal_df["totalLiabilities"], errors="coerce") / 1e9
    
    bal_df = bal_df.dropna(subset=["totalAssets", "totalLiabilities"])
    bal_df = bal_df.sort_values("Year")

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

    line = alt.Chart(bal_df).mark_line(color="yellow", strokeWidth=3).encode(
        x="Year:N",
        y="totalAssets:Q"
    )

    chart = alt.layer(bars, line).properties(
        width=500,
        height=300,
        title="Liabilities (Bars) vs. Assets (Line)"
    )
    
    st.altair_chart(chart, use_container_width=True)

# -----------------------------------------------------------------------------
# Guidance Dictionaries for Display (Unchanged)
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
                
                if "operatingCashflow" in cf_df.columns:
                    plot_annual_bars(
                        cf_df[["fiscalDateEnding","operatingCashflow"]].copy(),
                        "operatingCashflow",
                        "Operating Cash Flow"
                    )
                if "capitalExpenditures" in cf_df.columns:
                    plot_annual_bars(
                        cf_df[["fiscalDateEnding","capitalExpenditures"]].copy(),
                        "capitalExpenditures",
                        "Capital Expenditures"
                    )
            else:
                st.info("No annual cash flow data from Alpha Vantage.")

# -----------------------------------------------------------------------------
# Growth Stock Screener (Using AV for Multi-Year Growth Analysis)
# -----------------------------------------------------------------------------
elif page == "Growth Stock Screener":
    st.title("🚀 Growth Stock Screener")
    ticker = st.text_input("Enter stock ticker for growth analysis:").upper()
    
    if st.button("Analyze Growth") and ticker:
        # ---------------------------------------------------------------------
        # 1. Pull Ratios from FMP (Optional, for extra context)
        # ---------------------------------------------------------------------
        ratios_url = f"{FMP_BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={FMP_API_KEY}"
        ratios_response = requests.get(ratios_url)
        ratios_data = None
        if ratios_response.status_code == 200:
            data = ratios_response.json()
            if data and isinstance(data, list) and len(data) > 0:
                ratios_data = data[0]
        
        st.subheader("Key Growth Ratios (from FMP)")
        if ratios_data:
            p_s = ratios_data.get("priceToSalesRatio")
            ev_sales = ratios_data.get("evToSales")
            fcf_per_share = ratios_data.get("freeCashFlowPerShare")
            
            if p_s not in [None, "N/A"]:
                st.markdown(f"**Price-to-Sales (P/S):** {float(p_s):.2f}")
            if ev_sales not in [None, "N/A"]:
                st.markdown(f"**EV/Revenue:** {float(ev_sales):.2f}")
            if fcf_per_share not in [None, "N/A"]:
                st.markdown(f"**Free Cash Flow Per Share:** {float(fcf_per_share):.2f}")
        else:
            st.info("No ratio data found for this ticker from FMP.")
        
        # ---------------------------------------------------------------------
        # 2. Pull Multi-Year Income Statement & Cash Flow from AV
        # ---------------------------------------------------------------------
        av_income = fetch_income_statement_av(ticker, AV_API_KEY)
        av_cashfl = fetch_cash_flow_av(ticker, AV_API_KEY)
        
        income_reports = av_income.get("annualReports", [])
        cashflow_reports = av_cashfl.get("annualReports", [])
        
        if len(income_reports) < 2 and len(cashflow_reports) < 2:
            st.warning("Not enough annual data from Alpha Vantage to compute multi-year growth.")
        else:
            # -----------------------------------------------------------------
            # 2a. Compute Revenue YoY Growth
            # -----------------------------------------------------------------
            if len(income_reports) >= 2:
                st.subheader("Revenue Growth Analysis (YoY)")
                inc_df = pd.DataFrame(income_reports)
                inc_df["Year"] = inc_df["fiscalDateEnding"].str[:4]
                inc_df["totalRevenue"] = pd.to_numeric(inc_df["totalRevenue"], errors="coerce")
                
                inc_df = inc_df.dropna(subset=["totalRevenue"])
                inc_df = inc_df.sort_values("Year")
                
                inc_df["Revenue_Growth_%"] = inc_df["totalRevenue"].pct_change() * 100
                
                # Rename column for charting
                inc_df_renamed = inc_df.rename(columns={"Revenue_Growth_%": "value"})
                inc_df_renamed = inc_df_renamed.dropna(subset=["value"])
                
                # Compute color for each row based on growth thresholds
                inc_df_renamed["growth_color"] = inc_df_renamed["value"].apply(
                    lambda x: "green" if x >= 20 else "orange" if x >= 10 else "red"
                )
                
                chart = (
                    alt.Chart(inc_df_renamed)
                    .mark_bar()
                    .encode(
                        x=alt.X("Year:N", sort=None),
                        y=alt.Y("value:Q", title="Revenue Growth (%)", axis=alt.Axis(format=",.2f")),
                        color=alt.Color("growth_color:N", scale=None),
                        tooltip=[
                            alt.Tooltip("Year:N", title="Year"),
                            alt.Tooltip("value:Q", title="Growth (%)", format=",.2f")
                        ]
                    )
                    .properties(width=600, height=300, title="YoY Revenue Growth")
                )
                st.altair_chart(chart, use_container_width=True)
                
                latest_growth = inc_df_renamed["value"].iloc[-1]
                st.markdown(f"**Latest Revenue Growth:** {color_coded_growth_text(latest_growth)}", unsafe_allow_html=True)
            
            # -----------------------------------------------------------------
            # 2b. Compute Operating Cash Flow YoY Growth
            # -----------------------------------------------------------------
            if len(cashflow_reports) >= 2:
                st.subheader("Operating Cash Flow Growth Analysis (YoY)")
                cf_df = pd.DataFrame(cashflow_reports)
                cf_df["Year"] = cf_df["fiscalDateEnding"].str[:4]
                cf_df["operatingCashflow"] = pd.to_numeric(cf_df["operatingCashflow"], errors="coerce")
                
                cf_df = cf_df.dropna(subset=["operatingCashflow"])
                cf_df = cf_df.sort_values("Year")
                
                cf_df["OCF_Growth_%"] = cf_df["operatingCashflow"].pct_change() * 100
                
                cf_df_renamed = cf_df.rename(columns={"OCF_Growth_%": "value"})
                cf_df_renamed = cf_df_renamed.dropna(subset=["value"])
                
                cf_df_renamed["growth_color"] = cf_df_renamed["value"].apply(
                    lambda x: "green" if x >= 20 else "orange" if x >= 10 else "red"
                )
                
                chart_ocf = (
                    alt.Chart(cf_df_renamed)
                    .mark_bar()
                    .encode(
                        x=alt.X("Year:N", sort=None),
                        y=alt.Y("value:Q", title="Operating CF Growth (%)", axis=alt.Axis(format=",.2f")),
                        color=alt.Color("growth_color:N", scale=None),
                        tooltip=[
                            alt.Tooltip("Year:N", title="Year"),
                            alt.Tooltip("value:Q", title="Growth (%)", format=",.2f")
                        ]
                    )
                    .properties(width=600, height=300, title="YoY Operating Cash Flow Growth")
                )
                st.altair_chart(chart_ocf, use_container_width=True)
                
                latest_ocf_growth = cf_df_renamed["value"].iloc[-1]
                st.markdown(f"**Latest Operating CF Growth:** {color_coded_growth_text(latest_ocf_growth)}", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Utility: Color-Coded Growth Text Function
# -----------------------------------------------------------------------------
def color_coded_growth_text(growth_value: float) -> str:
    """
    Returns an HTML string with a color-coded classification based on the growth_value:
    - < 10%: red (Weak)
    - 10-20%: orange (Moderate)
    - >= 20%: green (Strong)
    """
    if pd.isna(growth_value):
        return "N/A"
    if growth_value < 10:
        return f"<span style='color:red;'>{growth_value:.2f}% (Weak)</span>"
    elif growth_value < 20:
        return f"<span style='color:orange;'>{growth_value:.2f}% (Moderate)</span>"
    else:
        return f"<span style='color:green;'>{growth_value:.2f}% (Strong)</span>"
