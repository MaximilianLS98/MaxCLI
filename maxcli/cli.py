"""
Main CLI module with dynamic modular architecture.

This module provides the main entry point for MaxCLI with dynamic module loading
based on user configuration. Modules can be enabled/disabled through the modules
management commands.
"""

import argparse
from .config import init_config
from .modules.module_manager import load_and_register_modules, register_commands as register_module_commands


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the main argument parser.
    
    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog='max', 
        description="Max's Personal CLI - A modular collection of useful development and operations commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 Modular CLI System:
MaxCLI uses a modular architecture where functionality is organized into modules.
You can enable/disable modules based on your needs to keep the CLI clean and focused.

Module Management:
  max modules list                # Show all available modules
  max modules enable <module>     # Enable a module
  max modules disable <module>    # Disable a module

Core Commands:
  max init                        # Initialize CLI with your personal configuration
  
Examples of enabled commands (depends on active modules):
  max ssh list-targets            # Show all saved SSH targets (ssh_manager)
  max ssh add-target prod ubuntu 192.168.1.100 (ssh_manager)
  max coolify status              # Check Coolify instance status (coolify_manager)
  max setup minimal               # Basic development environment setup (setup_manager)
  max docker clean --extensive    # Clean up Docker system (docker_manager)
  max kctx my-k8s-context         # Switch Kubernetes context (kubernetes_manager)
  max switch-config altekai       # Switch gcloud config (gcp_manager)
  
Use 'max <command> --help' for detailed help on each command.
Use 'max modules list' to see available functionality.
        """
    )
    
    return parser


def register_core_commands(subparsers) -> None:
    """Register core CLI commands that are always available.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Initialize configuration command
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize or update personal configuration',
        description="""
Initialize MaxCLI with your personal configuration settings.

This is a one-time setup (or update) process that collects:
- Git username and email for repository configuration
- Dotfiles repository URL (optional)
- Google Cloud Platform project mappings (optional)
- Coolify instance URL and API key (optional)

The configuration is saved to ~/.config/maxcli/config.json and used by
other commands to personalize their behavior.

After initialization, commands like 'max setup dev-full' will use your
personal git settings and dotfiles repository automatically.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max init                        # First-time setup or update existing config
  max init --force                # Force reconfiguration (skip confirmation)
        """
    )
    init_parser.add_argument('--force', action='store_true', help='Force reconfiguration without confirmation')
    init_parser.set_defaults(func=init_config)


def main() -> None:
    """Main CLI entry point with dynamic module loading."""
    # Create the main parser
    parser = create_parser()
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title="Available Commands", 
        dest="command",
        description="Choose a command to run. Use 'max <command> --help' for detailed help on each command.",
        metavar="<command>"
    )
    
    # Set default behavior when no command is provided
    parser.set_defaults(func=lambda _: parser.print_help())
    
    # Register core commands (always available)
    register_core_commands(subparsers)
    
    # Register module management commands (always available)
    register_module_commands(subparsers)
    
    # Load and register enabled modules dynamically
    load_and_register_modules(subparsers)
    
    # Enable autocomplete if argcomplete is installed
    try:
        import argcomplete  # type: ignore # Optional dependency
        argcomplete.autocomplete(parser)
    except ImportError:
        pass
    
    # Parse arguments and execute the appropriate function
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help() 