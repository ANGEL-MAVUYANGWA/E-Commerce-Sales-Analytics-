# scripts/utils.py
"""
Utility functions for E-Commerce Sales Analytics Project
Author: ANGEL-MAVUYANGWA
"""

import os
import logging
import yaml
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> Dict:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration parameters
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


def create_directory(path: str) -> None:
    """
    Create directory if it doesn't exist
    
    Args:
        path: Directory path to create
    """
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Created directory: {path}")


def get_file_hash(file_path: str) -> str:
    """
    Calculate MD5 hash of a file for integrity checking
    
    Args:
        file_path: Path to file
        
    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that dataframe contains required columns
    
    Args:
        df: Input dataframe
        required_columns: List of required column names
        
    Returns:
        True if validation passes, False otherwise
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False
    
    logger.info("Dataframe validation passed")
    return True


def handle_missing_values(
    df: pd.DataFrame,
    numeric_strategy: str = "median",
    categorical_strategy: str = "mode",
    threshold: float = 0.5
) -> pd.DataFrame:
    """
    Handle missing values in dataframe
    
    Args:
        df: Input dataframe
        numeric_strategy: Strategy for numeric columns ('mean', 'median', 'zero')
        categorical_strategy: Strategy for categorical columns ('mode', 'constant')
        threshold: Maximum allowed missing percentage before dropping column
        
    Returns:
        Dataframe with handled missing values
    """
    df_clean = df.copy()
    
    # Drop columns with too many missing values
    missing_pct = df_clean.isnull().sum() / len(df_clean)
    cols_to_drop = missing_pct[missing_pct > threshold].index.tolist()
    
    if cols_to_drop:
        df_clean = df_clean.drop(columns=cols_to_drop)
        logger.info(f"Dropped columns with >{threshold*100}% missing: {cols_to_drop}")
    
    # Handle remaining missing values
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    categorical_cols = df_clean.select_dtypes(include=['object']).columns
    
    # Numeric columns
    for col in numeric_cols:
        if df_clean[col].isnull().sum() > 0:
            if numeric_strategy == "mean":
                fill_value = df_clean[col].mean()
            elif numeric_strategy == "median":
                fill_value = df_clean[col].median()
            elif numeric_strategy == "zero":
                fill_value = 0
            else:
                fill_value = df_clean[col].median()
            
            df_clean[col] = df_clean[col].fillna(fill_value)
            logger.debug(f"Filled missing values in {col} with {numeric_strategy}: {fill_value}")
    
    # Categorical columns
    for col in categorical_cols:
        if df_clean[col].isnull().sum() > 0:
            if categorical_strategy == "mode":
                fill_value = df_clean[col].mode().iloc[0] if not df_clean[col].mode().empty else "UNKNOWN"
            else:
                fill_value = "UNKNOWN"
            
            df_clean[col] = df_clean[col].fillna(fill_value)
            logger.debug(f"Filled missing values in {col} with {categorical_strategy}: {fill_value}")
    
    logger.info(f"Missing values handled. Final shape: {df_clean.shape}")
    return df_clean


def remove_outliers_iqr(
    df: pd.DataFrame,
    column: str,
    multiplier: float = 1.5
) -> pd.DataFrame:
    """
    Remove outliers using IQR method
    
    Args:
        df: Input dataframe
        column: Column to check for outliers
        multiplier: IQR multiplier (default 1.5)
        
    Returns:
        Dataframe with outliers removed
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR
    
    outliers_removed = df[(df[column] < lower_bound) | (df[column] > upper_bound)].shape[0]
    df_clean = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
    
    logger.info(f"Removed {outliers_removed} outliers from column '{column}'")
    return df_clean


def cap_outliers_percentile(
    df: pd.DataFrame,
    column: str,
    percentile: float = 0.99
) -> pd.DataFrame:
    """
    Cap outliers at specified percentile
    
    Args:
        df: Input dataframe
        column: Column to cap outliers
        percentile: Percentile threshold (default 0.99)
        
    Returns:
        Dataframe with capped outliers
    """
    df_clean = df.copy()
    cap_value = df_clean[column].quantile(percentile)
    outliers_count = (df_clean[column] > cap_value).sum()
    
    df_clean[column] = np.where(df_clean[column] > cap_value, cap_value, df_clean[column])
    
    logger.info(f"Capped {outliers_count} outliers in column '{column}' at {percentile*100}th percentile: {cap_value}")
    return df_clean


def standardize_text_columns(
    df: pd.DataFrame,
    columns: List[str]
) -> pd.DataFrame:
    """
    Standardize text columns to uppercase and strip whitespace
    
    Args:
        df: Input dataframe
        columns: List of column names to standardize
        
    Returns:
        Dataframe with standardized text columns
    """
    df_clean = df.copy()
    
    for col in columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.upper().str.strip()
            df_clean[col] = df_clean[col].replace(['NAN', 'NONE', ''], 'UNKNOWN')
            logger.debug(f"Standardized column: {col}")
    
    return df_clean


def generate_summary_statistics(df: pd.DataFrame) -> Dict:
    """
    Generate comprehensive summary statistics
    
    Args:
        df: Input dataframe
        
    Returns:
        Dictionary containing summary statistics
    """
    summary = {
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': df.dtypes.to_dict(),
        'missing': df.isnull().sum().to_dict(),
        'missing_pct': (df.isnull().sum() / len(df) * 100).to_dict(),
        'duplicates': df.duplicated().sum()
    }
    
    # Numeric column statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        summary['numeric_stats'] = df[numeric_cols].describe().to_dict()
    
    # Categorical column statistics
    categorical_cols = df.select_dtypes(include=['object']).columns
    if len(categorical_cols) > 0:
        summary['categorical_stats'] = {}
        for col in categorical_cols[:5]:  # Limit to first 5 for performance
            summary['categorical_stats'][col] = df[col].value_counts().head(10).to_dict()
    
    logger.info("Summary statistics generated")
    return summary


def save_summary_report(df: pd.DataFrame, output_path: str) -> None:
    """
    Save summary statistics report to file
    
    Args:
        df: Input dataframe
        output_path: Path to save report
    """
    summary = generate_summary_statistics(df)
    
    with open(output_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("DATA SUMMARY REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Dataset Shape: {summary['shape'][0]} rows x {summary['shape'][1]} columns\n")
        f.write(f"Total Duplicates: {summary['duplicates']}\n\n")
        
        f.write("COLUMN INFORMATION:\n")
        f.write("-" * 40 + "\n")
        for col in summary['columns']:
            dtype = summary['dtypes'][col]
            missing = summary['missing'][col]
            missing_pct = summary['missing_pct'][col]
            f.write(f"  {col}: {dtype} | Missing: {missing} ({missing_pct:.2f}%)\n")
        
        if 'numeric_stats' in summary:
            f.write("\nNUMERIC COLUMN STATISTICS:\n")
            f.write("-" * 40 + "\n")
            for col, stats in summary['numeric_stats'].items():
                f.write(f"\n  {col}:\n")
                for stat, value in stats.items():
                    f.write(f"    {stat}: {value:.2f}\n")
    
    logger.info(f"Summary report saved to {output_path}")