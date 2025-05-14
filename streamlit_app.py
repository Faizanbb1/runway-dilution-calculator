import streamlit as st
import pandas as pd
import base64
from weasyprint import HTML
import altair as alt

# Set page config
st.set_page_config(page_title="Runway & Dilution Calculator", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: 'Inter', 'Segoe UI', sans-serif;
            background-color: #f8f9fa;
        }
        .sidebar .sidebar-content {
            background-color: #ffffff;
        }
        h1, h2, h3 {
            color: #FF385C;
        }
        .stButton > button {
            background-color: #FF385C;
            color: white;
            padding: 10px 24px;
            border-radius: 12px;
            border: none;
            font-weight: 600;
            font-size: 16px;
        }
        .stDownloadButton button {
            background-color: #008489;
            color: white;
            border-radius: 10px;
            font-weight: 600;
        }
        .summary-box {
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.05);
            font-size: 17px;
            border-left: 6px solid #FF385C;
            margin-bottom: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='margin-bottom: 0.5rem;'>📊 Runway & Dilution Calculator</h1>", unsafe_allow_html=True)
st.markdown("""
<p style='color: #777; font-size: 18px;'>
    💡 <em>Use the sidebar to input your burn, raise and valuation assumptions.<br>
    Your summary and projections will appear instantly below.</em>
</p>
""", unsafe_allow_html=True)

# Session state
if 'loaded' not in st.session_state:
    st.session_state.loaded = False

# Sidebar inputs
with st.sidebar.expander("🛠️ Configure Your Inputs", expanded=True):
    current_burn = st.number_input("Current Monthly Burn ($)", value=st.session_state.get("current_burn", 0))
    added_headcount_burn = st.number_input("Headcount Added from Month 6 ($)", value=st.session_state.get("added_headcount_burn", 0))
    revenue_ramp = st.number_input("Expected Monthly Revenue Ramp ($)", value=st.session_state.get("revenue_ramp", 0))
    runway_months = st.selectbox("Runway Duration (Months)", [18, 24], index=1 if st.session_state.get("runway_months", 24) == 24 else 0)
    option_pool_percent = st.slider("Option Pool Refresh (%)", 0, 30, st.session_state.get("option_pool_percent", 0))
    input_raise_amount = st.number_input("Raise Amount ($)", value=st.session_state.get("raise_amount", 0))
    input_pre_money_valuation = st.number_input("Pre-Money Valuation ($)", value=st.session_state.get("pre_money_valuation", 0))
    bridge_round = st.checkbox("Include $1M Bridge Round", value=st.session_state.get("bridge_round", False))

if st.sidebar.button("📅 Load Example"):
    st.session_state.loaded = True
    st.session_state.current_burn = 75000
    st.session_state.added_headcount_burn = 30000
    st.session_state.revenue_ramp = 10000
    st.session_state.runway_months = 24
    st.session_state.option_pool_percent = 10
    st.session_state.raise_amount = 3000000
    st.session_state.pre_money_valuation = 10000000
    st.session_state.bridge_round = False

# Adjusted calculations
raw_raise = input_raise_amount
initial_post_money = input_pre_money_valuation + raw_raise
adjusted_raise = raw_raise + ((option_pool_percent / 100) * input_pre_money_valuation)
if bridge_round:
    adjusted_raise += 1_000_000
adjusted_post_money = input_pre_money_valuation + adjusted_raise
ownership_sold = adjusted_raise / adjusted_post_money if adjusted_post_money else 0

# Runway Calculations
months = list(range(1, runway_months + 1))
burn = [current_burn + (added_headcount_burn if m >= 6 else 0) for m in months]
revenue = [revenue_ramp * m for m in months]
net_burn = [b - r for b, r in zip(burn, revenue)]
cumulative_burn_series = pd.Series(net_burn).cumsum()
cumulative_burn = cumulative_burn_series.tolist()
runway_end_month = next((i + 1 for i, value in enumerate(cumulative_burn) if value > adjusted_raise), runway_months)

