# CSV Data Processing with MaxCLI

The `process-csv` command allows you to apply custom Python functions to CSV datasets, providing a flexible way to analyze, transform, and process your data.

## Basic Usage

```bash
max process-csv --csv-file data.csv --function-file analysis.py
```

## Command Options

- `--csv-file`: Path to the CSV data file to process
- `--function-file`: Path to the Python file containing the processing function
- `--save-as`: Save the function file with a custom name for future use
- `--list-saved`: List all saved function files

## Function File Requirements

Your Python function file must contain a function named `process_data` that:

- Accepts a pandas DataFrame as the only parameter
- Returns any type of result (DataFrame, dict, string, etc.)

### Basic Function Template

```python
import pandas as pd

def process_data(df: pd.DataFrame):
    """Your data processing logic here."""

    # Example: Return basic statistics
    return df.describe()

    # Example: Filter data
    # return df[df['column'] > threshold]

    # Example: Group and aggregate
    # return df.groupby('category').sum()

    # Example: Custom analysis
    # return {
    #     'total_rows': len(df),
    #     'columns': list(df.columns),
    #     'summary': df.describe().to_dict()
    # }
```

## Examples

### 1. Basic Data Analysis

```bash
max process-csv --csv-file example_data.csv --function-file example_function.py
```

### 2. Save Function for Later Use

```bash
max process-csv --csv-file sales_data.csv --function-file my_analysis.py --save-as sales_analyzer
```

### 3. List Saved Functions

```bash
max process-csv --list-saved
```

## Example Function Files

### Statistical Analysis

```python
import pandas as pd
import numpy as np

def process_data(df: pd.DataFrame):
    """Comprehensive statistical analysis."""
    return {
        'shape': df.shape,
        'dtypes': df.dtypes.to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'numeric_summary': df.describe().to_dict(),
        'memory_usage': f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
    }
```

### Data Filtering

```python
import pandas as pd

def process_data(df: pd.DataFrame):
    """Filter high-value records."""
    # Assuming there's a 'salary' column
    if 'salary' in df.columns:
        return df[df['salary'] > df['salary'].median()]
    return df
```

### Grouping and Aggregation

```python
import pandas as pd

def process_data(df: pd.DataFrame):
    """Group by department and calculate statistics."""
    if 'department' in df.columns:
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            return df.groupby('department')[numeric_cols].agg(['mean', 'sum', 'count'])
    return df.describe()
```

## Saved Functions Directory

Functions saved with `--save-as` are stored in `maxcli/saved_functions/` and can be reused across different datasets. Use `--list-saved` to see all available saved functions.

## Requirements

- pandas library must be installed
- CSV file must be properly formatted and readable
- Function file must contain the `process_data` function

## Error Handling

The command includes comprehensive error handling for:

- Missing or invalid CSV files
- Missing or invalid Python function files
- Missing `process_data` function
- Runtime errors during data processing
- File system errors when saving functions

## Tips

1. **Test your functions**: Always test your function files with small datasets first
2. **Handle edge cases**: Include error handling in your functions for missing columns or unexpected data types
3. **Use descriptive names**: When saving functions, use descriptive names that indicate their purpose
4. **Document your functions**: Include docstrings to describe what your functions do
5. **Performance**: For large datasets, consider using vectorized pandas operations for better performance
