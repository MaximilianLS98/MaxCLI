"""
Setup Manager Module for MaxCLI.

This module provides development environment setup functionality including:
- Minimal terminal and git setup
- Complete development environment with tools and languages
- GUI applications installation
- Interactive setup options
"""

import argparse
from maxcli.commands.setup import setup, minimal_setup, dev_full_setup, apps_setup


def register_commands(subparsers) -> None:
    """Register setup management commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Setup command group
    setup_parser = subparsers.add_parser(
        'setup', 
        help='Setup a new laptop or development environment',
        description="""
Setup utilities for configuring a new laptop or development environment.

This command provides different setup profiles:
- minimal: Basic terminal and git configuration
- dev-full: Complete development environment with tools and languages
- apps: GUI applications for productivity and development

Each setup profile is idempotent - you can run them multiple times safely.
They will skip items that are already installed.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max setup minimal               # Basic terminal setup
  max setup dev-full              # Full development environment
  max setup apps                  # Install GUI applications
        """
    )
    setup_subparsers = setup_parser.add_subparsers(
        title="Setup Profiles", 
        dest="setup_command",
        description="Choose a setup profile based on your needs",
        metavar="<profile>"
    )
    setup_parser.set_defaults(func=setup)

    minimal_parser = setup_subparsers.add_parser(
        'minimal', 
        help='Minimal terminal and git setup for basic development',
        description="""
Install and configure basic development tools for terminal usage.

This lightweight setup includes:
- Homebrew package manager (if not installed)
- Essential command-line tools: git, zsh, wget, htop
- Oh My Zsh for enhanced terminal experience
- Basic git configuration setup

Perfect for:
- Setting up a basic development environment
- Servers or minimal installations
- Users who prefer to manually install additional tools
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max setup minimal              # Install basic development tools
        """
    )
    minimal_parser.set_defaults(func=minimal_setup)

    dev_full_parser = setup_subparsers.add_parser(
        'dev-full', 
        help='Complete development environment with languages and tools',
        description="""
Install a comprehensive development environment with popular tools and languages.

This full setup includes everything from 'minimal' plus:
- Programming languages: Node.js (via nvm), Python
- Container tools: Docker, kubectl  
- Cloud tools: AWS CLI, Google Cloud SDK, Terraform
- Development tools: tmux for terminal multiplexing
- pipx for Python CLI tool management
- Dotfiles cloning and configuration

Perfect for:
- New developer laptops
- Setting up a complete coding environment
- Full-stack development work
- DevOps and cloud development

NOTE: You'll need to update the dotfiles repository URL in the configuration.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  max setup dev-full             # Install complete development environment
        """
    )
    dev_full_parser.set_defaults(func=dev_full_setup)

    apps_parser = setup_subparsers.add_parser(
        'apps', 
        help='Install essential GUI applications for development and productivity',
        description="""
Install popular GUI applications using Homebrew Cask.

By default, this installs all applications:
- Development: Visual Studio Code, Cursor AI Editor, Docker Desktop
- Communication: Slack  
- Browsers: Google Chrome, Arc Browser
- API Testing: Postman
- Terminal: Ghostty (modern GPU-accelerated terminal)

INTERACTIVE MODE: Use --interactive flag to choose specific applications to install.
You can select individual apps, install all, or skip installation entirely.

All applications are installed via Homebrew Cask, making them easy to manage
and update. The installation will skip apps that are already installed.

Perfect for:
- Setting up GUI applications on a new Mac
- Standardizing application installs across team members
- Customizing which productivity applications to install
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max setup apps                 # Install all GUI applications (default)
  max setup apps --interactive   # Choose specific apps to install
  
Interactive mode provides:
- Checkbox selection with Space/Enter (if questionary available)
- Numbered selection with fallback mode
- Options to install all, none, or specific applications
        """
    )
    apps_parser.add_argument('--interactive', action='store_true', help='Interactive app selection')
    apps_parser.set_defaults(func=apps_setup) 