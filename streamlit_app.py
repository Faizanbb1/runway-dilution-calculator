import streamlit as st
import pandas as pd
import base64

# Set page config for a modern look
st.set_page_config(page_title="Runway & Dilution Calculator", layout="wide")

# Custom CSS for premium UI
st.markdown("""
    <style>
        /* GLOBAL RESET TO LIGHT CREAM */
        html, body, [class*="st-"], .block-container {
            background-color: #fffaf2 !important;
            color: #333 !important;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }

        /* Sidebar styling */
        .css-1d391kg, .css-1v0mbdj, .css-1v3fvcr, .css-1cpxqw2, .css-1dp5vir {
            background-color: #fffaf2 !important;
        }

        .sidebar .sidebar-content, .css-hxt7ib {
            background-color: #fffaf2 !important;
            color: #333 !important;
        }

        /* Headings and highlights */
        h1, h2, h3, h4, h5 {
            color: #FF385C !important;
        }

        /* Buttons */
        .stButton > button {
            background-color: #FF385C !important;
            color: white !important;
            padding: 10px 24px;
            border-radius: 12px;
            border: none;
            font-weight: 600;
            font-size: 16px;
        }

        .stDownloadButton button {
            background-color: #008489 !important;
            color: white !important;
            border-radius: 10px;
            font-weight: 600;
        }

        /* Inputs and widgets */
        input, textarea, .stNumberInput, .stSelectbox, .stSlider {
            background-color: white !important;
            color: #333 !important;
            border-radius: 10px !important;
        }

        /* DataFrame styling */
        .stDataFrame {
            background-color: white !important;
            border-radius: 12px !important;
            padding: 12px;
            color: #333 !important;
        }

        /* Summary box */
        .summary-box {
            padding: 25px;
            border-radius: 12px;
            background: linear-gradient(to right, #fffefc, #fdf9f3) !important;
            box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.05);
            color: #333 !important;
            border-left: 6px solid #FF385C;
            margin-bottom: 1.5rem;
        }

        /* Override system dark mode */
        @media (prefers-color-scheme: dark) {
            html, body, [class*="st-"], .block-container, .css-hxt7ib {
                background-color: #fffaf2 !important;
                color: #333 !important;
            }
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

# Session state to store/load data
if 'loaded' not in st.session_state:
    st.session_state.loaded = False

# Sidebar inputs with onboarding
with st.sidebar.expander("🛠️ Configure Your Inputs", expanded=True):
    current_burn = st.number_input("Current Monthly Burn ($)", help="Total monthly cash outflows before new hires", value=st.session_state.get("current_burn", 0))
    added_headcount_burn = st.number_input("Headcount Added from Month 6 ($)", help="Monthly cost increase due to hiring after month 6", value=st.session_state.get("added_headcount_burn", 0))
    revenue_ramp = st.number_input("Expected Monthly Revenue Ramp ($)", help="Expected revenue increase per month", value=st.session_state.get("revenue_ramp", 0))
    runway_months = st.selectbox("Runway Duration (Months)", [18, 24], index=1 if st.session_state.get("runway_months", 24) == 24 else 0)
    option_pool_percent = st.slider("Option Pool Refresh (%)", 0, 30, st.session_state.get("option_pool_percent", 0))
    input_raise_amount = st.number_input("Raise Amount ($)", value=st.session_state.get("raise_amount", 0))
    input_pre_money_valuation = st.number_input("Pre-Money Valuation ($)", value=st.session_state.get("pre_money_valuation", 0))
    bridge_round = st.checkbox("Include $1M Bridge Round", help="Toggle to simulate an extra $1M in interim funding", value=st.session_state.get("bridge_round", False))
st.sidebar.markdown("---")
if st.sidebar.button("📥 Load Example"):
    st.session_state.loaded = True
    st.session_state.current_burn = 75000
    st.session_state.added_headcount_burn = 30000
    st.session_state.revenue_ramp = 10000
    st.session_state.runway_months = 24
    st.session_state.option_pool_percent = 10
    st.session_state.raise_amount = 3000000
    st.session_state.pre_money_valuation = 10000000
    st.session_state.bridge_round = False

if st.sidebar.button("💾 Save Inputs"):
    st.success("Inputs saved!")

# Adjusted values
raw_raise = input_raise_amount
initial_post_money = input_pre_money_valuation + raw_raise

# Adjust for option pool refresh (dilutes pre-money)
adjusted_raise = raw_raise + ((option_pool_percent / 100) * input_pre_money_valuation)

# Add bridge round if toggled
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

# Summary insights
health_score = max(0, 100 - ownership_sold * 100)
if runway_end_month >= 20:
    runway_color = '🟢 Healthy'
elif 12 <= runway_end_month < 20:
    runway_color = '🟡 Caution'
else:
    runway_color = '🔴 Risky'

plain_english = f"""
### Summary Insights:

- You are planning to raise: ${input_raise_amount:,.0f}
- This results in an **ownership dilution of {ownership_sold * 100:.2f}%**.
- Based on your burn and revenue profile, you will have **{runway_end_month} month{'s' if runway_end_month != 1 else ''}** of runway.
- **Runway Status:** {runway_color}
- **Financial Health Score:** {health_score:.0f}/100
"""

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("🧠 Explain My Results")
    st.markdown(plain_english)

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
        "Cumulative Burn ($)": cumulative_burn
    })
    st.dataframe(runway_df.style.format("${:,.0f}"), use_container_width=True, height=500)

    csv = runway_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name='runway_dilution_table.csv',
        mime='text/csv'
    )

    st.download_button(
        label="📄 Export Summary as PDF",
        data=plain_english.encode('utf-8'),
        file_name='runway_summary.pdf',
        mime='application/pdf',
        key='pdf-download-summary'
    )
