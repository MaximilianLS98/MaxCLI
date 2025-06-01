"""
Example function file for CSV data processing with MaxCLI.

This file demonstrates how to write a processing function that can be used
with the 'max process-csv' command.

The function must be named 'process_data' and accept a pandas DataFrame as input.
It can return any type of result (DataFrame, Series, dict, string, etc.).
"""

import pandas as pd
import numpy as np


def process_data(df: pd.DataFrame):
    """Example data processing function.
    
    This function performs basic statistical analysis on the dataset and returns
    a summary report as a dictionary.
    
    Args:
        df: Input pandas DataFrame containing the CSV data.
        
    Returns:
        Dictionary containing analysis results.
    """
    
    # Basic info about the dataset
    analysis_results = {
        'dataset_info': {
            'num_rows': len(df),
            'num_columns': len(df.columns),
            'column_names': list(df.columns),
            'memory_usage': f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
        },
        
        'data_types': df.dtypes.to_dict(),
        
        'missing_values': df.isnull().sum().to_dict(),
        
        'numeric_summary': {}
    }
    
    # Analyze numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    if len(numeric_columns) > 0:
        for col in numeric_columns:
            analysis_results['numeric_summary'][col] = {
                'mean': df[col].mean(),
                'median': df[col].median(),
                'std': df[col].std(),
                'min': df[col].min(),
                'max': df[col].max(),
                'unique_values': df[col].nunique()
            }
    
    # Analyze categorical columns
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_columns) > 0:
        analysis_results['categorical_summary'] = {}
        for col in categorical_columns:
            analysis_results['categorical_summary'][col] = {
                'unique_values': df[col].nunique(),
                'most_common': df[col].value_counts().head(3).to_dict(),
                'missing_count': df[col].isnull().sum()
            }
    
    return analysis_results


# Example of other types of processing functions:

def process_data_filter_example(df: pd.DataFrame):
    """Example: Filter data based on conditions."""
    # This would filter rows where a numeric column is above its mean
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        first_numeric_col = numeric_cols[0]
        mean_value = df[first_numeric_col].mean()
        return df[df[first_numeric_col] > mean_value]
    return df


def process_data_groupby_example(df: pd.DataFrame):
    """Example: Group data and calculate aggregations."""
    # This would group by the first categorical column and sum numeric columns
    categorical_cols = df.select_dtypes(include=['object']).columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(categorical_cols) > 0 and len(numeric_cols) > 0:
        group_col = categorical_cols[0]
        return df.groupby(group_col)[numeric_cols].sum()
    
    return df.describe()  # Fallback to statistical summary 