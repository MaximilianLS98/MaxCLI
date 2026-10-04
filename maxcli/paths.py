"""Shared paths; development and tests can use an isolated config directory."""
import os
from pathlib import Path


def config_dir() -> Path:
    override = os.environ.get("MAXCLI_CONFIG_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))).expanduser() / "maxcli"
