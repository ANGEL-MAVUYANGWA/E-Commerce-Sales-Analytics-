# dashboard/app.py
"""
Streamlit Dashboard for E-Commerce Sales Analytics
Author: ANGEL-MAVUYANGWA
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils import load_config

# Page configuration
st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration
config = load_config()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1E3D58;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E3D58;
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #666;
    }
    .insight-box {
        background-color: #e8f4f8;
        border-left: 4px solid #1E3D58;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Load and cache the cleaned data"""
    file_path = config['data']['cleaned_path']
    df = pd.read_csv(file_path)
    
    # Parse dates
    date_col = config['columns']['date']
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    return df


@st.cache_data
def filter_data(df, date_range, status_filter, category_filter, state_filter):
    """Apply filters to the data"""
    filtered_df = df.copy()
    
    # Date filter
    if date_range and len(date_range) == 2 and 'Date' in filtered_df.columns:
        mask = (filtered_df['Date'] >= pd.to_datetime(date_range[0])) & \
               (filtered_df['Date'] <= pd.to_datetime(date_range[1]))
        filtered_df = filtered_df[mask]
    
    # Status filter
    if status_filter and status_filter != 'All' and 'Status_Group' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Status_Group'] == status_filter]
    
    # Category filter
    if category_filter and category_filter != 'All' and 'Category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Category'] == category_filter]
    
    # State filter
    if state_filter and state_filter != 'All' and 'ship-state' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['ship-state'] == state_filter]
    
    return filtered_df


