"""
Main CLI module with dynamic modular architecture.

This module provides the main entry point for MaxCLI with dynamic module loading
based on user configuration. Modules can be enabled/disabled through the modules
management commands.
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from .config import is_initialized, init_config
from .runtime import CommandError, NON_INTERACTIVE, prompt_input
from .modules.module_manager import load_and_register_modules, register_commands as register_module_commands, load_modules_config


# Lifecycle management is shared with the standalone channel launcher.
from .installation import display_version, update as update_maxcli, InstallError


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
  max config init                 # Initialize CLI with your personal configuration
  max config backup               # Backup your MaxCLI configuration
  max config restore              # Restore configuration from backup
  max update                      # Update MaxCLI to the latest version from GitHub
  max uninstall                   # Deactivate this channel; preserve user data
  
Examples of enabled commands (depends on active modules):
  max ssh targets list            # Show all saved SSH targets (ssh_manager)
  max ssh targets add prod ubuntu 192.168.1.100 (ssh_manager)
  max coolify status              # Check Coolify instance status (coolify_manager)
  max setup minimal               # Basic development environment setup (setup_manager)
  max docker clean --extensive    # Clean up Docker system (docker_manager)
  max openclaw gateway restart    # Restart local OpenClaw gateway (openclaw_manager)
  max kctx my-k8s-context         # Switch Kubernetes context (kubernetes_manager)
  max gcp config switch altekai   # Switch gcloud config (gcp_manager)
  
Use 'max <command> --help' for detailed help on each command.
Use 'max modules list' to see available functionality.
        """
    )
    
    # Add version arguments
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Show version and installation channel (offline)'
    )
    
    parser.add_argument('--non-interactive', action='store_true', help='Never prompt; fail when input is required')
    return parser


def register_core_commands(subparsers) -> None:
    """Register core CLI commands that are always available.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    init_parser = subparsers.add_parser('init', help='Initialize personal configuration (alias for config init)')
    init_parser.add_argument('--force', action='store_true')
    init_parser.set_defaults(func=init_config)
    from .projects import register_commands as register_projects
    register_projects(subparsers)
    from .doctor import register_commands as register_doctor
    register_doctor(subparsers)
    from .installation import add_update_arguments, uninstall
    update_parser = subparsers.add_parser('update', help='Update the stable GitHub release or roll back')
    add_update_arguments(update_parser)
    update_parser.set_defaults(func=update_maxcli)
    uninstall_parser = subparsers.add_parser('uninstall', help='Deactivate this channel; preserve configuration and backups')
    uninstall_parser.add_argument('--force', action='store_true')
    uninstall_parser.add_argument('--dry-run', action='store_true')
    uninstall_parser.set_defaults(func=uninstall)


def _main() -> None:
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
    first = next((arg for arg in sys.argv[1:] if arg != '--non-interactive'), None)
    # Diagnostics must work even when module configuration is corrupt, and help/version
    # must not initialize or migrate user state.
    if first not in ('doctor', '--help', '-h', '--version', '-v'):
        load_and_register_modules(subparsers)
    elif first in ('--help', '-h'):
        # Show available commands without loading (and potentially rewriting) user config.
        from .modules.module_manager import AVAILABLE_MODULES
        parser.epilog = (parser.epilog or "") + "\nModule commands: " + ', '.join(
            command for info in AVAILABLE_MODULES.values() for command in info['commands'])
    
    # Enable autocomplete if argcomplete is installed
    try:
        import argcomplete  # Optional dependency
        argcomplete.autocomplete(parser)
    except ImportError:
        pass
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle version flag early (before subcommands)
    if args.command is None and getattr(args, 'version', False):
        display_version(args)
        return
    
    # Execute the appropriate function
    if hasattr(args, 'func'):
        token = NON_INTERACTIVE.set(args.non_interactive or not sys.stdin.isatty())
        try:
            result = args.func(args)
            if result is False:
                raise CommandError("Command failed. See diagnostics above.")
            if type(result) is int and result != 0:
                sys.exit(result)
        finally:
            NON_INTERACTIVE.reset(token)
    else:
        parser.print_help()


def main() -> None:
    """CLI boundary: actionable errors and predictable failure statuses."""
    try:
        _main()
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        sys.exit(130)
    except EOFError:
        print("Input required. Supply explicit arguments or use an interactive terminal.", file=sys.stderr)
        sys.exit(2)
    except subprocess.TimeoutExpired:
        print("External command timed out.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        # Do not print the command: argv can contain credentials.
        print("External command failed (exit {}).".format(exc.returncode), file=sys.stderr)
        sys.exit(exc.returncode if exc.returncode > 0 else 1)
    except (CommandError, InstallError, OSError, ValueError) as exc:
        print("Error: {}".format(exc), file=sys.stderr)
        sys.exit(1)
