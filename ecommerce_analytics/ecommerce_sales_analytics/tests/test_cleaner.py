# tests/test_cleaner.py
"""
Unit tests for data cleaning module
Author: ANGEL-MAVUYANGWA
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.data_cleaning import DataCleaner
from scripts.utils import handle_missing_values, standardize_text_columns, cap_outliers_percentile


class TestDataCleaner(unittest.TestCase):
    """Test cases for DataCleaner class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cleaner = DataCleaner()
        
        # Create sample data for testing
        self.sample_data = pd.DataFrame({
            'Order ID': ['ORD-001', 'ORD-002', 'ORD-003', 'ORD-001'],
            'Date': ['30-04-22', '01-05-22', '02-05-22', '30-04-22'],
            'Status': ['Shipped - Delivered to Buyer', 'Cancelled', 'Shipped', 'Shipped - Delivered to Buyer'],
            'Amount': [1000, 500, None, 1000],
            'Qty': [2, 1, 3, 2],
            'SKU': ['SKU-A', 'SKU-B', 'SKU-C', 'SKU-A'],
            'Category': ['Clothing', 'Clothing', None, 'Clothing'],
            'ship-state': ['Maharashtra', 'Karnataka', 'Delhi', 'Maharashtra']
        })
    
    def test_remove_duplicates(self):
        """Test duplicate removal functionality"""
        self.cleaner.df = self.sample_data.copy()
        initial_count = len(self.cleaner.df)
        duplicates_removed = self.cleaner.remove_duplicates()
        
        self.assertEqual(duplicates_removed, 1)
        self.assertEqual(len(self.cleaner.df), initial_count - 1)
    
    def test_fix_date_format(self):
        """Test date formatting functionality"""
        self.cleaner.df = self.sample_data.copy()
        self.cleaner.fix_date_format()
        
        self.assertIn('Year', self.cleaner.df.columns)
        self.assertIn('Month', self.cleaner.df.columns)
        self.assertIn('Month_Name', self.cleaner.df.columns)
        self.assertIn('Day_of_Week', self.cleaner.df.columns)
    
    def test_fix_amount_column(self):
        """Test amount column fixing"""
        self.cleaner.df = self.sample_data.copy()
        self.cleaner.fix_amount_column()
        
        # Check that null values are filled
        self.assertEqual(self.cleaner.df['Amount'].isnull().sum(), 0)
        
        # Check that values are numeric
        self.assertTrue(pd.api.types.is_numeric_dtype(self.cleaner.df['Amount']))
    
    def test_create_status_groups(self):
        """Test status grouping functionality"""
        self.cleaner.df = self.sample_data.copy()
        self.cleaner.create_status_groups()
        
        self.assertIn('Status_Group', self.cleaner.df.columns)
        self.assertEqual(self.cleaner.df.loc[0, 'Status_Group'], 'DELIVERED')
        self.assertEqual(self.cleaner.df.loc[1, 'Status_Group'], 'CANCELLED')
    
    def test_handle_missing_values(self):
        """Test missing values handling"""
        df_test = handle_missing_values(self.sample_data, threshold=0.5)
        
        # Check that missing values are filled
        self.assertEqual(df_test['Amount'].isnull().sum(), 0)
        self.assertEqual(df_test['Category'].isnull().sum(), 0)
    
    def test_standardize_text_columns(self):
        """Test text column standardization"""
        columns_to_standardize = ['Status', 'Category', 'ship-state']
        df_test = standardize_text_columns(self.sample_data, columns_to_standardize)
        
        # Check that values are uppercase
        self.assertTrue(df_test['Status'].iloc[0].isupper())
        self.assertTrue(df_test['ship-state'].iloc[0].isupper())
    
    def test_cap_outliers(self):
        """Test outlier capping"""
        data_with_outliers = pd.DataFrame({
            'Amount': [100, 200, 300, 400, 5000, 6000, 7000]
        })
        
        df_capped = cap_outliers_percentile(data_with_outliers, 'Amount', percentile=0.9)
        
        # Check that outliers are capped
        self.assertLessEqual(df_capped['Amount'].max(), data_with_outliers['Amount'].quantile(0.9))
    
    def test_clean_data_pipeline(self):
        """Test complete cleaning pipeline"""
        self.cleaner.df = self.sample_data.copy()
        cleaned_df = self.cleaner.clean_data()
        
        # Check that cleaning was performed
        self.assertGreater(len(cleaned_df.columns), len(self.sample_data.columns))
        self.assertIn('Status_Group', cleaned_df.columns)
        self.assertIn('Year', cleaned_df.columns)
        self.assertEqual(cleaned_df['Amount'].isnull().sum(), 0)


class TestUtilsFunctions(unittest.TestCase):
    """Test cases for utility functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_df = pd.DataFrame({
            'numeric_col': [1, 2, 3, 4, 5, None],
            'categorical_col': ['A', 'B', None, 'A', 'B', 'C'],
            'all_missing': [None, None, None, None, None, None]
        })
    
    def test_handle_missing_values_drop_column(self):
        """Test dropping columns with high missing percentage"""
        df_result = handle_missing_values(self.test_df, threshold=0.5)
        
        # Column with all missing should be dropped
        self.assertNotIn('all_missing', df_result.columns)
    
    def test_standardize_text_columns_empty(self):
        """Test standardizing with empty column list"""
        df_result = standardize_text_columns(self.test_df, [])
        
        # Should return unchanged dataframe
        self.assertEqual(len(df_result.columns), len(self.test_df.columns))


if __name__ == '__main__':
    unittest.main()