def create_kpi_row(df):
    """Create KPI metrics row"""
    amount_col = config['columns']['amount']
    
    # Filter delivered orders for revenue metrics
    delivered_df = df[df['Status_Group'] == 'DELIVERED'] if 'Status_Group' in df.columns else df
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_revenue = delivered_df[amount_col].sum() if amount_col in delivered_df.columns else 0
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">Rs. {total_revenue:,.0f}</div>
            <div class="kpi-label">Total Revenue</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_orders = len(delivered_df)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{total_orders:,}</div>
            <div class="kpi-label">Total Orders</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_order = delivered_df[amount_col].mean() if amount_col in delivered_df.columns else 0
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">Rs. {avg_order:,.0f}</div>
            <div class="kpi-label">Avg Order Value</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        unique_products = df['SKU'].nunique() if 'SKU' in df.columns else 0
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{unique_products:,}</div>
            <div class="kpi-label">Unique Products</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        delivery_rate = (df['Status_Group'] == 'DELIVERED').mean() * 100 if 'Status_Group' in df.columns else 0
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{delivery_rate:.1f}%</div>
            <div class="kpi-label">Delivery Rate</div>
        </div>
        """, unsafe_allow_html=True)


def create_monthly_trend_chart(df):
    """Create monthly sales trend chart"""
    amount_col = config['columns']['amount']
    date_col = config['columns']['date']
    
    if date_col not in df.columns or amount_col not in df.columns:
        st.info("Date or Amount column not available for trend analysis")
        return
    
    delivered_df = df[df['Status_Group'] == 'DELIVERED'] if 'Status_Group' in df.columns else df
    
    monthly = delivered_df.groupby(delivered_df[date_col].dt.to_period('M'))[amount_col].sum().reset_index()
    monthly[date_col] = monthly[date_col].astype(str)
    
    fig = px.line(
        monthly, 
        x=date_col, 
        y=amount_col,
        title='Monthly Revenue Trend',
        labels={date_col: 'Month', amount_col: 'Revenue (Rs.)'},
        markers=True
    )
    
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_layout(height=400, hovermode='x unified')
    
    st.plotly_chart(fig, use_container_width=True)


def create_category_pie_chart(df):
    """Create category revenue pie chart"""
    amount_col = config['columns']['amount']
    
    delivered_df = df[df['Status_Group'] == 'DELIVERED'] if 'Status_Group' in df.columns else df
    
    if 'Category' not in delivered_df.columns or amount_col not in delivered_df.columns:
        st.info("Category data not available")
        return
    
    category_revenue = delivered_df.groupby('Category')[amount_col].sum().reset_index()
    category_revenue = category_revenue.nlargest(8, amount_col)
    
    fig = px.pie(
        category_revenue,
        values=amount_col,
        names='Category',
        title='Revenue Share by Category',
        hole=0.3
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def create_top_products_chart(df):
    """Create top products bar chart"""
    amount_col = config['columns']['amount']
    top_n = config['analysis']['top_n_products']
    
    delivered_df = df[df['Status_Group'] == 'DELIVERED'] if 'Status_Group' in df.columns else df
    
    if 'SKU' not in delivered_df.columns or amount_col not in delivered_df.columns:
        st.info("Product data not available")
        return
    
    product_revenue = delivered_df.groupby('SKU')[amount_col].sum().reset_index()
    top_products = product_revenue.nlargest(top_n, amount_col)
    
    fig = px.bar(
        top_products,
        x=amount_col,
        y='SKU',
        orientation='h',
        title=f'Top {top_n} Products by Revenue',
        labels={amount_col: 'Revenue (Rs.)', 'SKU': 'Product'},
        color=amount_col,
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)


def create_regional_chart(df):
    """Create regional performance chart"""
    amount_col = config['columns']['amount']
    top_n = config['analysis']['top_n_states']
    
    delivered_df = df[df['Status_Group'] == 'DELIVERED'] if 'Status_Group' in df.columns else df
    
    if 'ship-state' not in delivered_df.columns or amount_col not in delivered_df.columns:
        st.info("Regional data not available")
        return
    
    state_revenue = delivered_df.groupby('ship-state')[amount_col].sum().reset_index()
    top_states = state_revenue.nlargest(top_n, amount_col)
    
    fig = px.bar(
        top_states,
        x=amount_col,
        y='ship-state',
        orientation='h',
        title=f'Top {top_n} States by Revenue',
        labels={amount_col: 'Revenue (Rs.)', 'ship-state': 'State'},
        color=amount_col,
        color_continuous_scale='RdYlGn'
    )
    
    fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)


def create_status_chart(df):
    """Create order status distribution chart"""
    if 'Status_Group' not in df.columns:
        st.info("Status data not available")
        return
    
    status_counts = df['Status_Group'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    color_map = {
        'DELIVERED': '#2ecc71',
        'CANCELLED': '#e74c3c',
        'SHIPPED': '#3498db',
        'RETURNED': '#f39c12',
        'PENDING': '#95a5a6',
        'LOST': '#7f8c8d',
        'REJECTED': '#e67e22',
        'OTHER': '#bdc3c7'
    }
    
    fig = px.pie(
        status_counts,
        values='Count',
        names='Status',
        title='Order Status Distribution',
        color='Status',
        color_discrete_map=color_map,
        hole=0.3
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def create_weekday_chart(df):
    """Create weekday sales analysis chart"""
    amount_col = config['columns']['amount']
    date_col = config['columns']['date']
    
    if date_col not in df.columns or amount_col not in df.columns:
        st.info("Date data not available")
        return
    
    delivered_df = df[df['Status_Group'] == 'DELIVERED'] if 'Status_Group' in df.columns else df
    
    delivered_df['Weekday'] = delivered_df[date_col].dt.day_name()
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_sales = delivered_df.groupby('Weekday')[amount_col].sum().reindex(weekday_order).reset_index()
    weekday_sales.columns = ['Day', 'Revenue']
    
    fig = px.bar(
        weekday_sales,
        x='Day',
        y='Revenue',
        title='Revenue by Day of Week',
        labels={'Day': 'Day of Week', 'Revenue': 'Revenue (Rs.)'},
        color='Revenue',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def create_price_distribution_chart(df):
    """Create price distribution histogram"""
    amount_col = config['columns']['amount']
    
    if amount_col not in df.columns:
        st.info("Amount data not available")
        return
    
    fig = px.histogram(
        df,
        x=amount_col,
        nbins=50,
        title='Order Value Distribution',
        labels={amount_col: 'Order Value (Rs.)'},
        color_discrete_sequence=['steelblue']
    )
    
    # Add mean and median lines
    mean_val = df[amount_col].mean()
    median_val = df[amount_col].median()
    
    fig.add_vline(
        x=mean_val, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"Mean: Rs. {mean_val:.0f}"
    )
    fig.add_vline(
        x=median_val, 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"Median: Rs. {median_val:.0f}"
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def create_fulfillment_chart(df):
    """Create fulfillment method analysis chart"""
    amount_col = config['columns']['amount']
    
    delivered_df = df[df['Status_Group'] == 'DELIVERED'] if 'Status_Group' in df.columns else df
    
    if 'Fulfilment' not in delivered_df.columns or amount_col not in delivered_df.columns:
        st.info("Fulfillment data not available")
        return
    
    fulfillment_revenue = delivered_df.groupby('Fulfilment')[amount_col].sum().reset_index()
    
    fig = px.pie(
        fulfillment_revenue,
        values=amount_col,
        names='Fulfilment',
        title='Revenue by Fulfillment Method',
        hole=0.3
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def create_insight_box(insights):
    """Create insight box for key findings"""
    st.markdown('<div class="insight-box">', unsafe_allow_html=True)
    st.markdown("### Key Business Insights")
    
    for insight in insights:
        st.markdown(f"- {insight}")
    
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main dashboard application"""
    
    # Header
    st.markdown('<div class="main-header">E-Commerce Sales Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comprehensive Sales Performance Analysis</div>', unsafe_allow_html=True)
    
    # Load data
    try:
        df = load_data()
        st.sidebar.success(f"Data loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()
    
    # Sidebar filters
    st.sidebar.markdown("## Filters")
    st.sidebar.markdown("---")
    
    # Date range filter
    date_col = config['columns']['date']
    if date_col in df.columns and not df[date_col].isnull().all():
        min_date = df[date_col].min().date()
        max_date = df[date_col].max().date()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
    else:
        date_range = []
    
    # Status filter
    if 'Status_Group' in df.columns:
        status_options = ['All'] + sorted(df['Status_Group'].unique().tolist())
        status_filter = st.sidebar.selectbox("Order Status", status_options)
    else:
        status_filter = 'All'
    
    # Category filter
    if 'Category' in df.columns:
        category_options = ['All'] + sorted(df['Category'].unique().tolist())
        category_filter = st.sidebar.selectbox("Category", category_options)
    else:
        category_filter = 'All'
    
    # State filter
    if 'ship-state' in df.columns:
        state_options = ['All'] + sorted(df['ship-state'].unique().tolist())
        state_filter = st.sidebar.selectbox("State", state_options)
    else:
        state_filter = 'All'
    
    # Apply filters
    filtered_df = filter_data(df, date_range, status_filter, category_filter, state_filter)
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        """
        **Dashboard Features:**
        - Real-time KPI tracking
        - Sales trend analysis
        - Product performance
        - Regional insights
        - Operational metrics
        """
    )
    
    # KPI Row
    create_kpi_row(filtered_df)
    
    st.markdown("---")
    
    # Row 1: Sales Trend and Category Performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Revenue Trend")
        create_monthly_trend_chart(filtered_df)
    
    with col2:
        st.subheader("Category Performance")
        create_category_pie_chart(filtered_df)
    
    st.markdown("---")
    
    # Row 2: Top Products and Regional Performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Products")
        create_top_products_chart(filtered_df)
    
    with col2:
        st.subheader("Regional Performance")
        create_regional_chart(filtered_df)
    
    st.markdown("---")
    
    # Row 3: Order Status and Weekday Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Order Status Distribution")
        create_status_chart(filtered_df)
    
    with col2:
        st.subheader("Weekly Sales Pattern")
        create_weekday_chart(filtered_df)
    
    st.markdown("---")
    
    # Row 4: Price Distribution and Fulfillment Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Price Distribution")
        create_price_distribution_chart(filtered_df)
    
    with col2:
        st.subheader("Fulfillment Method")
        create_fulfillment_chart(filtered_df)
    
    st.markdown("---")
    
    # Key Insights
    insights = [
        f"Total revenue achieved: Rs. {filtered_df[filtered_df['Status_Group'] == 'DELIVERED'][config['columns']['amount']].sum():,.2f}",
        f"Average order value: Rs. {filtered_df[filtered_df['Status_Group'] == 'DELIVERED'][config['columns']['amount']].mean():,.2f}",
        f"Delivery success rate: {(filtered_df['Status_Group'] == 'DELIVERED').mean() * 100:.1f}%",
        f"Unique products sold: {filtered_df['SKU'].nunique():,}",
        f"Geographic reach: {filtered_df['ship-state'].nunique()} states, {filtered_df['ship-city'].nunique()} cities"
    ]
    
    create_insight_box(insights)
    
    # Data preview
    st.markdown("---")
    st.subheader("Data Preview")
    st.dataframe(filtered_df.head(100), use_container_width=True)
    
    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data (CSV)",
        data=csv,
        file_name=f"sales_data_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
    
    # Footer
    st.markdown("---")
    st.caption(f"Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()