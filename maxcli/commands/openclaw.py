"""OpenClaw related commands for local instance management."""

import subprocess
import sys
from typing import List


def _run_openclaw_command(command: List[str]) -> None:
    """Run an openclaw command and forward output.

    Args:
        command: OpenClaw command parts (without the leading `openclaw`).
    """
    try:
        subprocess.run(["openclaw", *command], check=True)
    except FileNotFoundError:
        print("❌ openclaw CLI was not found in PATH.", file=sys.stderr)
        print("💡 Install OpenClaw and ensure `openclaw` is available in your shell.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"❌ OpenClaw command failed with exit code {exc.returncode}.", file=sys.stderr)
        sys.exit(exc.returncode)


def openclaw_status_command(args) -> None:
    """Show overall OpenClaw status."""
    _run_openclaw_command(["status"])


def openclaw_gateway_command(args) -> None:
    """Run OpenClaw gateway action (status/start/stop/restart)."""
    _run_openclaw_command(["gateway", args.gateway_action])


def openclaw_logs_command(args) -> None:
    """Show recent OpenClaw logs."""
    command = ["logs"]
    if args.lines:
        command.extend(["--lines", str(args.lines)])
    _run_openclaw_command(command)
