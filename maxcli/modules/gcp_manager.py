"""
GCP Manager Module for MaxCLI.

This module provides Google Cloud Platform configuration management including:
- Switching between gcloud configurations
- Creating new gcloud configurations with full authentication
- Managing Application Default Credentials (ADC)
- Listing available configurations
"""

import argparse
from maxcli.commands.gcp import switch_config, create_config, list_configs


def register_commands(subparsers) -> None:
    """Register GCP management commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Switch gcloud configuration command
    switch_parser = subparsers.add_parser(
        'switch-config', 
        help='Switch gcloud config and application default credentials',
        description="""
Switch to an existing gcloud configuration and its associated Application Default Credentials (ADC).

This command will:
1. Activate the specified gcloud configuration
2. Copy the saved ADC file for this configuration to the active ADC location
3. Set the appropriate quota project if a mapping exists

The configuration must have been previously created using 'max create-config' or manually set up
with a corresponding ADC file at ~/.config/gcloud/adc_<name>.json

INTERACTIVE MODE: If no configuration name is provided, you'll see an interactive menu
with arrow key navigation to select from available configurations.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max switch-config altekai       # Switch to 'altekai' configuration
  max switch-config               # Interactive mode - choose from menu
  max switch-config urbansharing  # Switch to 'urbansharing' configuration
        """
    )
    switch_parser.add_argument('name', nargs='?', help='Configuration name (optional - if not provided, shows interactive menu)')
    switch_parser.set_defaults(func=switch_config)

    # Create new gcloud configuration command
    create_parser = subparsers.add_parser(
        'create-config', 
        help='Create new gcloud config with full authentication setup',
        description="""
Create a new gcloud configuration with complete authentication and ADC setup.

This command will guide you through:
1. Creating a new gcloud configuration
2. Authenticating with your Google account
3. Setting up Application Default Credentials (ADC)
4. Saving the ADC file for future switching
5. Configuring quota project (with smart mapping or manual input)

After completion, you can switch to this configuration using 'max switch-config <name>'.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max create-config myproject     # Create config named 'myproject'
  max create-config altekai       # Create config with existing quota mapping
        """
    )
    create_parser.add_argument('name', help='Configuration name to create (required)')
    create_parser.set_defaults(func=create_config)

    # List available configurations command
    list_parser = subparsers.add_parser(
        'list-configs', 
        help='List all available gcloud configurations with ADC files',
        description="""
Display all gcloud configurations that have associated Application Default Credentials (ADC) files.

This shows configurations that can be used with 'max switch-config' command.
Only configurations with saved ADC files in ~/.config/gcloud/adc_*.json are listed.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max list-configs                # Show all available configurations
        """
    )
    list_parser.set_defaults(func=list_configs) 