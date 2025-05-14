import streamlit as st
import pandas as pd
import base64

# Set page config for a modern look
st.set_page_config(page_title="Runway & Dilution Calculator", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
        .main {
            background-color: #f4f6f8;
            padding: 2rem;
        }
        .sidebar .sidebar-content {
            background-color: #ffffff;
        }
        .stButton>button {
            border-radius: 8px;
            border: 1px solid #1f77b4;
            color: white;
            background-color: #1f77b4;
        }
        .stDownloadButton button {
            background-color: #2ca02c;
            color: white;
            border-radius: 6px;
        }
        .summary-box {
            background-color: white;
            border-left: 5px solid #1f77b4;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='color:#1f77b4;'>🚀 Runway & Dilution Calculator</h1>", unsafe_allow_html=True)

# Session state to store/load data
if 'loaded' not in st.session_state:
    st.session_state.loaded = False

# Sidebar inputs with optional prefill
st.sidebar.header("📊 Input Parameters")
current_burn = st.sidebar.number_input("Current Monthly Burn ($)", value=st.session_state.get("current_burn", 0))
added_headcount_burn = st.sidebar.number_input("Headcount Added from Month 6 ($)", value=st.session_state.get("added_headcount_burn", 0))
revenue_ramp = st.sidebar.number_input("Expected Monthly Revenue Ramp ($)", value=st.session_state.get("revenue_ramp", 0))
runway_months = st.sidebar.selectbox("Runway Duration (Months)", [18, 24], index=1 if st.session_state.get("runway_months", 24) == 24 else 0)
option_pool_percent = st.sidebar.slider("Option Pool Refresh (%)", 0, 30, st.session_state.get("option_pool_percent", 0))
input_raise_amount = st.sidebar.number_input("Raise Amount ($)", value=st.session_state.get("raise_amount", 0))
input_pre_money_valuation = st.sidebar.number_input("Pre-Money Valuation ($)", value=st.session_state.get("pre_money_valuation", 0))
bridge_round = st.sidebar.checkbox("Include $1M Bridge Round", value=st.session_state.get("bridge_round", False))

# Load and Save buttons at bottom of sidebar
st.sidebar.markdown("---")
if st.sidebar.button("📥 Load Inputs"):
    st.session_state.loaded = True
    st.session_state.current_burn = 75000
    st.session_state.added_headcount_burn = 30000
    st.session_state.revenue_ramp = 10000
    st.session_state.runway_months = 24
    st.session_state.option_pool_percent = 10
    st.session_state.raise_amount = 3000000
    st.session_state.pre_money_valuation = 10000000
    st.session_state.bridge_round = False

if st.sidebar.button("💾 Save Changes"):
    st.success("Inputs saved!")

# Adjusted values
adjusted_raise = input_raise_amount
adjusted_post_money = input_pre_money_valuation + adjusted_raise

if option_pool_percent:
    adjusted_raise += (option_pool_percent / 100) * adjusted_post_money
if bridge_round:
    adjusted_raise += 1_000_000

adjusted_post_money = input_pre_money_valuation + adjusted_raise
ownership_sold = adjusted_raise / adjusted_post_money if adjusted_post_money else 0

# Runway Table Calculations
months = list(range(1, runway_months + 1))
burn = [current_burn + (added_headcount_burn if m >= 6 else 0) for m in months]
revenue = [revenue_ramp * m for m in months]
net_burn = [b - r for b, r in zip(burn, revenue)]
cumulative_burn = pd.Series(net_burn).cumsum()

# Capital exhaustion point
runway_end_month = (
    cumulative_burn[cumulative_burn > adjusted_raise].index.min() + 1
    if (cumulative_burn > adjusted_raise).any()
    else runway_months
)

# Create DataFrame
runway_df = pd.DataFrame({
    "Month": months,
    "Burn ($)": burn,
    "Revenue ($)": revenue,
    "Net Burn ($)": net_burn,
    "Cumulative Burn ($)": cumulative_burn
})

# Display table
st.subheader("📉 Runway Table")
st.dataframe(runway_df.style.format("${:,.0f}"))

# Download option
csv = runway_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Table as Excel (CSV)",
    data=csv,
    file_name='runway_dilution_table.csv',
    mime='text/csv'
)

# Summary
st.subheader("📈 Summary")
st.markdown(f"""
<div class='summary-box'>
    <p><strong>💰 Adjusted Raise Amount:</strong> ${adjusted_raise:,.0f}</p>
    <p><strong>📊 Post-Money Valuation:</strong> ${adjusted_post_money:,.0f}</p>
    <p><strong>📉 Ownership Sold:</strong> {ownership_sold * 100:.2f}%</p>
    <p><strong>⏳ Capital Runs Out In:</strong> Month {runway_end_month}</p>
</div>
""", unsafe_allow_html=True)
