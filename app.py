import streamlit as st
import requests
from datetime import datetime

# Fetch API key from correct secret path
API_KEY = st.secrets["fmp"]["api_key"]

def get_stock_profile(ticker):
    """Fetches stock profile (sector, financial ratios, etc.)."""
    url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200 and response.json():
        return response.json()[0]  # Extract first element
    return None

def get_sector_pe():
    """Fetches sector P/E ratios using today's date."""
    today = datetime.today().strftime("%Y-%m-%d")
    url = f"https://financialmodelingprep.com/api/v4/sector_price_earning_ratio?date={today}&apikey={API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            data = response.json()
            return {item["sector"].strip(): float(item["pe"]) for item in data}
        except Exception as e:
            return {}
    return {}

def format_percentage(value):
    """Formats a decimal as a percentage (e.g., 0.2031 → 20.31%)."""
    return f"{value * 100:.2f}%" if value is not None else "N/A"

# Streamlit UI
st.title("📊 Stock Valuation Dashboard")

# User input for stock ticker
ticker = st.text_input("Enter stock ticker:", value="AAPL").upper()
if st.button("Analyze"):
    stock_profile = get_stock_profile(ticker)

    if stock_profile:
        stock_sector = stock_profile.get("sector", "Unknown")
        stock_pe = stock_profile.get("beta", "N/A")  # Adjust key if needed
        dcf_valuation = stock_profile.get("dcf", "N/A")
        stock_price = stock_profile.get("price", "N/A")

        # Fetch sector P/E
        sector_pe_data = get_sector_pe()
        sector_pe = sector_pe_data.get(stock_sector, "N/A")

        # Display key valuation metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 DCF Valuation", f"${dcf_valuation:.2f}")
        with col2:
            st.metric("📈 Stock Price", f"${stock_price:.2f}")

        # Financial Ratios
        st.markdown("### 📊 **Key Financial Ratios**")

        financial_ratios = {
            "Price-to-Earnings (P/E) Ratio": (stock_pe, "Higher P/E suggests strong growth expectations. Below 15 = undervalued, 15-25 = fair, above 25 = overvalued."),
            "Current Ratio": (stock_profile.get("currentRatio"), "Above 1.5 = strong liquidity, 1.0-1.5 = adequate, below 1 = potential liquidity issues."),
            "Quick Ratio": (stock_profile.get("quickRatio"), "Above 1.0 = strong liquidity, 0.5-1.0 = acceptable, below 0.5 = risky."),
            "Debt to Equity Ratio": (stock_profile.get("debtToEquity"), "Below 1.0 = conservative financing, 1.0-2.0 = moderate risk, above 2.0 = highly leveraged."),
            "Return on Equity (ROE)": (format_percentage(stock_profile.get("returnOnEquity")), "Above 15% = strong, 10-15% = average, below 10% = weak."),
        }

        for ratio, (value, description) in financial_ratios.items():
            st.markdown(f"**{ratio}:** {value}")
            st.markdown(f"*{description}*")

        # P/E Ratio Comparison
        st.markdown("### 📊 **P/E Ratio Comparison**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(f"{ticker} P/E", f"{stock_pe:.2f}")
        with col2:
            st.metric(f"{stock_sector} Sector P/E", f"{sector_pe:.2f}" if sector_pe != "N/A" else "N/A")

        # Interpretation
        if sector_pe != "N/A":
            if stock_pe > sector_pe:
                st.warning(f"{ticker} has a higher P/E than its sector average. It may be overvalued.")
            else:
                st.success(f"{ticker} has a lower P/E than its sector average. It may be undervalued.")
        else:
            st.error(f"⚠️ Sector P/E not found for {stock_sector}. Check sector name matching above.")
    else:
        st.error("Invalid stock ticker or no data available.")


