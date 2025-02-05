import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Streamlit App Configuration
st.set_page_config(page_title="Stock Screener", layout="wide")

API_KEY = st.secrets["fmp"]["api_key"]
BASE_URL = "https://financialmodelingprep.com/api/v3"

# 📌 Function to Fetch Growth Metrics (5-year historical)
def get_growth_metrics(ticker, years=5):
    url = f"{BASE_URL}/key-metrics/{ticker}?limit={years}&apikey={API_KEY}"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

# 📌 Function to Fetch DCF & Ratios (Value Screener)
def get_dcf(ticker):
    url = f"{BASE_URL}/discounted-cash-flow/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    return response.json()[0] if response.status_code == 200 else None

def get_ratios(ticker):
    url = f"{BASE_URL}/ratios/{ticker}?period=annual&limit=1&apikey={API_KEY}"
    response = requests.get(url)
    return response.json()[0] if response.status_code == 200 else None

# 📌 Function to Fetch Sector Averages
def get_sector_averages():
    url = f"https://financialmodelingprep.com/api/v4/sector_price_earning_ratio?apikey={API_KEY}"
    response = requests.get(url)
    return {item["sector"].strip(): item for item in response.json()} if response.status_code == 200 else None

# 📌 Growth Metrics Guidance
GROWTH_GUIDANCE = {
    "revenueGrowth": ("Revenue Growth (YoY)", "Above 20% = strong, 10-20% = average, below 10% = weak."),
    "priceToSalesRatio": ("Price-to-Sales (P/S) Ratio", "Lower is better, but high P/S may be justified by strong growth."),
    "enterpriseValueOverRevenue": ("EV/Revenue", "Used to value high-growth companies; compare to sector."),
    "grossProfitMargin": ("Gross Margin (%)", "Above 50% = strong pricing power and scalability."),
    "freeCashFlowPerShare": ("Free Cash Flow Per Share", "A positive and growing FCF is ideal for long-term sustainability."),
}

# 📌 Value Screener Ratios & Guidance
RATIO_GUIDANCE = {
    "priceEarningsRatio": ("Price-to-Earnings (P/E) Ratio", "Below 15 = undervalued, above 25 = overvalued."),
    "currentRatio": ("Current Ratio", "Above 1.5 = strong liquidity."),
    "quickRatio": ("Quick Ratio", "Above 1.0 = strong liquidity."),
    "debtEquityRatio": ("Debt to Equity Ratio", "Below 1.0 = conservative financing."),
    "returnOnEquity": ("Return on Equity (ROE)", "Above 15% = strong."),
}

# 📌 Sidebar Navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Choose a Screener", ["Value Stock Screener", "Growth Stock Screener", "Sector Comparison"])

# ===========================================
# 📌 VALUE STOCK SCREENER (DCF & Ratios)
# ===========================================
if page == "Value Stock Screener":
    st.title("💰 Value Stock Screener")

    ticker = st.text_input("Enter stock ticker for value analysis:").upper()

    if st.button("Analyze Value") and ticker:
        dcf_data = get_dcf(ticker)
        ratios_data = get_ratios(ticker)

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
        else:
            st.error("❌ Could not fetch value metrics for this stock.")

# ===========================================
# 📌 GROWTH STOCK SCREENER
# ===========================================
elif page == "Growth Stock Screener":
    st.title("🚀 Growth Stock Screener")

    ticker = st.text_input("Enter stock ticker for growth analysis:").upper()

    if st.button("Analyze Growth") and ticker:
        growth_data = get_growth_metrics(ticker)

        if growth_data:
            st.subheader(f"📈 Growth Metrics for {ticker} (Last 5 Years)")

            # Convert API response to DataFrame
            df = pd.DataFrame(growth_data)

            # Reverse order (latest first)
            df = df.iloc[::-1]

            # 📌 Display Growth Metrics Table
            st.dataframe(df[["date"] + list(GROWTH_GUIDANCE.keys())].set_index("date"))

            # 📌 Plot Growth Trends
            st.subheader("📊 Growth Trends Over Time")

            fig, ax = plt.subplots(figsize=(10, 5))

            for key, (title, _) in GROWTH_GUIDANCE.items():
                if key in df.columns and df[key].notnull().any():
                    ax.plot(df["date"], df[key], marker="o", label=title)

            ax.set_xlabel("Year")
            ax.set_ylabel("Growth Metrics")
            ax.legend()
            ax.grid()
            st.pyplot(fig)

        else:
            st.error("❌ Growth metrics not available for this stock.")

# ===========================================
# 📌 SECTOR COMPARISON SCREEN
# ===========================================
elif page == "Sector Comparison":
    st.title("📊 Sector Growth Comparison")

    sector_data = get_sector_averages()

    if sector_data:
        # Convert to DataFrame
        sector_df = pd.DataFrame.from_dict(sector_data, orient="index")

        # Display Sector Averages
        st.subheader("📌 Sector Average Growth Metrics")
        st.dataframe(sector_df)

        # 📌 Bar Chart of Sector P/E Ratios
        st.subheader("📊 Sector P/E Ratios")

        fig, ax = plt.subplots(figsize=(10, 5))
        sector_df_sorted = sector_df.sort_values(by="pe", ascending=False)
        ax.barh(sector_df_sorted.index, sector_df_sorted["pe"], color="blue")
        ax.set_xlabel("P/E Ratio")
        ax.set_title("Sector P/E Ratios")
        st.pyplot(fig)

    else:
        st.error("❌ Could not fetch sector data.")

