import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter


# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Nassau Candy Dashboard",
    layout="wide"
)


# ==========================================
# LOAD DATA
# ==========================================

df = pd.read_csv("Nassau Candy Distributor.csv")


# ==========================================
# DATA CLEANING
# ==========================================

df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y')
df['Ship Date'] = pd.to_datetime(df['Ship Date'], format='%d-%m-%Y')

# Remove invalid sales rows
df = df[df['Sales'] > 0]

# Fill missing units
df['Units'] = df['Units'].fillna(df['Units'].median())

# Standardize Division names
df['Division'] = df['Division'].str.strip().str.title()


# ==========================================
# KPI CALCULATIONS
# ==========================================

df['Gross Margin %'] = (
    df['Gross Profit'] / df['Sales']
) * 100

df['Profit Per Unit'] = (
    df['Gross Profit'] / df['Units']
)

total_sales_all = df['Sales'].sum()

df['Revenue Contribution %'] = (
    df['Sales'] / total_sales_all
) * 100

total_profit_all = df['Gross Profit'].sum()

df['Profit Contribution %'] = (
    df['Gross Profit'] / total_profit_all
) * 100


# ==========================================
# PDF GENERATION FUNCTION
# ==========================================

def generate_pdf(data):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = []

    # Title
    title = Paragraph(
        "Nassau Candy Distributor Profitability Report",
        styles['Title']
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    # KPI Summary
    total_sales = data['Sales'].sum()
    total_profit = data['Gross Profit'].sum()
    avg_margin = data['Gross Margin %'].mean()

    summary = f"""
    <b>Total Sales:</b> ${total_sales:,.2f}<br/>
    <b>Total Profit:</b> ${total_profit:,.2f}<br/>
    <b>Average Margin:</b> {avg_margin:.2f}%<br/>
    """

    elements.append(
        Paragraph(summary, styles['BodyText'])
    )

    elements.append(Spacer(1, 20))

    # Top Products
    top_products = data.groupby(
        'Product Name'
    )['Gross Profit'].sum().sort_values(
        ascending=False
    ).head(10)

    elements.append(
        Paragraph(
            "Top 10 Profitable Products",
            styles['Heading2']
        )
    )

    for product, profit in top_products.items():

        text = f"{product} : ${profit:,.2f}"

        elements.append(
            Paragraph(text, styles['BodyText'])
        )

    # Build PDF
    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    return pdf


# ==========================================
# SIDEBAR FILTERS
# ==========================================

st.sidebar.title("Filters")

# Division Filter
division = st.sidebar.multiselect(
    "Select Division",
    options=df['Division'].unique(),
    default=df['Division'].unique()
)

# Margin Filter
margin_filter = st.sidebar.slider(
    "Minimum Margin %",
    min_value=0,
    max_value=100,
    value=10
)

# Date Filter
start_date = st.sidebar.date_input(
    "Start Date",
    value=df['Order Date'].min()
)

end_date = st.sidebar.date_input(
    "End Date",
    value=df['Order Date'].max()
)

# Product Search
product_search = st.sidebar.text_input(
    "Search Product"
)


# ==========================================
# APPLY FILTERS
# ==========================================

filtered_df = df[
    (df['Division'].isin(division)) &
    (df['Gross Margin %'] >= margin_filter) &
    (df['Order Date'] >= pd.to_datetime(start_date)) &
    (df['Order Date'] <= pd.to_datetime(end_date))
]

if product_search:

    filtered_df = filtered_df[
        filtered_df['Product Name'].str.contains(
            product_search,
            case=False
        )
    ]


# ==========================================
# DASHBOARD TITLE
# ==========================================

st.title(
    "Product Line Profitability & Margin Performance Analysis"
)

st.subheader("Nassau Candy Distributor")


# ==========================================
# KPI METRICS
# ==========================================

total_sales = filtered_df['Sales'].sum()

total_profit = filtered_df['Gross Profit'].sum()

avg_margin = filtered_df['Gross Margin %'].mean()

avg_profit_unit = filtered_df['Profit Per Unit'].mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Sales",
    round(total_sales, 4)
)

