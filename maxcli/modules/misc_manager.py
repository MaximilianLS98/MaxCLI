"""
Miscellaneous Manager Module for MaxCLI.

This module provides miscellaneous utility functionality including:
- Database backup operations
- Application deployment utilities
- CSV data processing with Python functions
- Other utility commands
"""

import argparse
from maxcli.commands.misc import backup_db, deploy_app, process_csv_data


def register_commands(subparsers) -> None:
    """Register miscellaneous utility commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Database backup command
    backup_parser = subparsers.add_parser(
        'backup-db', 
        help='Backup PostgreSQL database to timestamped file',
        description="""
Create a backup of the PostgreSQL database 'mydb' using pg_dump.

The backup file will be saved to ~/backups/db_<date>.sql where <date> is the current date
in YYYY-MM-DD format. The backup directory will be created if it doesn't exist.

Requirements:
- PostgreSQL client tools (pg_dump) must be installed
- Database 'mydb' must exist and be accessible
- User must have read permissions on the database
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max backup-db                   # Create backup file like ~/backups/db_2024-01-15.sql
        """
    )
    backup_parser.set_defaults(func=backup_db)

    # Application deployment command
    deploy_parser = subparsers.add_parser(
        'deploy-app', 
        help='Deploy the application (placeholder command)',
        description="""
Deploy the application using predefined deployment logic.

NOTE: This is currently a placeholder command. The actual deployment logic
needs to be implemented based on your specific deployment requirements.

Typical deployment steps might include:
- Building the application
- Running tests
- Pushing to container registry
- Updating Kubernetes deployments
- Running post-deployment checks
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max deploy-app                  # Run deployment process
        """
    )
    deploy_parser.set_defaults(func=deploy_app)

    # CSV data processing command
    csv_parser = subparsers.add_parser(
        'process-csv',
        help='Process CSV data using a Python function file',
        description="""
Process CSV data by applying a Python function to the dataset.

The Python function file must contain a function named 'process_data' that accepts
a pandas DataFrame as input and returns the processed result. The function can
perform any data analysis, transformation, or computation on the dataset.

You can optionally save the function file for future use by providing the --save-as
option. Saved functions are stored in the maxcli/saved_functions directory and can
be listed using the --list-saved option.

Requirements:
- pandas library must be installed
- Function file must contain a 'process_data' function
- CSV file must be valid and readable

Function File Format:
The Python file should follow this pattern:

    import pandas as pd
    
    def process_data(df: pd.DataFrame):
        # Your data processing logic here
        # Examples:
        # - return df.describe()  # Statistical summary
        # - return df.groupby('column').sum()  # Grouping
        # - return df[df['value'] > threshold]  # Filtering
        return processed_result
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max process-csv --csv-file data.csv --function-file analysis.py
  max process-csv --csv-file sales.csv --function-file stats.py --save-as sales_analysis
  max process-csv --list-saved                      # List saved functions
        """
    )
    
    # Add arguments for CSV processing command
    csv_parser.add_argument(
        '--csv-file', 
        type=str,
        help='Path to the CSV data file to process'
    )
    csv_parser.add_argument(
        '--function-file', 
        type=str,
        help='Path to the Python file containing the processing function'
    )
    csv_parser.add_argument(
        '--save-as', 
        type=str,
        help='Save the function file with this name for future use'
    )
    csv_parser.add_argument(
        '--list-saved', 
        action='store_true',
        help='List all saved function files'
    )
    
    csv_parser.set_defaults(func=process_csv_data) 