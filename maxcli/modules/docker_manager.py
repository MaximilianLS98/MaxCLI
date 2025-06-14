"""
Docker Manager Module for MaxCLI.

This module provides Docker system management functionality including:
- Docker system cleanup operations with configurable levels
- Container, image, and volume management
- Both extensive (aggressive) and minimal (conservative) cleanup options
"""

import argparse
from maxcli.commands.docker import docker_clean_command


def register_commands(subparsers) -> None:
    """Register Docker management commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Main docker command with subcommands
    docker_parser = subparsers.add_parser(
        'docker',
        help='Docker system management operations',
        description="""
Docker system management toolkit.

This command provides various Docker management operations organized into subcommands.
Use 'max docker <subcommand> --help' for detailed help on each subcommand.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max docker clean --extensive    # Aggressive Docker cleanup
  max docker clean --minimal      # Conservative Docker cleanup
  max docker clean                # Default to minimal cleanup
        """
    )
    
    # Create subparsers for docker subcommands
    docker_subparsers = docker_parser.add_subparsers(
        title="Docker Commands",
        dest="docker_command",
        description="Available Docker management operations",
        metavar="<subcommand>"
    )
    
    # Docker clean subcommand
    clean_parser = docker_subparsers.add_parser(
        'clean',
        help='Clean up Docker system with configurable cleanup levels',
        description="""
Perform Docker system cleanup with configurable aggressiveness levels.

Cleanup Levels:
• --extensive: Aggressive cleanup that removes ALL unused Docker resources
  - All stopped containers
  - All networks not used by at least one container  
  - All dangling images
  - All build cache
  - All unused volumes
  
• --minimal: Conservative cleanup that preserves recent/useful items
  - Containers stopped for more than 24 hours
  - Dangling images only (untagged/unreferenced)
  - Unused networks
  - Build cache older than 7 days
  - Preserves: all tagged images, recent containers, all volumes

If no level is specified, defaults to --minimal for safety.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max docker clean --extensive    # Remove all unused Docker resources
  max docker clean --minimal      # Safe cleanup preserving recent items
  max docker clean                # Default to minimal cleanup
        """
    )
    
    # Add mutually exclusive group for cleanup level
    cleanup_group = clean_parser.add_mutually_exclusive_group()
    cleanup_group.add_argument(
        '--extensive', 
        action='store_true',
        help='Perform aggressive cleanup (removes ALL unused resources)'
    )
    cleanup_group.add_argument(
        '--minimal', 
        action='store_true',
        help='Perform conservative cleanup (preserves recent items)'
    )
    
    clean_parser.set_defaults(func=docker_clean_command) 