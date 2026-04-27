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
    return pd.read_csv("https://raw.githubusercontent.com/raaahuuull/Nassau_Candy_Analysis/refs/heads/main/Nassau%20Candy%20Distributor.csv")  # replace with GitHub raw URL if needed

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

st.sidebar.markdown("### Analysis Controls")

risk_mode = st.sidebar.radio(
    "High Risk Definition",
    ["Basic (Margin < 20%)", "Advanced (Low Margin + Low Sales)"]
)

st.sidebar.caption("Switch between simple and advanced risk logic.")

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


# -------------------------------
# COST vs SALES DIAGNOSTICS
# -------------------------------
st.markdown("## Cost vs Sales Diagnostics")
st.markdown("This chart shows cost efficiency of each product.")

cost_df = filtered_df.copy()
cost_df['Cost'] = cost_df['Sales'] - cost_df['Gross Profit']

fig = px.scatter(
    cost_df,
    x='Sales',
    y='Cost',
    color='Division',
    size='Sales',   # 👈 NEW (makes points visible)
    hover_data=['Product Name'],
    title='Cost vs Sales Analysis'
)

fig.update_traces(marker=dict(size=12, opacity=0.8))

max_val = max(cost_df['Sales'].max(), cost_df['Cost'].max())

fig.add_shape(
    type="line",
    x0=0, y0=0,
    x1=max_val, y1=max_val,
    line=dict(color="red", dash="dash")
)

st.plotly_chart(fig, use_container_width=True, height=500)

st.caption("Points above the diagonal line indicate cost exceeding sales (potential loss).")

# -----------------------------
# HIGH RISK PRODUCTS
# -----------------------------
st.subheader("High Risk Products")

prod_full = filtered_df.groupby('Product Name').agg({
    'Sales': 'sum',
    'Gross Profit': 'sum',
    'Units': 'sum'
}).reset_index()

# Safe margin calculation
prod_full['Margin %'] = (
    prod_full['Gross Profit'] / prod_full['Sales']
).replace([float('inf'), -float('inf')], 0).fillna(0) * 100

# Toggle logic
if risk_mode == "Basic (Margin < 20%)":
    high_risk = prod_full[prod_full['Margin %'] < 20]
else:
    high_risk = prod_full[
        (prod_full['Margin %'] < 50) &
        (prod_full['Sales'] < prod_full['Sales'].quantile(0.4))
    ]

st.caption(f"Risk model: {risk_mode}")

if high_risk.empty:
    st.info("No high-risk products identified based on current thresholds.")
else:
    # Add reason
    if risk_mode == "Basic (Margin < 20%)":
        high_risk = high_risk.assign(Reason="Low margin (<20%)")
    else:
        high_risk = high_risk.assign(Reason="Low margin & low sales")

    display_df = high_risk.sort_values(by='Margin %').round(2)

    st.write(f"{len(high_risk)} high-risk product(s) identified")

    st.dataframe(display_df, use_container_width=True)
    
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
st.write(f"Top {len(cutoff_80)} products contribute ~80% of total profit, indicating strong revenue concentration.")
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
