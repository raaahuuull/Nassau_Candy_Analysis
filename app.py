import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Nassau Candy Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# PREMIUM STYLING
# -------------------------------
st.markdown("""
<style>
.main {
    background-color: #f8f9fa;
}
h1, h2, h3 {
    color: #2c3e50;
}
.stMetric {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# TITLE
# -------------------------------
st.title("Nassau Candy Profitability Dashboard")
st.markdown("Product and Division Performance Analysis")

# -------------------------------
# LOAD DATA
# -------------------------------
df = pd.read_csv("Nassau Candy Distributor.csv")
df = df.dropna()

# -------------------------------
# SIDEBAR FILTER
# -------------------------------
st.sidebar.header("Filters")

division_filter = st.sidebar.multiselect(
    "Select Division",
    options=df['Division'].unique(),
    default=df['Division'].unique()
)

df = df[df['Division'].isin(division_filter)]

# -------------------------------
# KPI SECTION
# -------------------------------
total_revenue = df['Sales'].sum()
total_profit = df['Gross Profit'].sum()
overall_margin = (total_profit / total_revenue) * 100

st.markdown("## Key Metrics")

col1, col2, col3 = st.columns(3)
col1.metric("Revenue", f"${total_revenue:,.0f}")
col2.metric("Profit", f"${total_profit:,.0f}")
col3.metric("Margin", f"{overall_margin:.2f}%")

st.markdown("---")

# -------------------------------
# DIVISION ANALYSIS
# -------------------------------
st.markdown("## Division Performance")

division = df.groupby('Division').agg({
    'Sales': 'sum',
    'Gross Profit': 'sum'
}).reset_index()

division['Margin %'] = (division['Gross Profit'] / division['Sales']) * 100

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots()
    ax.bar(division['Division'], division['Margin %'])
    ax.set_title("Margin by Division")
    ax.set_ylabel("Margin %")
    st.pyplot(fig)

with col2:
    division['Revenue Share'] = division['Sales'] / division['Sales'].sum()

    fig2, ax2 = plt.subplots()
    ax2.pie(
        division['Revenue Share'],
        labels=division['Division'],
        autopct='%1.1f%%',
        startangle=90
    )
    ax2.set_title("Revenue Distribution")
    st.pyplot(fig2)

st.markdown("---")

# -------------------------------
# PARETO ANALYSIS
# -------------------------------
st.markdown("## Pareto Analysis (80/20 Rule)")

prod = df.groupby('Product Name').agg({
    'Sales': 'sum',
    'Gross Profit': 'sum'
}).reset_index()

prod['Total_Profit'] = prod['Gross Profit']

pareto = prod.sort_values('Total_Profit', ascending=False)
pareto['Cumulative %'] = (
    pareto['Total_Profit'].cumsum() / pareto['Total_Profit'].sum()
) * 100

fig3, ax1 = plt.subplots(figsize=(10,5))

ax1.bar(pareto['Product Name'], pareto['Total_Profit'])
ax1.set_ylabel("Profit")

ax2 = ax1.twinx()
ax2.plot(
    pareto['Product Name'],
    pareto['Cumulative %'],
    color='red',
    marker='o'
)
ax2.set_ylabel("Cumulative %")

plt.xticks(rotation=45, ha='right')
st.pyplot(fig3)

st.markdown("---")

# -------------------------------
# RISK ANALYSIS
# -------------------------------
st.markdown("## High Risk Products")

# Risk logic
df['Cost_to_Sales_Ratio'] = (df['Cost'] / df['Sales']) * 100
df['Gross_Margin_Pct'] = (df['Gross Profit'] / df['Sales']) * 100

df['Risk_Flag'] = (
    (df['Cost_to_Sales_Ratio'] > 60) &
    (df['Gross_Margin_Pct'] < 50)
)

risk_df = df[df['Risk_Flag'] == True]

st.dataframe(
    risk_df[['Product Name', 'Sales', 'Gross Profit', 'Cost_to_Sales_Ratio']]
)

st.markdown("---")

# -------------------------------
# INSIGHTS SECTION
# -------------------------------
st.markdown("## Key Insights")

best_div = division.loc[division['Margin %'].idxmax()]
worst_div = division.loc[division['Margin %'].idxmin()]

best_product = prod.sort_values('Total_Profit', ascending=False).iloc[0]

pareto_cutoff = pareto[pareto['Cumulative %'] <= 80]

st.write(f"Best Division: {best_div['Division']} ({best_div['Margin %']:.2f}%)")
st.write(f"Lowest Performing Division: {worst_div['Division']} ({worst_div['Margin %']:.2f}%)")
st.write(f"Top Product: {best_product['Product Name']}")
st.write(f"Pareto Insight: {len(pareto_cutoff)} products generate 80% of profit")