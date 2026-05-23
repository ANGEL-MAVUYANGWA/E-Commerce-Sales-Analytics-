# scripts/data_analysis.py
"""
Data Analysis Module for E-Commerce Sales Analytics
Author: ANGEL-MAVUYANGWA
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils import load_config, create_directory, logger


class SalesAnalyzer:
    """
    Sales analysis class for e-commerce data
    Performs comprehensive business analysis and KPI calculation
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize SalesAnalyzer with configuration
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.df = None
        self.delivered_df = None
        self.analysis_results = {}
        self.logger = logging.getLogger(__name__)
        
        create_directory("reports")
        self.logger.info("SalesAnalyzer initialized successfully")
    
    def load_data(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load cleaned data for analysis
        
        Args:
            file_path: Path to cleaned data file
            
        Returns:
            Loaded dataframe
        """
        if file_path is None:
            file_path = self.config['data']['cleaned_path']
        
        try:
            self.df = pd.read_csv(file_path)
            
            # Parse dates if present
            date_col = self.config['columns']['date']
            if date_col in self.df.columns:
                self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
            
            # Filter delivered orders for revenue calculations
            if 'Status_Group' in self.df.columns:
                self.delivered_df = self.df[self.df['Status_Group'] == 'DELIVERED']
            else:
                self.delivered_df = self.df
            
            self.logger.info(f"Data loaded successfully: {self.df.shape[0]} rows, {self.df.shape[1]} columns")
            return self.df
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise
    
    def calculate_kpis(self) -> Dict[str, Any]:
        """
        Calculate key performance indicators
        
        Returns:
            Dictionary with KPI values
        """
        self.logger.info("Calculating KPIs")
        
        amount_col = self.config['columns']['amount']
        qty_col = self.config['columns']['quantity']
        
        kpis = {
            'total_revenue': float(self.delivered_df[amount_col].sum()) if amount_col in self.delivered_df.columns else 0,
            'total_orders': len(self.delivered_df),
            'total_units_sold': float(self.delivered_df[qty_col].sum()) if qty_col in self.delivered_df.columns else 0,
            'average_order_value': float(self.delivered_df[amount_col].mean()) if amount_col in self.delivered_df.columns else 0,
            'median_order_value': float(self.delivered_df[amount_col].median()) if amount_col in self.delivered_df.columns else 0,
            'unique_products': int(self.df['SKU'].nunique()) if 'SKU' in self.df.columns else 0,
            'unique_customers': int(self.df['Order ID'].nunique()) if 'Order ID' in self.df.columns else 0,
            'unique_states': int(self.df['ship-state'].nunique()) if 'ship-state' in self.df.columns else 0,
            'unique_cities': int(self.df['ship-city'].nunique()) if 'ship-city' in self.df.columns else 0,
            'delivery_rate': float((self.df['Status_Group'] == 'DELIVERED').mean() * 100) if 'Status_Group' in self.df.columns else 0,
            'cancellation_rate': float((self.df['Status_Group'] == 'CANCELLED').mean() * 100) if 'Status_Group' in self.df.columns else 0,
            'return_rate': float((self.df['Status_Group'] == 'RETURNED').mean() * 100) if 'Status_Group' in self.df.columns else 0,
            'b2b_orders': int(self.df['B2B'].sum()) if 'B2B' in self.df.columns else 0,
            'b2b_revenue': float(self.delivered_df[self.delivered_df['B2B'] == True][amount_col].sum()) if 'B2B' in self.delivered_df.columns and amount_col in self.delivered_df.columns else 0
        }
        
        self.analysis_results['kpis'] = kpis
        return kpis
    
    def analyze_sales_trends(self) -> Dict[str, Any]:
        """
        Analyze sales trends over time
        
        Returns:
            Dictionary with trend analysis results
        """
        self.logger.info("Analyzing sales trends")
        
        amount_col = self.config['columns']['amount']
        date_col = self.config['columns']['date']
        
        if date_col not in self.delivered_df.columns:
            self.logger.warning("Date column not available for trend analysis")
            return {}
        
        trends = {}
        
        # Monthly trends
        monthly = self.delivered_df.groupby(self.delivered_df[date_col].dt.to_period('M'))[amount_col].agg(['sum', 'mean', 'count']).reset_index()
        monthly.columns = ['Period', 'Total_Revenue', 'Avg_Order_Value', 'Order_Count']
        monthly['Period'] = monthly['Period'].astype(str)
        
        trends['monthly'] = monthly.to_dict('records')
        
        if not monthly.empty:
            # Best and worst months
            best_month_idx = monthly['Total_Revenue'].idxmax()
            worst_month_idx = monthly['Total_Revenue'].idxmin()
            
            trends['best_month'] = {
                'period': monthly.loc[best_month_idx, 'Period'],
                'revenue': float(monthly.loc[best_month_idx, 'Total_Revenue']),
                'orders': int(monthly.loc[best_month_idx, 'Order_Count'])
            }
            
            trends['worst_month'] = {
                'period': monthly.loc[worst_month_idx, 'Period'],
                'revenue': float(monthly.loc[worst_month_idx, 'Total_Revenue']),
                'orders': int(monthly.loc[worst_month_idx, 'Order_Count'])
            }
            
            # Month-over-month growth
            monthly['Revenue_Growth'] = monthly['Total_Revenue'].pct_change() * 100
            trends['monthly_growth'] = monthly[['Period', 'Revenue_Growth']].to_dict('records')
        
        # Daily trends (weekday analysis)
        self.delivered_df['Weekday'] = self.delivered_df[date_col].dt.day_name()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_sales = self.delivered_df.groupby('Weekday')[amount_col].agg(['sum', 'mean', 'count']).reindex(weekday_order).reset_index()
        weekday_sales.columns = ['Day', 'Total_Revenue', 'Avg_Order_Value', 'Order_Count']
        
        trends['weekday_analysis'] = weekday_sales.to_dict('records')
        
        if not weekday_sales.empty:
            best_day_idx = weekday_sales['Total_Revenue'].idxmax()
            trends['best_day'] = {
                'day': weekday_sales.loc[best_day_idx, 'Day'],
                'revenue': float(weekday_sales.loc[best_day_idx, 'Total_Revenue'])
            }
        
        # Quarterly trends
        if 'Quarter' in self.delivered_df.columns:
            quarterly = self.delivered_df.groupby('Quarter')[amount_col].sum().reset_index()
            trends['quarterly'] = quarterly.to_dict('records')
        
        self.analysis_results['sales_trends'] = trends
        return trends
    
    def analyze_product_performance(self) -> Dict[str, Any]:
        """
        Analyze product performance metrics
        
        Returns:
            Dictionary with product analysis results
        """
        self.logger.info("Analyzing product performance")
        
        amount_col = self.config['columns']['amount']
        top_n = self.config['analysis']['top_n_products']
        
        performance = {}
        
        # Top products by revenue
        if 'SKU' in self.delivered_df.columns:
            product_revenue = self.delivered_df.groupby('SKU')[amount_col].agg(['sum', 'mean', 'count']).reset_index()
            product_revenue.columns = ['SKU', 'Total_Revenue', 'Avg_Price', 'Units_Sold']
            product_revenue = product_revenue.sort_values('Total_Revenue', ascending=False)
            
            performance['top_products'] = product_revenue.head(top_n).to_dict('records')
            performance['bottom_products'] = product_revenue.tail(top_n).to_dict('records')
            
            # Revenue concentration
            total_revenue = product_revenue['Total_Revenue'].sum()
            top_1_pct = product_revenue.head(int(len(product_revenue) * 0.01))['Total_Revenue'].sum() if len(product_revenue) > 0 else 0
            top_5_pct = product_revenue.head(int(len(product_revenue) * 0.05))['Total_Revenue'].sum() if len(product_revenue) > 0 else 0
            
            performance['revenue_concentration'] = {
                'top_1_percent_share': float(top_1_pct / total_revenue * 100) if total_revenue > 0 else 0,
                'top_5_percent_share': float(top_5_pct / total_revenue * 100) if total_revenue > 0 else 0
            }
        
        # Category performance
        if 'Category' in self.delivered_df.columns:
            category_revenue = self.delivered_df.groupby('Category')[amount_col].sum().reset_index()
            category_revenue = category_revenue.sort_values(amount_col, ascending=False)
            performance['category_performance'] = category_revenue.head(10).to_dict('records')
        
        # Size performance
        if 'Size' in self.delivered_df.columns:
            size_revenue = self.delivered_df.groupby('Size')[amount_col].sum().reset_index()
            size_revenue = size_revenue.sort_values(amount_col, ascending=False)
            performance['size_performance'] = size_revenue.head(10).to_dict('records')
        
        self.analysis_results['product_performance'] = performance
        return performance
    
    def analyze_regional_performance(self) -> Dict[str, Any]:
        """
        Analyze regional sales performance
        
        Returns:
            Dictionary with regional analysis results
        """
        self.logger.info("Analyzing regional performance")
        
        amount_col = self.config['columns']['amount']
        top_n = self.config['analysis']['top_n_states']
        
        performance = {}
        
        # State performance
        if 'ship-state' in self.delivered_df.columns:
            state_revenue = self.delivered_df.groupby('ship-state')[amount_col].agg(['sum', 'mean', 'count']).reset_index()
            state_revenue.columns = ['State', 'Total_Revenue', 'Avg_Order_Value', 'Order_Count']
            state_revenue = state_revenue.sort_values('Total_Revenue', ascending=False)
            
            performance['top_states'] = state_revenue.head(top_n).to_dict('records')
            
            # Revenue concentration
            total_revenue = state_revenue['Total_Revenue'].sum()
            top_3_revenue = state_revenue.head(3)['Total_Revenue'].sum()
            top_5_revenue = state_revenue.head(5)['Total_Revenue'].sum()
            
            performance['state_concentration'] = {
                'top_3_share': float(top_3_revenue / total_revenue * 100) if total_revenue > 0 else 0,
                'top_5_share': float(top_5_revenue / total_revenue * 100) if total_revenue > 0 else 0
            }
        
        # City performance
        if 'ship-city' in self.delivered_df.columns:
            city_revenue = self.delivered_df.groupby('ship-city')[amount_col].sum().reset_index()
            city_revenue = city_revenue.sort_values(amount_col, ascending=False)
            performance['top_cities'] = city_revenue.head(top_n).to_dict('records')
        
        self.analysis_results['regional_performance'] = performance
        return performance
    
    def analyze_operational_metrics(self) -> Dict[str, Any]:
        """
        Analyze operational metrics like fulfillment, shipping, etc.
        
        Returns:
            Dictionary with operational analysis results
        """
        self.logger.info("Analyzing operational metrics")
        
        amount_col = self.config['columns']['amount']
        metrics = {}
        
        # Fulfillment analysis
        if 'Fulfilment' in self.delivered_df.columns:
            fulfillment = self.delivered_df.groupby('Fulfilment')[amount_col].agg(['sum', 'mean', 'count']).reset_index()
            fulfillment.columns = ['Fulfilment_Method', 'Total_Revenue', 'Avg_Order_Value', 'Order_Count']
            metrics['fulfillment_analysis'] = fulfillment.to_dict('records')
        
        # Sales channel analysis
        if 'Sales Channel' in self.delivered_df.columns:
            channel = self.delivered_df.groupby('Sales Channel')[amount_col].agg(['sum', 'mean', 'count']).reset_index()
            channel.columns = ['Sales_Channel', 'Total_Revenue', 'Avg_Order_Value', 'Order_Count']
            metrics['channel_analysis'] = channel.to_dict('records')
        
        # Service level analysis
        if 'ship-service-level' in self.delivered_df.columns:
            service = self.delivered_df.groupby('ship-service-level')[amount_col].agg(['sum', 'mean', 'count']).reset_index()
            service.columns = ['Service_Level', 'Total_Revenue', 'Avg_Order_Value', 'Order_Count']
            metrics['service_level_analysis'] = service.to_dict('records')
        
        self.analysis_results['operational_metrics'] = metrics
        return metrics
    
    def analyze_price_distribution(self) -> Dict[str, Any]:
        """
        Analyze price distribution and brackets
        
        Returns:
            Dictionary with price analysis results
        """
        self.logger.info("Analyzing price distribution")
        
        amount_col = self.config['columns']['amount']
        
        if amount_col not in self.df.columns:
            return {}
        
        distribution = {
            'statistics': {
                'mean': float(self.df[amount_col].mean()),
                'median': float(self.df[amount_col].median()),
                'std': float(self.df[amount_col].std()),
                'min': float(self.df[amount_col].min()),
                'max': float(self.df[amount_col].max()),
                'q1': float(self.df[amount_col].quantile(0.25)),
                'q3': float(self.df[amount_col].quantile(0.75))
            },
            'percentiles': {
                '10th': float(self.df[amount_col].quantile(0.10)),
                '25th': float(self.df[amount_col].quantile(0.25)),
                '50th': float(self.df[amount_col].quantile(0.50)),
                '75th': float(self.df[amount_col].quantile(0.75)),
                '90th': float(self.df[amount_col].quantile(0.90)),
                '95th': float(self.df[amount_col].quantile(0.95)),
                '99th': float(self.df[amount_col].quantile(0.99))
            }
        }
        
        # Price bracket analysis
        if 'Revenue_Category' in self.df.columns:
            bracket_counts = self.df['Revenue_Category'].value_counts()
            distribution['price_brackets'] = {
                str(k): int(v) for k, v in bracket_counts.items()
            }
        
        self.analysis_results['price_distribution'] = distribution
        return distribution
    
    def analyze_correlations(self) -> Dict[str, Any]:
        """
        Analyze correlations between numeric variables
        
        Returns:
            Dictionary with correlation analysis results
        """
        self.logger.info("Analyzing correlations")
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {}
        
        correlation_matrix = self.df[numeric_cols].corr()
        
        # Find strongest correlations
        correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.3:  # Only report meaningful correlations
                    correlations.append({
                        'variable_1': correlation_matrix.columns[i],
                        'variable_2': correlation_matrix.columns[j],
                        'correlation': float(corr_value)
                    })
        
        correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        self.analysis_results['correlations'] = {
            'matrix': correlation_matrix.to_dict(),
            'strong_correlations': correlations[:10]
        }
        
        return self.analysis_results['correlations']
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """
        Run all analysis modules
        
        Returns:
            Dictionary with all analysis results
        """
        self.logger.info("="*60)
        self.logger.info("Starting complete data analysis")
        self.logger.info("="*60)
        
        self.calculate_kpis()
        self.analyze_sales_trends()
        self.analyze_product_performance()
        self.analyze_regional_performance()
        self.analyze_operational_metrics()
        self.analyze_price_distribution()
        self.analyze_correlations()
        
        self.analysis_results['analysis_completed'] = datetime.now().isoformat()
        
        self.logger.info("="*60)
        self.logger.info("Analysis completed successfully")
        self.logger.info("="*60)
        
        return self.analysis_results
    
    def generate_analysis_report(self, output_path: str = "reports/analysis_report.json") -> None:
        """
        Save analysis results to JSON file
        
        Args:
            output_path: Path to save report
        """
        import json
        
        # Convert non-serializable objects
        report_copy = {}
        for key, value in self.analysis_results.items():
            if isinstance(value, (np.int64, np.float64)):
                report_copy[key] = float(value)
            elif isinstance(value, pd.DataFrame):
                report_copy[key] = value.to_dict()
            elif isinstance(value, pd.Series):
                report_copy[key] = value.to_dict()
            else:
                report_copy[key] = value
        
        with open(output_path, 'w') as f:
            json.dump(report_copy, f, indent=2, default=str)
        
        self.logger.info(f"Analysis report saved to {output_path}")
    
    def print_kpi_summary(self) -> None:
        """
        Print KPI summary to console
        """
        if 'kpis' not in self.analysis_results:
            self.calculate_kpis()
        
        kpis = self.analysis_results['kpis']
        
        print("\n - data_analysis.py:442" + "="*60)
        print("KEY PERFORMANCE INDICATORS (KPIs) - data_analysis.py:443")
        print("= - data_analysis.py:444"*60)
        print(f"Total Revenue:             Rs. {kpis['total_revenue']:,.2f} - data_analysis.py:445")
        print(f"Total Orders:              {kpis['total_orders']:,} - data_analysis.py:446")
        print(f"Total Units Sold:          {kpis['total_units_sold']:,} - data_analysis.py:447")
        print(f"Average Order Value:       Rs. {kpis['average_order_value']:.2f} - data_analysis.py:448")
        print(f"Median Order Value:        Rs. {kpis['median_order_value']:.2f} - data_analysis.py:449")
        print(f"Unique Products:           {kpis['unique_products']:,} - data_analysis.py:450")
        print(f"Unique Customers:          {kpis['unique_customers']:,} - data_analysis.py:451")
        print(f"Unique States:             {kpis['unique_states']:,} - data_analysis.py:452")
        print(f"Unique Cities:             {kpis['unique_cities']:,} - data_analysis.py:453")
        print(f"Delivery Rate:             {kpis['delivery_rate']:.1f}% - data_analysis.py:454")
        print(f"Cancellation Rate:         {kpis['cancellation_rate']:.1f}% - data_analysis.py:455")
        print(f"Return Rate:               {kpis['return_rate']:.1f}% - data_analysis.py:456")
        print(f"B2B Orders:                {kpis['b2b_orders']:,} - data_analysis.py:457")
        print(f"B2B Revenue:               Rs. {kpis['b2b_revenue']:,.2f} - data_analysis.py:458")
    
    def print_trend_summary(self) -> None:
        """
        Print trend analysis summary to console
        """
        if 'sales_trends' not in self.analysis_results:
            self.analyze_sales_trends()
        
        trends = self.analysis_results.get('sales_trends', {})
        
        print("\n - data_analysis.py:469" + "="*60)
        print("SALES TREND ANALYSIS - data_analysis.py:470")
        print("= - data_analysis.py:471"*60)
        
        if not trends or not isinstance(trends, dict):
            print("\nNo trend data available (date column may be missing) - data_analysis.py:474")
            print("This occurs when the 'Date' column is not present in the dataset - data_analysis.py:475")
            return
        
        if 'best_month' in trends and trends['best_month']:
            print(f"Best Month: {trends['best_month']['period']}  Revenue: Rs. {trends['best_month']['revenue']:,.2f} - data_analysis.py:479")
        else:
            print("\nMonthly trend data not available - data_analysis.py:481")
        
        if 'best_day' in trends and trends['best_day']:
            print(f"Best Day: {trends['best_day']['day']}  Revenue: Rs. {trends['best_day']['revenue']:,.2f} - data_analysis.py:484")
        else:
            print("Daily trend data not available - data_analysis.py:486")
        
        if 'monthly_growth' in trends and trends['monthly_growth'] and len(trends['monthly_growth']) > 1:
            try:
                valid_growth = [g for g in trends['monthly_growth'] if g.get('Revenue_Growth') is not None]
                if valid_growth:
                    latest_growth = valid_growth[-1]['Revenue_Growth']
                    print(f"Latest MonthoverMonth Growth: {latest_growth:.1f}% - data_analysis.py:493")
            except (KeyError, IndexError, TypeError):
                pass
    
    def print_product_summary(self) -> None:
        """
        Print product performance summary to console
        """
        if 'product_performance' not in self.analysis_results:
            self.analyze_product_performance()
        
        products = self.analysis_results['product_performance']
        
        print("\n - data_analysis.py:506" + "="*60)
        print("TOP PRODUCTS BY REVENUE - data_analysis.py:507")
        print("= - data_analysis.py:508"*60)
        
        if 'top_products' in products:
            for i, product in enumerate(products['top_products'][:5], 1):
                print(f"{i}. {product['SKU']}  Rs. {product['Total_Revenue']:,.2f} ({product['Units_Sold']} units) - data_analysis.py:512")
        
        if 'category_performance' in products:
            print("\nTOP CATEGORIES BY REVENUE - data_analysis.py:515")
            print(""*40)
            for category in products['category_performance'][:5]:
                print(f"{category['Category']}: Rs. {category[self.config['columns']['amount']]:,.2f} - data_analysis.py:518")
        
        if 'size_performance' in products:
            print("\nTOP SIZES BY REVENUE - data_analysis.py:521")
            print(""*40)
            for size in products['size_performance'][:5]:
                print(f"Size {size['Size']}: Rs. {size[self.config['columns']['amount']]:,.2f} - data_analysis.py:524")
    
    def print_regional_summary(self) -> None:
        """
        Print regional performance summary to console
        """
        if 'regional_performance' not in self.analysis_results:
            self.analyze_regional_performance()
        
        regions = self.analysis_results['regional_performance']
        
        print("\n - data_analysis.py:535" + "="*60)
        print("TOP STATES BY REVENUE - data_analysis.py:536")
        print("= - data_analysis.py:537"*60)
        
        if 'top_states' in regions:
            for i, state in enumerate(regions['top_states'][:5], 1):
                print(f"{i}. {state['State']}  Rs. {state['Total_Revenue']:,.2f} ({state['Order_Count']} orders) - data_analysis.py:541")
        
        if 'state_concentration' in regions:
            print(f"\nTop 3 States contribute: {regions['state_concentration']['top_3_share']:.1f}% of revenue - data_analysis.py:544")
            print(f"Top 5 States contribute: {regions['state_concentration']['top_5_share']:.1f}% of revenue - data_analysis.py:545")


def main():
    """
    Main execution function
    """
    analyzer = SalesAnalyzer()
    
    # Load data
    analyzer.load_data()
    
    # Run complete analysis
    analyzer.run_complete_analysis()
    
    # Print summaries
    analyzer.print_kpi_summary()
    analyzer.print_trend_summary()
    analyzer.print_product_summary()
    analyzer.print_regional_summary()
    
    # Save report
    analyzer.generate_analysis_report()
    
    print("\nAnalysis completed successfully! - data_analysis.py:569")
    
    return analyzer


if __name__ == "__main__":
    analyzer = main()