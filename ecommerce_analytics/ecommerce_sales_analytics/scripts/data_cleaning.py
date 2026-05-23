# scripts/data_cleaning.py
"""
Data Cleaning Module for E-Commerce Sales Analytics
Author: ANGEL-MAVUYANGWA
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils import (
    load_config, create_directory, handle_missing_values,
    standardize_text_columns, cap_outliers_percentile,
    save_summary_report, logger
)


class DataCleaner:
    """
    Data cleaning class for e-commerce sales data
    Handles missing values, duplicates, formatting, and outliers
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize DataCleaner with configuration
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.df = None
        self.cleaning_report = {}
        self.logger = logging.getLogger(__name__)
        
        # Create necessary directories
        create_directory("data/cleaned")
        create_directory("logs")
        create_directory("reports")
        
        self.logger.info("DataCleaner initialized successfully")
    
    def load_data(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load raw data from CSV file
        
        Args:
            file_path: Path to raw data file
            
        Returns:
            Loaded dataframe
        """
        if file_path is None:
            file_path = self.config['data']['raw_path']
        
        try:
            self.df = pd.read_csv(file_path)
            self.logger.info(f"Data loaded successfully: {self.df.shape[0]} rows, {self.df.shape[1]} columns")
            self.cleaning_report['initial_shape'] = self.df.shape
            return self.df
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise
    
    def explore_data(self) -> Dict:
        """
        Perform initial data exploration
        
        Returns:
            Dictionary with exploration results
        """
        self.logger.info("Starting data exploration")
        
        exploration = {
            'shape': self.df.shape,
            'columns': list(self.df.columns),
            'dtypes': self.df.dtypes.to_dict(),
            'missing_count': self.df.isnull().sum().to_dict(),
            'missing_percentage': (self.df.isnull().sum() / len(self.df) * 100).to_dict(),
            'duplicate_count': self.df.duplicated().sum()
        }
        
        # Print exploration results
        print("\n - data_cleaning.py:93" + "="*60)
        print("DATA EXPLORATION REPORT - data_cleaning.py:94")
        print("= - data_cleaning.py:95"*60)
        print(f"Dataset Shape: {exploration['shape'][0]} rows x {exploration['shape'][1]} columns - data_cleaning.py:96")
        print(f"Duplicate Rows: {exploration['duplicate_count']} - data_cleaning.py:97")
        
        print("\nMissing Values Summary: - data_cleaning.py:99")
        missing_df = pd.DataFrame({
            'Column': list(exploration['missing_count'].keys()),
            'Missing_Count': list(exploration['missing_count'].values()),
            'Missing_Percentage': list(exploration['missing_percentage'].values())
        })
        missing_df = missing_df[missing_df['Missing_Count'] > 0].sort_values('Missing_Percentage', ascending=False)
        print(missing_df.to_string(index=False))
        
        self.cleaning_report['exploration'] = exploration
        return exploration
    
    def remove_duplicates(self) -> int:
        """
        Remove duplicate rows from dataframe
        
        Returns:
            Number of duplicates removed
        """
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates()
        duplicates_removed = initial_count - len(self.df)
        
        self.logger.info(f"Removed {duplicates_removed} duplicate rows")
        self.cleaning_report['duplicates_removed'] = duplicates_removed
        
        return duplicates_removed
    
    def fix_date_format(self) -> None:
        """
        Fix date column formatting and extract date features
        """
        date_col = self.config['columns']['date']
        
        if date_col not in self.df.columns:
            self.logger.warning(f"Date column '{date_col}' not found")
            return
        
        date_format = self.config['cleaning']['date_format']
        
        try:
            self.df[date_col] = pd.to_datetime(self.df[date_col], format=date_format, errors='coerce')
            
            # Extract date features
            self.df['Year'] = self.df[date_col].dt.year
            self.df['Month'] = self.df[date_col].dt.month
            self.df['Month_Name'] = self.df[date_col].dt.month_name()
            self.df['Day'] = self.df[date_col].dt.day
            self.df['Day_of_Week'] = self.df[date_col].dt.day_name()
            self.df['Week_Number'] = self.df[date_col].dt.isocalendar().week
            self.df['Quarter'] = self.df[date_col].dt.quarter
            
            self.logger.info(f"Date column formatted successfully. Date range: {self.df[date_col].min()} to {self.df[date_col].max()}")
        except Exception as e:
            self.logger.error(f"Error formatting date column: {e}")
    
    def fix_amount_column(self) -> None:
        """
        Fix amount column: convert to numeric and handle invalid values
        """
        amount_col = self.config['columns']['amount']
        
        if amount_col not in self.df.columns:
            self.logger.warning(f"Amount column '{amount_col}' not found")
            return
        
        # Convert to numeric
        self.df[amount_col] = pd.to_numeric(self.df[amount_col], errors='coerce')
        
        # Count invalid values
        invalid_count = self.df[amount_col].isnull().sum()
        if invalid_count > 0:
            self.logger.warning(f"Found {invalid_count} invalid amount values")
        
        # Fill missing with median
        median_value = self.df[amount_col].median()
        self.df[amount_col] = self.df[amount_col].fillna(median_value)
        
        self.logger.info(f"Amount column fixed. Median value: {median_value}")
        self.cleaning_report['amount_median'] = median_value
    
    def fix_quantity_column(self) -> None:
        """
        Fix quantity column: convert to integer and handle invalid values
        """
        qty_col = self.config['columns']['quantity']
        
        if qty_col not in self.df.columns:
            self.logger.warning(f"Quantity column '{qty_col}' not found")
            return
        
        # Convert to numeric
        self.df[qty_col] = pd.to_numeric(self.df[qty_col], errors='coerce')
        
        # Fill missing with 1
        self.df[qty_col] = self.df[qty_col].fillna(1)
        
        # Ensure minimum quantity is 1
        self.df[qty_col] = self.df[qty_col].clip(lower=1)
        
        self.logger.info(f"Quantity column fixed. Total units: {self.df[qty_col].sum()}")
    
    def create_status_groups(self) -> None:
        """
        Create aggregated status groups from raw status column
        """
        status_col = self.config['columns']['status']
        status_mapping = self.config['status_mapping']
        
        if status_col not in self.df.columns:
            self.logger.warning(f"Status column '{status_col}' not found")
            return
        
        self.df['Status_Group'] = self.df[status_col].map(status_mapping).fillna('OTHER')
        
        # Log distribution
        status_dist = self.df['Status_Group'].value_counts()
        self.logger.info(f"Status groups created. Distribution:\n{status_dist}")
        self.cleaning_report['status_distribution'] = status_dist.to_dict()
    
    def create_derived_columns(self) -> None:
        """
        Create additional derived columns for analysis
        """
        amount_col = self.config['columns']['amount']
        qty_col = self.config['columns']['quantity']
        
        # Calculate total value
        if amount_col in self.df.columns and qty_col in self.df.columns:
            self.df['Total_Value'] = self.df[amount_col] * self.df[qty_col]
            self.logger.info("Created Total_Value column")
        
        # Create revenue category
        if amount_col in self.df.columns:
            brackets = self.config['analysis']['revenue_brackets']
            labels = ['<250', '250-500', '500-1000', '1000-2500', '2500-5000', '5000+']
            self.df['Revenue_Category'] = pd.cut(
                self.df[amount_col],
                bins=brackets,
                labels=labels,
                right=False
            )
            self.logger.info("Created Revenue_Category column")
        
        # Extract category from SKU if needed
        if 'Category' not in self.df.columns or self.df['Category'].isnull().all():
            if 'SKU' in self.df.columns:
                self.df['Category_Extracted'] = self.df['SKU'].str.split('-').str[0]
                self.logger.info("Extracted category from SKU")
    
    def handle_outliers(self) -> None:
        """
        Handle outliers in numeric columns using percentile capping
        """
        amount_col = self.config['columns']['amount']
        percentile = self.config['cleaning']['outlier_percentile']
        
        if amount_col in self.df.columns:
            original_max = self.df[amount_col].max()
            self.df = cap_outliers_percentile(self.df, amount_col, percentile)
            new_max = self.df[amount_col].max()
            self.logger.info(f"Amount column capped: max reduced from {original_max} to {new_max}")
            
            self.cleaning_report['amount_capped'] = {
                'original_max': float(original_max),
                'new_max': float(new_max),
                'cap_percentile': percentile
            }
    
    def fix_b2b_column(self) -> None:
        """
        Fix B2B column to boolean type
        """
        if 'B2B' in self.df.columns:
            self.df['B2B'] = self.df['B2B'].astype(str).str.upper() == 'TRUE'
            self.logger.info(f"B2B column fixed. B2B orders: {self.df['B2B'].sum()}")
    
    def standardize_columns(self) -> None:
        """
        Standardize all relevant text columns
        """
        text_columns = [
            'Status', 'Fulfilment', 'Sales Channel', 'ship-service-level',
            'Category', 'Size', 'ship-city', 'ship-state', 'ship-country'
        ]
        
        self.df = standardize_text_columns(self.df, text_columns)
        self.logger.info("Text columns standardized")
    
    def clean_data(self) -> pd.DataFrame:
        """
        Execute complete data cleaning pipeline
        
        Returns:
            Cleaned dataframe
        """
        self.logger.info("="*60)
        self.logger.info("Starting data cleaning pipeline")
        self.logger.info("="*60)
        
        # Step 1: Remove duplicates
        self.remove_duplicates()
        
        # Step 2: Fix date format
        self.fix_date_format()
        
        # Step 3: Fix amount column
        self.fix_amount_column()
        
        # Step 4: Fix quantity column
        self.fix_quantity_column()
        
        # Step 5: Standardize text columns
        self.standardize_columns()
        
        # Step 6: Create status groups
        self.create_status_groups()
        
        # Step 7: Handle missing values
        threshold = self.config['cleaning']['missing_threshold']
        self.df = handle_missing_values(self.df, threshold=threshold)
        
        # Step 8: Handle outliers
        self.handle_outliers()
        
        # Step 9: Fix B2B column
        self.fix_b2b_column()
        
        # Step 10: Create derived columns
        self.create_derived_columns()
        
        self.cleaning_report['final_shape'] = self.df.shape
        self.cleaning_report['cleaning_completed'] = datetime.now().isoformat()
        
        self.logger.info("="*60)
        self.logger.info(f"Data cleaning completed. Final shape: {self.df.shape}")
        self.logger.info("="*60)
        
        return self.df
    
    def save_cleaned_data(self, output_path: Optional[str] = None) -> None:
        """
        Save cleaned data to CSV file
        
        Args:
            output_path: Path to save cleaned data
        """
        if output_path is None:
            output_path = self.config['data']['cleaned_path']
        
        create_directory(os.path.dirname(output_path))
        self.df.to_csv(output_path, index=False)
        self.logger.info(f"Cleaned data saved to {output_path}")
    
    def save_cleaning_report(self, output_path: str = "reports/cleaning_report.json") -> None:
        """
        Save cleaning report to JSON file
        
        Args:
            output_path: Path to save report
        """
        import json
        
        # Convert non-serializable objects
        report_copy = {}
        for key, value in self.cleaning_report.items():
            if isinstance(value, pd.Series):
                report_copy[key] = value.to_dict()
            elif isinstance(value, pd.DataFrame):
                report_copy[key] = value.to_dict()
            elif isinstance(value, (np.int64, np.float64)):
                report_copy[key] = float(value)
            else:
                report_copy[key] = value
        
        with open(output_path, 'w') as f:
            json.dump(report_copy, f, indent=2, default=str)
        
        self.logger.info(f"Cleaning report saved to {output_path}")
    
    def generate_cleaning_summary(self) -> None:
        """
        Generate and print cleaning summary
        """
        print("\n - data_cleaning.py:383" + "="*60)
        print("DATA CLEANING SUMMARY - data_cleaning.py:384")
        print("= - data_cleaning.py:385"*60)
        
        print(f"Initial shape: {self.cleaning_report.get('initial_shape', ('N/A', 'N/A'))} - data_cleaning.py:387")
        print(f"Final shape: {self.cleaning_report.get('final_shape', ('N/A', 'N/A'))} - data_cleaning.py:388")
        print(f"Duplicates removed: {self.cleaning_report.get('duplicates_removed', 0)} - data_cleaning.py:389")
        
        if 'status_distribution' in self.cleaning_report:
            print("\nStatus Distribution: - data_cleaning.py:392")
            for status, count in self.cleaning_report['status_distribution'].items():
                print(f"{status}: {count} - data_cleaning.py:394")
        
        if 'amount_capped' in self.cleaning_report:
            print(f"\nAmount column capped at {self.cleaning_report['amount_capped']['cap_percentile']*100}th percentile - data_cleaning.py:397")
            print(f"Original max: {self.cleaning_report['amount_capped']['original_max']:.2f} - data_cleaning.py:398")
            print(f"New max: {self.cleaning_report['amount_capped']['new_max']:.2f} - data_cleaning.py:399")
        
        print(f"\nCleaning completed: {self.cleaning_report.get('cleaning_completed', 'N/A')} - data_cleaning.py:401")
    
    def get_cleaned_data(self) -> pd.DataFrame:
        """
        Get the cleaned dataframe
        
        Returns:
            Cleaned dataframe
        """
        if self.df is None:
            raise ValueError("No data loaded. Call load_data() first.")
        return self.df


def main():
    """
    Main execution function
    """
    # Initialize cleaner
    cleaner = DataCleaner()
    
    # Load data
    cleaner.load_data()
    
    # Explore data
    cleaner.explore_data()
    
    # Clean data
    cleaner.clean_data()
    
    # Save cleaned data
    cleaner.save_cleaned_data()
    
    # Save cleaning report
    cleaner.save_cleaning_report()
    
    # Generate summary
    cleaner.generate_cleaning_summary()
    
    # Save summary statistics
    save_summary_report(cleaner.get_cleaned_data(), "reports/data_summary.txt")
    
    print("\nData cleaning pipeline completed successfully! - data_cleaning.py:443")
    print(f"Cleaned data shape: {cleaner.get_cleaned_data().shape} - data_cleaning.py:444")
    
    return cleaner


if __name__ == "__main__":
    cleaner = main()