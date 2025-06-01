# CSV Data Processing with MaxCLI

The `process-csv` command allows you to apply custom Python functions to CSV datasets for data analysis and processing.

## Quick Start

```bash
# Install pandas (required dependency)
pip install pandas

# Basic usage
max process-csv --csv-file data.csv --function-file analysis.py

# Save function for later use
max process-csv --csv-file data.csv --function-file analysis.py --save-as my_analyzer

# List saved functions
max process-csv --list-saved
```

## Function File Format

Your Python file must contain a `process_data` function:

```python
import pandas as pd

def process_data(df: pd.DataFrame):
    """Your data processing logic here."""
    # Return statistics
    return df.describe()

    # Or filter data
    # return df[df['column'] > threshold]

    # Or group and aggregate
    # return df.groupby('category').sum()
```

## Examples

### Statistical Analysis

```python
def process_data(df: pd.DataFrame):
    return {
        'rows': len(df),
        'columns': list(df.columns),
        'summary': df.describe().to_dict()
    }
```

### Data Filtering

```python
def process_data(df: pd.DataFrame):
    # Filter high-value records
    if 'salary' in df.columns:
        return df[df['salary'] > df['salary'].median()]
    return df
```

## Features

- ✅ **Flexible Processing**: Write any Python function to process your data
- ✅ **Save & Reuse**: Save functions for future use across different datasets
- ✅ **Error Handling**: Comprehensive validation and helpful error messages
- ✅ **Multiple Output Types**: Return DataFrames, dicts, strings, or any data type
- ✅ **Optional Dependency**: Graceful handling when pandas is not installed

## Saved Functions

Functions are stored in `maxcli/saved_functions/` and can be reused with any dataset.

---

See example files: `example_data.csv` and `example_function.py` for complete examples.
