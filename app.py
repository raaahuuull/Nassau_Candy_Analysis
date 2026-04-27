import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Nassau Candy Dashboard", layout="wide")

# -----------------------------
# LOAD DATA (HYBRID)
# -----------------------------
@st.cache_data
def load_default_data():
    return pd.read_csv("data.csv")  # replace with GitHub raw URL if needed

st.sidebar.header("Data Source")

uploaded_file = st.sidebar.file_uploader("Upload CSV (optional)", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("Custom dataset loaded")
    except Exception as e:
        st.sidebar.error("Error loading file. Using default dataset.")
        df = load_default_data()
else:
    df = load_default_data()
    st.sidebar.info("Using default dataset")

# -----------------------------
# BASIC CHECK
# -----------------------------
required_cols = ['Division', 'Product Name', 'Sales', 'Gross Profit', 'Units']

if not all(col in df.columns for col in required_cols):
    st.error("Dataset format is incorrect. Required columns missing.")
    st.stop()

# -----------------------------
# SIDEBAR FILTER
# -----------------------------
division_filter = st.sidebar.multiselect(
    "Select Division",
    options=df['Division'].unique(),
    default=df['Division'].unique()
)

filtered_df = df[df['Division'].isin(division_filter)]

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# -----------------------------
# KPIs
# -----------------------------
total_revenue = filtered_df['Sales'].sum()
total_profit = filtered_df['Gross Profit'].sum()
overall_margin = (total_profit / total_revenue) * 100

col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${total_revenue:,.0f}")
col2.metric("Total Profit", f"${total_profit:,.0f}")
col3.metric("Overall Margin", f"{overall_margin:.2f}%")

# -----------------------------
# DIVISION ANALYSIS
# -----------------------------
st.subheader("Division Performance")

division = filtered_df.groupby('Division').agg({
    'Sales': 'sum',
    'Gross Profit': 'sum'
}).reset_index()

division['Margin %'] = (division['Gross Profit'] / division['Sales']) * 100

fig_div = px.bar(
    division,
    x='Division',
    y='Margin %',
    text_auto='.2f',
    title='Gross Margin by Division'
)

st.plotly_chart(fig_div, use_container_width=True)

# -----------------------------
# PARETO ANALYSIS
# -----------------------------
st.subheader("Pareto Analysis")

prod = filtered_df.groupby('Product Name').agg({
    'Gross Profit': 'sum'
}).reset_index()

pareto = prod.sort_values(by='Gross Profit', ascending=False)
pareto['Cumulative %'] = (pareto['Gross Profit'].cumsum() / pareto['Gross Profit'].sum()) * 100

pareto_display = pareto.head(10)

fig = go.Figure()

fig.add_trace(go.Bar(
    x=pareto_display['Product Name'],
    y=pareto_display['Gross Profit'],
    name='Profit'
))

fig.add_trace(go.Scatter(
    x=pareto_display['Product Name'],
    y=pareto_display['Cumulative %'],
    name='Cumulative %',
    yaxis='y2',
    mode='lines+markers'
))

fig.update_layout(
    title='Top Profit-Contributing Products',
    yaxis=dict(title='Profit'),
    yaxis2=dict(
        title='Cumulative %',
        overlaying='y',
        side='right',
        range=[0, 100]
    )
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# HIGH RISK PRODUCTS
# -----------------------------
st.subheader("High Risk Products")

prod_full = filtered_df.groupby('Product Name').agg({
    'Sales': 'sum',
    'Gross Profit': 'sum',
    'Units': 'sum'
}).reset_index()

prod_full['Margin %'] = (prod_full['Gross Profit'] / prod_full['Sales']) * 100

high_risk = prod_full[prod_full['Margin %'] < 20]

if high_risk.empty:
    st.info("No high-risk products found based on current criteria.")
else:
    st.dataframe(high_risk)

# -----------------------------
# KEY INSIGHTS (FIXED)
# -----------------------------
st.subheader("Key Insights")

# Division insights
if len(division) > 1:
    best_div = division.loc[division['Margin %'].idxmax()]
    worst_div = division.loc[division['Margin %'].idxmin()]

    st.write(f"Best Division: {best_div['Division']} ({best_div['Margin %']:.2f}%)")
    st.write(f"Weak Division: {worst_div['Division']} ({worst_div['Margin %']:.2f}%)")
else:
    only_div = division.iloc[0]
    st.write(f"Selected Division: {only_div['Division']} ({only_div['Margin %']:.2f}%)")

# Product insights
best_product = pareto.iloc[0]
cutoff_80 = pareto[pareto['Cumulative %'] <= 80]

st.write(f"Top Product: {best_product['Product Name']}")
st.write(f"{len(cutoff_80)} products generate 80% of total profit")

# -----------------------------
# BUSINESS RECOMMENDATIONS
# -----------------------------
st.subheader("Business Recommendations")

st.markdown("""
- Focus marketing and inventory on high-profit products  
- Reprice or optimize cost for low-margin products  
- Reduce dependency on a small set of products (Pareto risk)  
- Improve efficiency in low-performing divisions  
""")
