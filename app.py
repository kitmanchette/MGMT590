import streamlit as st
import pandas as pd
import plotly.express as px

# STEP 2 — Page Config
st.set_page_config(layout="wide")

# FIX: Inject Custom CSS to prevent sidebar dropdown clipping and allow scrolling
st.markdown(
    """
    <style>
    /* Allow the sidebar container to show overflowing dropdown menus */
    [data-testid="stSidebarUserContent"] {
        padding-bottom: 20rem; /* Adds scrollable space at the bottom */
    }
    div[data-baseweb="select"] {
        z-index: 9999 !important; /* Forces the dropdown to stay on top */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title
st.title("Nova Retail Customer Analysis")

# STEP 3 — Load Data
required_columns = [
    'idx', 'label', 'CustomerID', 'TransactionID', 'TransactionDate', 
    'ProductCategory', 'PurchaseAmount', 'CustomerAgeGroup', 
    'CustomerGender', 'CustomerRegion', 'CustomerSatisfaction', 'RetailChannel'
]

df = None
try:
    df = pd.read_excel("NR_dataset.xlsx")
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing logical fields: {missing_columns}")
        st.write("Actual Columns in Dataset:", df.columns.tolist())
        st.stop()
        
    # Consolidate '55-64' age group into '55+' as requested
    df['CustomerAgeGroup'] = df['CustomerAgeGroup'].replace('55-64', '55+')
    
except FileNotFoundError:
    st.error("Dataset file not found in repository.")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
    st.stop()

# Business Insights Section
st.markdown("### Executive Business Insights")
col_ins1, col_ins2, col_ins3 = st.columns(3)

with col_ins1:
    st.info(
        "**1. Growth & Segment Opportunities**\n\n"
        "Customers classified under the **Growth** and **Promising** segments generate the substantial majority "
        "of revenue (exceeding $12,000 combined). Targeted loyalty rewards and upselling strategies within these "
        "high-potential groups represent NovaRetail's strongest expansion path."
    )

with col_ins2:
    st.warning(
        "**2. Early Warning of Decline**\n\n"
        "The **Decline** segment accounts for nearly $3,650 in total spend across 19 transacting accounts. "
        "Marketing initiatives must prioritize immediate re-engagement campaigns and proactive outreach to stabilize "
        "satisfaction and mitigate active churn metrics."
    )

with col_ins3:
    st.success(
        "**3. Channel & Regional Strategy**\n\n"
        "The **Physical Store** channel outpaces Online revenue by over $2,000, driven strongly by high performance "
        "in the **West** and **North** regions. Strengthening omni-channel retail consistency and replicating physical "
        "promotional tactics online can optimize underperforming channels."
    )

st.markdown("---")

# STEP 4 — Sidebar Filters
st.sidebar.header("Dashboard Filters")

def create_sidebar_multiselect(label, options):
    selected = st.sidebar.multiselect(label, options=["All"] + list(options), default=["All"])
    return selected

region_options = df['CustomerRegion'].dropna().unique()
channel_options = df['RetailChannel'].dropna().unique()
category_options = df['ProductCategory'].dropna().unique()
age_options = sorted(df['CustomerAgeGroup'].dropna().unique())

selected_regions = create_sidebar_multiselect("Select Customer Region", region_options)
selected_channels = create_sidebar_multiselect("Select Retail Channel", channel_options)
selected_categories = create_sidebar_multiselect("Select Product Category", category_options)
selected_ages = create_sidebar_multiselect("Select Customer Age Group", age_options)

st.sidebar.markdown("---")
# Dynamic Group By/Legend selection dropdown including Customer Satisfaction
groupby_labels = {
    "Customer Segment": "label",
    "Customer Satisfaction": "CustomerSatisfaction",
    "Product Category": "ProductCategory",
    "Customer Region": "CustomerRegion",
    "Retail Channel": "RetailChannel",
    "Customer Age Group": "CustomerAgeGroup",
    "Customer Gender": "CustomerGender"
}
selected_groupby_label = st.sidebar.selectbox(
    "Select Chart Group By / Legend Variable",
    options=list(groupby_labels.keys()),
    index=0
)
groupby_variable = groupby_labels[selected_groupby_label]

# STEP 5 — Filtering Logic
filtered_df = df.copy()

if "All" not in selected_regions:
    filtered_df = filtered_df[filtered_df['CustomerRegion'].isin(selected_regions)]

if "All" not in selected_channels:
    filtered_df = filtered_df[filtered_df['RetailChannel'].isin(selected_channels)]

if "All" not in selected_categories:
    filtered_df = filtered_df[filtered_df['ProductCategory'].isin(selected_categories)]

if "All" not in selected_ages:
    filtered_df = filtered_df[filtered_df['CustomerAgeGroup'].isin(selected_ages)]

# STEP 9 — Edge Case Handling: Empty filter result
if filtered_df.empty:
    st.warning("No data available matching the selected filter combinations. Please adjust your criteria.")
else:
    # Key Metrics Display
    st.markdown("### Key Performance Indicators")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Purchase Amount", f"${filtered_df['PurchaseAmount'].sum():,.2f}")
    kpi2.metric("Total Transactions", f"{filtered_df['TransactionID'].nunique():,}")
    kpi3.metric("Total Unique Customers", f"{filtered_df['CustomerID'].nunique():,}")
    kpi4.metric("Avg Satisfaction Score", f"{filtered_df['CustomerSatisfaction'].mean():.2f} / 5.0")
    
    st.markdown("---")
    
    # STEP 6 — Aggregation based on the dropdown variable
    agg_df = filtered_df.copy()
    if groupby_variable == 'CustomerSatisfaction':
        agg_df[groupby_variable] = agg_df[groupby_variable].astype(str)
        
    agg_df = agg_df.groupby(groupby_variable)['PurchaseAmount'].sum().reset_index()
    agg_df = agg_df.sort_values(by=groupby_variable)
    
    # STEP 7 — Plot
    fig = px.bar(
        agg_df,
        x=groupby_variable,
        y='PurchaseAmount',
        color=groupby_variable,
        labels={groupby_variable: selected_groupby_label, 'PurchaseAmount': 'Total Purchase Amount ($)'},
        title=f'Total Revenue Generated by {selected_groupby_label}',
        template='plotly_white'
    )
    fig.update_layout(showlegend=True, hovermode='x unified')
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # STEP 8 — Show Filtered Table
    st.markdown("### Filtered Customer Transactions Data Table")
    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)
