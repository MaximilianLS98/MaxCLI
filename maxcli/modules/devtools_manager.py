"""
Developer Tools Manager Module for MaxCLI.

This module provides various developer utilities including:
- JWT token decoding and inspection
- Base64 encoding/decoding (future)
- JSON formatting and validation (future)
- Hash generation (future)
- And other common development tools

The commands are exposed as "max decode <format>" to keep the CLI clean.
"""

import argparse
from maxcli.commands.devtools import register_commands


def register_commands_wrapper(subparsers) -> None:
    """Register developer tools commands.

    This is the entry point called by the module manager.
    It delegates to the devtools commands module.

    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    register_commands(subparsers)
