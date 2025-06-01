"""
Miscellaneous Manager Module for MaxCLI.

This module provides miscellaneous utility functionality including:
- Database backup operations
- Application deployment utilities
- Other utility commands
"""

import argparse
from maxcli.commands.misc import backup_db, deploy_app


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