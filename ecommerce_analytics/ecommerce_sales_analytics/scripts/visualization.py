# scripts/visualization.py
"""
Data Visualization Module for E-Commerce Sales Analytics
Author: ANGEL-MAVUYANGWA
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import sys
import os
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils import load_config, create_directory, logger


class SalesVisualizer:
    """
    Visualization class for e-commerce sales data
    Creates professional charts and dashboards
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize SalesVisualizer with configuration
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.df = None
        self.delivered_df = None
        self.logger = logging.getLogger(__name__)
        
        # Set style for matplotlib
        style = self.config['visualization']['style']
        plt.style.use(style)
        sns.set_palette(self.config['visualization']['color_palette'])
        
        create_directory("reports/images")
        self.logger.info("SalesVisualizer initialized successfully")
    
    def load_data(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load cleaned data for visualization
        
        Args:
            file_path: Path to cleaned data file
            
        Returns:
            Loaded dataframe
        """
        if file_path is None:
            file_path = self.config['data']['cleaned_path']
        
        try:
            self.df = pd.read_csv(file_path)
            
            # Parse dates
            date_col = self.config['columns']['date']
            if date_col in self.df.columns:
                self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
            
            # Filter delivered orders
            if 'Status_Group' in self.df.columns:
                self.delivered_df = self.df[self.df['Status_Group'] == 'DELIVERED']
            else:
                self.delivered_df = self.df
            
            self.logger.info(f"Data loaded: {self.df.shape[0]} rows")
            return self.df
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise
    
    def create_kpi_dashboard(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Create KPI dashboard with matplotlib
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        self.logger.info("Creating KPI dashboard")
        
        amount_col = self.config['columns']['amount']
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        fig.suptitle('E-Commerce Sales Dashboard - Key Metrics', fontsize=16, fontweight='bold')
        
        # KPI 1: Total Revenue
        total_revenue = self.delivered_df[amount_col].sum() if amount_col in self.delivered_df.columns else 0
        axes[0, 0].text(0.5, 0.5, f'Rs. {total_revenue:,.0f}', 
                        ha='center', va='center', fontsize=20, fontweight='bold')
        axes[0, 0].set_title('Total Revenue', fontsize=12)
        axes[0, 0].axis('off')
        
        # KPI 2: Total Orders
        total_orders = len(self.delivered_df)
        axes[0, 1].text(0.5, 0.5, f'{total_orders:,}', 
                        ha='center', va='center', fontsize=20, fontweight='bold')
        axes[0, 1].set_title('Total Orders', fontsize=12)
        axes[0, 1].axis('off')
        
        # KPI 3: Average Order Value
        avg_order = self.delivered_df[amount_col].mean() if amount_col in self.delivered_df.columns else 0
        axes[0, 2].text(0.5, 0.5, f'Rs. {avg_order:,.0f}', 
                        ha='center', va='center', fontsize=20, fontweight='bold')
        axes[0, 2].set_title('Average Order Value', fontsize=12)
        axes[0, 2].axis('off')
        
        # KPI 4: Delivery Rate
        if 'Status_Group' in self.df.columns:
            delivery_rate = (self.df['Status_Group'] == 'DELIVERED').mean() * 100
        else:
            delivery_rate = 0
        axes[1, 0].text(0.5, 0.5, f'{delivery_rate:.1f}%', 
                        ha='center', va='center', fontsize=20, fontweight='bold')
        axes[1, 0].set_title('Delivery Rate', fontsize=12)
        axes[1, 0].axis('off')
        
        # KPI 5: Unique Products
        unique_products = self.df['SKU'].nunique() if 'SKU' in self.df.columns else 0
        axes[1, 1].text(0.5, 0.5, f'{unique_products:,}', 
                        ha='center', va='center', fontsize=20, fontweight='bold')
        axes[1, 1].set_title('Unique Products', fontsize=12)
        axes[1, 1].axis('off')
        
        # KPI 6: Unique Cities
        unique_cities = self.df['ship-city'].nunique() if 'ship-city' in self.df.columns else 0
        axes[1, 2].text(0.5, 0.5, f'{unique_cities:,}', 
                        ha='center', va='center', fontsize=20, fontweight='bold')
        axes[1, 2].set_title('Cities Served', fontsize=12)
        axes[1, 2].axis('off')
        
        plt.tight_layout()
        
        if save_path:
            dpi = self.config['visualization']['figure_dpi']
            plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"KPI dashboard saved to {save_path}")
        
        return fig
    
    def plot_monthly_sales_trend(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot monthly sales trend
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        self.logger.info("Plotting monthly sales trend")
        
        amount_col = self.config['columns']['amount']
        date_col = self.config['columns']['date']
        
        if date_col not in self.delivered_df.columns:
            self.logger.warning("Date column not available")
            return None
        
        monthly = self.delivered_df.groupby(self.delivered_df[date_col].dt.to_period('M'))[amount_col].sum()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(monthly))
        ax.plot(x, monthly.values, marker='o', linewidth=2, markersize=8, color='#1E3D58')
        ax.fill_between(x, monthly.values, alpha=0.3, color='#1E3D58')
        
        ax.set_title('Monthly Sales Trend', fontsize=14, fontweight='bold')
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Revenue (Rs.)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels([str(m) for m in monthly.index], rotation=45)
        
        # Add value labels
        for i, (idx, revenue) in enumerate(monthly.items()):
            ax.annotate(f'Rs. {revenue:,.0f}', (i, revenue), 
                       textcoords="offset points", xytext=(0, 10), 
                       ha='center', fontsize=9)
        
        plt.tight_layout()
        
        if save_path:
            dpi = self.config['visualization']['figure_dpi']
            plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"Monthly sales trend saved to {save_path}")
        
        return fig
    
    def plot_top_products(self, n: int = 10, save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot top products by revenue
        
        Args:
            n: Number of top products to display
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        self.logger.info(f"Plotting top {n} products")
        
        amount_col = self.config['columns']['amount']
        
        if 'SKU' not in self.delivered_df.columns:
            self.logger.warning("SKU column not available")
            return None
        
        product_revenue = self.delivered_df.groupby('SKU')[amount_col].sum().reset_index()
        product_revenue = product_revenue.nlargest(n, amount_col)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colors = plt.cm.viridis(np.linspace(0, 1, n))
        bars = ax.barh(range(n), product_revenue[amount_col], color=colors)
        
        ax.set_yticks(range(n))
        ax.set_yticklabels(product_revenue['SKU'])
        ax.set_xlabel('Revenue (Rs.)', fontsize=12)
        ax.set_title(f'Top {n} Products by Revenue', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        
        # Add value labels
        for i, (bar, revenue) in enumerate(zip(bars, product_revenue[amount_col])):
            ax.text(bar.get_width() + (bar.get_width() * 0.01), 
                   bar.get_y() + bar.get_height()/2,
                   f'Rs. {revenue:,.0f}', va='center', fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            dpi = self.config['visualization']['figure_dpi']
            plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"Top products chart saved to {save_path}")
        
        return fig
    
    def plot_category_performance(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot category performance
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        self.logger.info("Plotting category performance")
        
        amount_col = self.config['columns']['amount']
        
        if 'Category' not in self.delivered_df.columns:
            self.logger.warning("Category column not available")
            return None
        
        category_revenue = self.delivered_df.groupby('Category')[amount_col].sum().reset_index()
        category_revenue = category_revenue.nlargest(8, amount_col)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Bar chart
        colors = plt.cm.Set3(np.linspace(0, 1, len(category_revenue)))
        bars = ax1.bar(category_revenue['Category'], category_revenue[amount_col], color=colors)
        ax1.set_title('Revenue by Category', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Category', fontsize=10)
        ax1.set_ylabel('Revenue (Rs.)', fontsize=10)
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar, revenue in zip(bars, category_revenue[amount_col]):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (bar.get_height() * 0.01),
                    f'Rs. {revenue:,.0f}', ha='center', va='bottom', fontsize=9)
        
        # Pie chart
        ax2.pie(category_revenue[amount_col], labels=category_revenue['Category'], 
                autopct='%1.1f%%', startangle=90, colors=colors)
        ax2.set_title('Revenue Share by Category', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            dpi = self.config['visualization']['figure_dpi']
            plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"Category performance chart saved to {save_path}")
        
        return fig
    
    def plot_regional_performance(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot regional performance
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        self.logger.info("Plotting regional performance")
        
        amount_col = self.config['columns']['amount']
        n = self.config['analysis']['top_n_states']
        
        if 'ship-state' not in self.delivered_df.columns:
            self.logger.warning("State column not available")
            return None
        
        state_revenue = self.delivered_df.groupby('ship-state')[amount_col].sum().reset_index()
        state_revenue = state_revenue.nlargest(n, amount_col)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(state_revenue)))
        bars = ax.barh(range(len(state_revenue)), state_revenue[amount_col], color=colors)
        
        ax.set_yticks(range(len(state_revenue)))
        ax.set_yticklabels(state_revenue['ship-state'])
        ax.set_xlabel('Revenue (Rs.)', fontsize=12)
        ax.set_title(f'Top {n} States by Revenue', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        
        # Add value labels
        for i, (bar, revenue) in enumerate(zip(bars, state_revenue[amount_col])):
            ax.text(bar.get_width() + (bar.get_width() * 0.01), 
                   bar.get_y() + bar.get_height()/2,
                   f'Rs. {revenue:,.0f}', va='center', fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            dpi = self.config['visualization']['figure_dpi']
            plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"Regional performance chart saved to {save_path}")
        
        return fig
    
    def plot_order_status_distribution(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot order status distribution
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        self.logger.info("Plotting order status distribution")
        
        if 'Status_Group' not in self.df.columns:
            self.logger.warning("Status_Group column not available")
            return None
        
        status_counts = self.df['Status_Group'].value_counts()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        colors_status = []
        color_map = {
            'DELIVERED': '#2ecc71',
            'CANCELLED': '#e74c3c',
            'SHIPPED': '#3498db',
            'RETURNED': '#f39c12',
            'PENDING': '#95a5a6'
        }
        
        for status in status_counts.index:
            colors_status.append(color_map.get(status, '#bdc3c7'))
        
        # Bar chart
        bars = ax1.bar(status_counts.index, status_counts.values, color=colors_status)
        ax1.set_title('Order Status Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Status', fontsize=10)
        ax1.set_ylabel('Number of Orders', fontsize=10)
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar, count in zip(bars, status_counts.values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (bar.get_height() * 0.01),
                    f'{count:,}', ha='center', va='bottom', fontsize=10)
        
        # Pie chart
        ax2.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%',
                startangle=90, colors=colors_status)
        ax2.set_title('Order Status Share', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            dpi = self.config['visualization']['figure_dpi']
            plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"Order status chart saved to {save_path}")
        
        return fig
    
    def plot_weekday_sales(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot sales by day of week
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        self.logger.info("Plotting weekday sales analysis")
        
        amount_col = self.config['columns']['amount']
        date_col = self.config['columns']['date']
        
        if date_col not in self.delivered_df.columns:
            self.logger.warning("Date column not available")
            return None
        
        self.delivered_df['Weekday'] = self.delivered_df[date_col].dt.day_name()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_sales = self.delivered_df.groupby('Weekday')[amount_col].sum().reindex(weekday_order)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colors = plt.cm.viridis(np.linspace(0, 1, 7))
        bars = ax.bar(weekday_sales.index, weekday_sales.values, color=colors)
        
        ax.set_title('Sales by Day of Week', fontsize=14, fontweight='bold')
        ax.set_xlabel('Day', fontsize=12)
        ax.set_ylabel('Revenue (Rs.)', fontsize=12)
        
        # Add value labels
        for bar, revenue in zip(bars, weekday_sales.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (bar.get_height() * 0.01),
                   f'Rs. {revenue:,.0f}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        if save_path:
            dpi = self.config['visualization']['figure_dpi']
            plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"Weekday sales chart saved to {save_path}")
        
        return fig
    
    def plot_price_distribution(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot price distribution
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        self.logger.info("Plotting price distribution")
        
        amount_col = self.config['columns']['amount']
        
        if amount_col not in self.df.columns:
            self.logger.warning("Amount column not available")
            return None
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Histogram
        ax1.hist(self.df[amount_col], bins=50, edgecolor='black', alpha=0.7, color='steelblue')
        ax1.axvline(self.df[amount_col].mean(), color='red', linestyle='--', 
                   label=f'Mean: Rs. {self.df[amount_col].mean():,.0f}')
        ax1.axvline(self.df[amount_col].median(), color='green', linestyle='--', 
                   label=f'Median: Rs. {self.df[amount_col].median():,.0f}')
        ax1.set_title('Order Value Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Order Value (Rs.)', fontsize=10)
        ax1.set_ylabel('Frequency', fontsize=10)
        ax1.legend()
        
        # Box plot
        ax2.boxplot(self.df[amount_col], vert=True)
        ax2.set_title('Order Value Box Plot', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Order Value (Rs.)', fontsize=10)
        ax2.set_xticklabels(['All Orders'])
        
        plt.tight_layout()
        
        if save_path:
            dpi = self.config['visualization']['figure_dpi']
            plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"Price distribution chart saved to {save_path}")
        
        return fig
    
    def plot_fulfillment_analysis(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Plot fulfillment method analysis
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        self.logger.info("Plotting fulfillment analysis")
        
        amount_col = self.config['columns']['amount']
        
        if 'Fulfilment' not in self.delivered_df.columns:
            self.logger.warning("Fulfilment column not available")
            return None
        
        fulfillment_revenue = self.delivered_df.groupby('Fulfilment')[amount_col].sum()
        
        fig, ax = plt.subplots(figsize=(8, 8))
        
        colors = plt.cm.Set2(np.linspace(0, 1, len(fulfillment_revenue)))
        ax.pie(fulfillment_revenue.values, labels=fulfillment_revenue.index, 
               autopct='%1.1f%%', startangle=90, colors=colors)
        ax.set_title('Revenue by Fulfillment Method', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            dpi = self.config['visualization']['figure_dpi']
            plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"Fulfillment analysis chart saved to {save_path}")
        
        return fig
    
    def create_interactive_dashboard(self, save_path: Optional[str] = None) -> None:
        """
        Create interactive Plotly dashboard and save as HTML
        
        Args:
            save_path: Path to save the HTML file
        """
        self.logger.info("Creating interactive dashboard")
        
        amount_col = self.config['columns']['amount']
        date_col = self.config['columns']['date']
        
        # Monthly sales line chart
        if date_col in self.delivered_df.columns:
            monthly = self.delivered_df.groupby(self.delivered_df[date_col].dt.to_period('M'))[amount_col].sum().reset_index()
            monthly[date_col] = monthly[date_col].astype(str)
            
            fig1 = px.line(monthly, x=date_col, y=amount_col, 
                          title='Monthly Sales Trend',
                          labels={date_col: 'Month', amount_col: 'Revenue (Rs.)'},
                          markers=True)
            fig1.update_traces(line=dict(width=3), marker=dict(size=8))
        else:
            fig1 = None
        
        # Top products bar chart
        if 'SKU' in self.delivered_df.columns:
            product_revenue = self.delivered_df.groupby('SKU')[amount_col].sum().reset_index()
            top_products = product_revenue.nlargest(10, amount_col)
            
            fig2 = px.bar(top_products, x=amount_col, y='SKU', orientation='h',
                         title='Top 10 Products by Revenue',
                         labels={amount_col: 'Revenue (Rs.)', 'SKU': 'Product'},
                         color=amount_col, color_continuous_scale='Viridis')
        else:
            fig2 = None
        
        # Category pie chart
        if 'Category' in self.delivered_df.columns:
            category_revenue = self.delivered_df.groupby('Category')[amount_col].sum().reset_index()
            
            fig3 = px.pie(category_revenue, values=amount_col, names='Category',
                         title='Revenue Share by Category', hole=0.3)
        else:
            fig3 = None
        
        # Regional performance
        if 'ship-state' in self.delivered_df.columns:
            state_revenue = self.delivered_df.groupby('ship-state')[amount_col].sum().reset_index()
            top_states = state_revenue.nlargest(10, amount_col)
            
            fig4 = px.bar(top_states, x=amount_col, y='ship-state', orientation='h',
                         title='Top 10 States by Revenue',
                         labels={amount_col: 'Revenue (Rs.)', 'ship-state': 'State'},
                         color=amount_col, color_continuous_scale='RdYlGn')
        else:
            fig4 = None
        
        # Status distribution
        if 'Status_Group' in self.df.columns:
            status_counts = self.df['Status_Group'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            fig5 = px.pie(status_counts, values='Count', names='Status',
                         title='Order Status Distribution', hole=0.3)
        else:
            fig5 = None
        
        # Combine figures into HTML
        if save_path:
            with open(save_path, 'w') as f:
                f.write("<html><head><title>E-Commerce Sales Dashboard</title>")
                f.write("<style>body { font-family: Arial, sans-serif; margin: 20px; } ")
                f.write("h1 { color: #1E3D58; text-align: center; } ")
                f.write(".chart { margin: 20px 0; }</style></head><body>")
                f.write("<h1>E-Commerce Sales Analytics Dashboard</h1>")
                
                if fig1:
                    f.write("<div class='chart'>")
                    f.write(fig1.to_html(full_html=False))
                    f.write("</div>")
                
                if fig2:
                    f.write("<div class='chart'>")
                    f.write(fig2.to_html(full_html=False))
                    f.write("</div>")
                
                if fig3:
                    f.write("<div class='chart'>")
                    f.write(fig3.to_html(full_html=False))
                    f.write("</div>")
                
                if fig4:
                    f.write("<div class='chart'>")
                    f.write(fig4.to_html(full_html=False))
                    f.write("</div>")
                
                if fig5:
                    f.write("<div class='chart'>")
                    f.write(fig5.to_html(full_html=False))
                    f.write("</div>")
                
                f.write("</body></html>")
            
            self.logger.info(f"Interactive dashboard saved to {save_path}")
    
    def create_comprehensive_dashboard(self, save_path: Optional[str] = None) -> plt.Figure:
        """
        Create comprehensive matplotlib dashboard
        
        Args:
            save_path: Path to save the figure
            
        Returns:
            Matplotlib figure object
        """
        self.logger.info("Creating comprehensive dashboard")
        
        amount_col = self.config['columns']['amount']
        date_col = self.config['columns']['date']
        
        fig = plt.figure(figsize=(20, 14))
        fig.suptitle('E-Commerce Sales Analytics Dashboard', fontsize=16, fontweight='bold')
        
        # Create grid
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Monthly Sales Trend
        ax1 = fig.add_subplot(gs[0, :2])
        if date_col in self.delivered_df.columns:
            monthly = self.delivered_df.groupby(self.delivered_df[date_col].dt.to_period('M'))[amount_col].sum()
            x = range(len(monthly))
            ax1.plot(x, monthly.values, marker='o', linewidth=2, markersize=6, color='#1E3D58')
            ax1.fill_between(x, monthly.values, alpha=0.3, color='#1E3D58')
            ax1.set_title('Monthly Sales Trend', fontsize=12, fontweight='bold')
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Revenue (Rs.)')
            ax1.set_xticks(x)
            ax1.set_xticklabels([str(m) for m in monthly.index], rotation=45)
        
        # 2. Top Categories
        ax2 = fig.add_subplot(gs[0, 2])
        if 'Category' in self.delivered_df.columns:
            category_revenue = self.delivered_df.groupby('Category')[amount_col].sum().nlargest(6)
            colors = plt.cm.Set3(np.linspace(0, 1, len(category_revenue)))
            ax2.pie(category_revenue.values, labels=category_revenue.index, 
                    autopct='%1.1f%%', colors=colors)
            ax2.set_title('Top Categories', fontsize=12, fontweight='bold')
        
        # 3. Order Status
        ax3 = fig.add_subplot(gs[1, 0])
        if 'Status_Group' in self.df.columns:
            status_counts = self.df['Status_Group'].value_counts()
            color_map = {'DELIVERED': '#2ecc71', 'CANCELLED': '#e74c3c', 
                        'SHIPPED': '#3498db', 'RETURNED': '#f39c12'}
            colors = [color_map.get(s, '#95a5a6') for s in status_counts.index]
            ax3.bar(status_counts.index, status_counts.values, color=colors)
            ax3.set_title('Order Status Distribution', fontsize=12, fontweight='bold')
            ax3.set_xlabel('Status')
            ax3.set_ylabel('Count')
            ax3.tick_params(axis='x', rotation=45)
        
        # 4. Weekly Sales
        ax4 = fig.add_subplot(gs[1, 1])
        if date_col in self.delivered_df.columns:
            self.delivered_df['Weekday'] = self.delivered_df[date_col].dt.day_name()
            weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekday_sales = self.delivered_df.groupby('Weekday')[amount_col].sum().reindex(weekday_order)
            colors = plt.cm.viridis(np.linspace(0, 1, 7))
            ax4.bar(weekday_sales.index, weekday_sales.values, color=colors)
            ax4.set_title('Sales by Day of Week', fontsize=12, fontweight='bold')
            ax4.set_xlabel('Day')
            ax4.set_ylabel('Revenue (Rs.)')
            ax4.tick_params(axis='x', rotation=45)
        
        # 5. Top States
        ax5 = fig.add_subplot(gs[1, 2])
        if 'ship-state' in self.delivered_df.columns:
            state_revenue = self.delivered_df.groupby('ship-state')[amount_col].sum().nlargest(8)
            colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(state_revenue)))
            ax5.barh(range(len(state_revenue)), state_revenue.values, color=colors)
            ax5.set_yticks(range(len(state_revenue)))
            ax5.set_yticklabels(state_revenue.index)
            ax5.set_title('Top States by Revenue', fontsize=12, fontweight='bold')
            ax5.set_xlabel('Revenue (Rs.)')
            ax5.invert_yaxis()
        
        # 6. Price Distribution
        ax6 = fig.add_subplot(gs[2, :])
        if amount_col in self.df.columns:
            ax6.hist(self.df[amount_col], bins=50, edgecolor='black', alpha=0.7, color='steelblue')
            ax6.axvline(self.df[amount_col].mean(), color='red', linestyle='--', 
                       label=f'Mean: Rs. {self.df[amount_col].mean():,.0f}')
            ax6.axvline(self.df[amount_col].median(), color='green', linestyle='--', 
                       label=f'Median: Rs. {self.df[amount_col].median():,.0f}')
            ax6.set_title('Order Value Distribution', fontsize=12, fontweight='bold')
            ax6.set_xlabel('Order Value (Rs.)')
            ax6.set_ylabel('Frequency')
            ax6.legend()
        
        plt.tight_layout()
        
        if save_path:
            dpi = self.config['visualization']['figure_dpi']
            plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"Comprehensive dashboard saved to {save_path}")
        
        return fig
    
    def generate_all_visualizations(self, output_dir: str = "reports/images") -> None:
        """
        Generate all visualizations and save to output directory
        
        Args:
            output_dir: Directory to save visualizations
        """
        create_directory(output_dir)
        
        self.create_kpi_dashboard(f"{output_dir}/kpi_dashboard.png")
        self.plot_monthly_sales_trend(f"{output_dir}/monthly_sales_trend.png")
        self.plot_top_products(save_path=f"{output_dir}/top_products.png")
        self.plot_category_performance(f"{output_dir}/category_performance.png")
        self.plot_regional_performance(f"{output_dir}/regional_performance.png")
        self.plot_order_status_distribution(f"{output_dir}/order_status.png")
        self.plot_weekday_sales(f"{output_dir}/weekday_sales.png")
        self.plot_price_distribution(f"{output_dir}/price_distribution.png")
        self.plot_fulfillment_analysis(f"{output_dir}/fulfillment_analysis.png")
        self.create_comprehensive_dashboard(f"{output_dir}/comprehensive_dashboard.png")
        self.create_interactive_dashboard(f"{output_dir}/interactive_dashboard.html")
        
        self.logger.info(f"All visualizations saved to {output_dir}")


def main():
    """
    Main execution function
    """
    visualizer = SalesVisualizer()
    visualizer.load_data()
    visualizer.generate_all_visualizations()
    
    print("\nVisualization generation completed successfully! - visualization.py:778")
    print("Check the 'reports/images' directory for output files. - visualization.py:779")


if __name__ == "__main__":
    main()