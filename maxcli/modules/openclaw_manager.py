"""OpenClaw Manager Module for MaxCLI.

This module provides wrappers around the most important local OpenClaw CLI
operations for quickly checking and controlling a local instance.
"""

import argparse

from maxcli.commands.openclaw import (
    openclaw_status_command,
    openclaw_gateway_command,
    openclaw_logs_command,
)


def register_commands(subparsers) -> None:
    """Register OpenClaw management commands.

    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    openclaw_parser = subparsers.add_parser(
        "openclaw",
        help="Manage your local OpenClaw instance",
        description="""
OpenClaw local instance management.

Provides shortcuts for common OpenClaw operations:
- service status checks
- gateway lifecycle operations
- local log inspection
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max openclaw status
  max openclaw gateway status
  max openclaw gateway restart
  max openclaw logs --lines 200
        """,
    )

    openclaw_subparsers = openclaw_parser.add_subparsers(
        title="OpenClaw Commands",
        dest="openclaw_command",
        description="Available local OpenClaw operations",
        metavar="<subcommand>",
    )

    # max openclaw status
    status_parser = openclaw_subparsers.add_parser(
        "status",
        help="Show local OpenClaw status",
        description="Show status overview for your local OpenClaw installation.",
    )
    status_parser.set_defaults(func=openclaw_status_command)

    # max openclaw gateway <action>
    gateway_parser = openclaw_subparsers.add_parser(
        "gateway",
        help="Control OpenClaw gateway service",
        description="Run gateway service actions: status/start/stop/restart.",
    )
    gateway_parser.add_argument(
        "gateway_action",
        choices=["status", "start", "stop", "restart"],
        help="Gateway operation to run",
    )
    gateway_parser.set_defaults(func=openclaw_gateway_command)

    # max openclaw logs
    logs_parser = openclaw_subparsers.add_parser(
        "logs",
        help="Show OpenClaw logs",
        description="Show logs from your local OpenClaw instance.",
    )
    logs_parser.add_argument(
        "--lines",
        type=int,
        default=100,
        help="Number of log lines to show (default: 100)",
    )
    logs_parser.set_defaults(func=openclaw_logs_command)

    # Default behavior for `max openclaw`
    openclaw_parser.set_defaults(func=lambda _: openclaw_parser.print_help())
