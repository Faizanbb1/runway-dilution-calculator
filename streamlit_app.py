import streamlit as st
import pandas as pd

# Title
st.title("Runway & Dilution Calculator")

# Sidebar inputs
st.sidebar.header("Inputs")
current_burn = st.sidebar.number_input("Current Monthly Burn ($)", value=75000)
added_headcount_burn = st.sidebar.number_input("Headcount Added from Month 6 ($)", value=30000)
revenue_ramp = st.sidebar.number_input("Expected Monthly Revenue Ramp ($)", value=10000)
runway_months = st.sidebar.selectbox("Runway Duration (Months)", [18, 24], index=1)
option_pool_percent = st.sidebar.slider("Option Pool Refresh (%)", 0, 30, 10)
raise_amount = st.sidebar.number_input("Raise Amount ($)", value=3_000_000)
pre_money_valuation = st.sidebar.number_input("Pre-Money Valuation ($)", value=10_000_000)
bridge_round = st.sidebar.checkbox("Include $1M Bridge Round", value=False)

# Option Pool and Bridge Round Adjustments
post_money_valuation = pre_money_valuation + raise_amount

if option_pool_percent:
    raise_amount += (option_pool_percent / 100) * post_money_valuation

if bridge_round:
    raise_amount += 1_000_000

post_money_valuation = pre_money_valuation + raise_amount
ownership_sold = raise_amount / post_money_valuation

# Runway Table Calculations
months = list(range(1, runway_months + 1))
burn = [current_burn + (added_headcount_burn if m >= 6 else 0) for m in months]
revenue = [revenue_ramp * m for m in months]
net_burn = [b - r for b, r in zip(burn, revenue)]
cumulative_burn = pd.Series(net_burn).cumsum()

# Capital exhaustion point
runway_end_month = (
    cumulative_burn[cumulative_burn > raise_amount].index.min() + 1
    if (cumulative_burn > raise_amount).any()
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
st.subheader("Runway Table")
st.dataframe(runway_df.style.format("${:,.0f}"))

# Summary
st.subheader("Summary")
st.markdown(f"**Adjusted Raise Amount:** ${raise_amount:,.0f}")
st.markdown(f"**Post-Money Valuation:** ${post_money_valuation:,.0f}")
st.markdown(f"**Ownership Sold:** {ownership_sold * 100:.2f}%")
st.markdown(f"**Capital Runs Out In:** Month {runway_end_month}")