col2.metric(
    "Total Profit",
    round(total_profit, 4)
)

col3.metric(
    "Average Margin %",
    round(avg_margin, 4)
)

col4.metric(
    "Profit Per Unit",
    round(avg_profit_unit, 4)
)


# ==========================================
# TOP PROFITABLE PRODUCTS
# ==========================================

st.header("Top Profitable Products")

top_products = filtered_df.groupby(
    'Product Name'
)['Gross Profit'].sum().reset_index()

top_products = top_products.sort_values(
    by='Gross Profit',
    ascending=False
).head(10)

fig1 = px.bar(
    top_products,
    x='Product Name',
    y='Gross Profit',
    color='Gross Profit',
    title='Top 10 Profitable Products'
)

st.plotly_chart(
    fig1,
    use_container_width=True
)


# ==========================================
# DIVISION PERFORMANCE
# ==========================================

st.header("Division Performance Dashboard")

division_analysis = filtered_df.groupby(
    'Division'
).agg({
    'Sales': 'sum',
    'Gross Profit': 'sum',
    'Gross Margin %': 'mean'
}).reset_index()

fig2 = px.bar(
    division_analysis,
    x='Division',
    y=['Sales', 'Gross Profit'],
    barmode='group',
    title='Revenue vs Profit by Division'
)

st.plotly_chart(
    fig2,
    use_container_width=True
)


# ==========================================
# MARGIN DISTRIBUTION
# ==========================================

st.header("Margin Distribution by Division")

fig3 = px.box(
    filtered_df,
    x='Division',
    y='Gross Margin %',
    color='Division',
    title='Margin Distribution'
)

st.plotly_chart(
    fig3,
    use_container_width=True
)


# ==========================================
# COST VS SALES SCATTER
# ==========================================

st.header("Cost vs Sales Diagnostics")

fig4 = px.scatter(
    filtered_df,
    x='Cost',
    y='Sales',
    color='Gross Margin %',
    hover_data=['Product Name'],
    title='Cost vs Sales Scatter Analysis'
)

st.plotly_chart(
    fig4,
    use_container_width=True
)


# ==========================================
# PARETO ANALYSIS
# ==========================================

st.header("Profit Concentration Analysis")

pareto = filtered_df.groupby(
    'Product Name'
)['Gross Profit'].sum().sort_values(
    ascending=False
).reset_index()

pareto['Cumulative Profit'] = pareto[
    'Gross Profit'
].cumsum()

pareto['Cumulative %'] = (
    pareto['Cumulative Profit']
    / pareto['Gross Profit'].sum()
) * 100

fig5 = px.line(
    pareto,
    x='Product Name',
    y='Cumulative %',
    title='Pareto Analysis - Profit Concentration'
)

st.plotly_chart(
    fig5,
    use_container_width=True
)


# ==========================================
# HIGH SALES LOW MARGIN PRODUCTS
# ==========================================

st.header("High Sales but Low Margin Products")

risk_products = filtered_df[
    (filtered_df['Sales'] >
     filtered_df['Sales'].quantile(0.75)) &

    (filtered_df['Gross Margin %'] <
     filtered_df['Gross Margin %'].quantile(0.25))
]

st.dataframe(
    risk_products[[
        'Product Name',
        'Sales',
        'Cost',
        'Gross Profit',
        'Gross Margin %'
    ]]
)


# ==========================================
# RAW DATA
# ==========================================

st.header("Dataset Preview")

st.dataframe(filtered_df)


# ==========================================
# CSV DOWNLOAD
# ==========================================

st.header("Download Reports")

csv = filtered_df.to_csv(
    index=False
).encode('utf-8')

st.download_button(
    label="Download CSV Report",
    data=csv,
    file_name='nassau_candy_report.csv',
    mime='text/csv'
)


# ==========================================
# PDF DOWNLOAD
# ==========================================

pdf = generate_pdf(filtered_df)

st.download_button(
    label="Download PDF Report",
    data=pdf,
    file_name="nassau_profitability_report.pdf",
    mime="application/pdf"
)