# Insights
health_score = max(0, 100 - ownership_sold * 100)
runway_color = '🟢 Healthy' if runway_end_month >= 20 else '🟡 Caution' if runway_end_month >= 12 else '🔴 Risky'

plain_english = f"""
<h1>Runway & Dilution Summary</h1>
<p><strong>💰 Adjusted Raise Amount:</strong> ${adjusted_raise:,.0f}</p>
<p><strong>📊 Post-Money Valuation:</strong> ${adjusted_post_money:,.0f}</p>
<p><strong>📉 Ownership Sold:</strong> {ownership_sold * 100:.2f}%</p>
<p><strong>⏳ Capital Runs Out In:</strong> Month {runway_end_month}</p>
<p><strong>💡 Insights:</strong></p>
<ul>
    <li>You are planning to raise: ${input_raise_amount:,.0f}</li>
    <li>This results in an <strong>ownership dilution of {ownership_sold * 100:.2f}%</strong>.</li>
    <li>You will have <strong>{runway_end_month} months</strong> of runway based on your profile.</li>
    <li><strong>Runway Status:</strong> {runway_color}</li>
    <li><strong>Financial Health Score:</strong> {health_score:.0f}/100</li>
</ul>
"""

# Summary PDF generation
pdf_path = "/mnt/data/runway_dilution_summary.pdf"
HTML(string=plain_english).write_pdf(pdf_path)

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("🧠 Explain My Results")
    st.markdown(plain_english, unsafe_allow_html=True)
    st.download_button("📄 Export Summary as PDF", data=open(pdf_path, "rb").read(), file_name="runway_summary.pdf", mime="application/pdf")

    st.subheader("📈 Financial Summary")
    st.markdown(f"""
    <div class='summary-box'>
        <p><strong>💰 Adjusted Raise Amount:</strong> ${adjusted_raise:,.0f}</p>
        <p><strong>📊 Post-Money Valuation:</strong> ${adjusted_post_money:,.0f}</p>
        <p><strong>📉 Ownership Sold:</strong> {ownership_sold * 100:.2f}%</p>
        <p><strong>⏳ Capital Runs Out In:</strong> Month {runway_end_month}</p>
    </div>
    """, unsafe_allow_html=True)

with col1:
    st.subheader("📅 Runway Breakdown")
    runway_df = pd.DataFrame({
        "Month": months,
        "Burn ($)": burn,
        "Revenue ($)": revenue,
        "Net Burn ($)": net_burn,
        "Cumulative Burn ($)": cumulative_burn,
        "Capital Depleted": ["🔴" if m == runway_end_month else "" for m in months]
    })
    st.dataframe(runway_df.style.format("${:,.0f}"), use_container_width=True, height=500)

    st.download_button(
        label="⬇️ Download CSV",
        data=runway_df.to_csv(index=False).encode('utf-8'),
        file_name='runway_dilution_table.csv',
        mime='text/csv'
    )

    st.subheader("📊 Burn vs Capital Chart")
    chart_data = pd.DataFrame({
        "Month": months,
        "Cumulative Burn": cumulative_burn,
        "Capital Raised": [float(adjusted_raise)] * len(months)
    })

    base = alt.Chart(chart_data).transform_fold(
        ["Cumulative Burn", "Capital Raised"],
        as_=["Category", "Value"]
    ).mark_line().encode(
        x=alt.X("Month:Q", title="Month"),
        y=alt.Y("Value:Q", title="USD ($)", scale=alt.Scale(zero=False)),
        color=alt.Color("Category:N", legend=alt.Legend(title="Legend")),
        tooltip=["Month", "Category", "Value"]
    ).properties(width=700, height=400)

    vertical_line = alt.Chart(pd.DataFrame({"Month": [runway_end_month], "Label": ["Capital Exhausted"]})).mark_rule(
        strokeDash=[4, 4], color="gray"
    ).encode(x="Month:Q", tooltip="Label:N")

    st.altair_chart(base + vertical_line, use_container_width=True)
