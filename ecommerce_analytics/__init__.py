# __init__.py
"""
E-Commerce Sales Analytics Project
A comprehensive data analytics project for e-commerce sales data
"""

__version__ = "1.0.0"
__author__ = "Angel"

from scripts.data_cleaning import DataCleaner
from scripts.data_analysis import SalesAnalyzer
from scripts.visualization import SalesVisualizer

__all__ = ['DataCleaner', 'SalesAnalyzer', 'SalesVisualizer']