"""Validated reads and atomic, owner-only JSON writes."""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from .runtime import CommandError


def read_object(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise CommandError("Cannot read {}: {}".format(path, exc)) from exc
    if not isinstance(data, dict):
        raise CommandError("{} must contain a JSON object".format(path))
    return data


def write_object(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
