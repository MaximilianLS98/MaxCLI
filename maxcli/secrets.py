"""Secret handling for display and portable configuration backups."""
import getpass
import re
from .runtime import require_interactive


def is_secret(name):
    return bool(re.search(r'password|passphrase|secret|token|api[_-]?key|private[_-]?key|credential', name, re.I))


def redact(value, omit=False):
    if isinstance(value, dict):
        return {key: ('[redacted]' if is_secret(key) else redact(item, omit))
                for key, item in value.items() if not (omit and is_secret(key))}
    if isinstance(value, list):
        return [redact(item, omit) for item in value]
    return value


def prompt_secret(label, current=None):
    require_interactive()
    value = getpass.getpass(label + (' (Enter keeps existing value)' if current else ' (optional)') + ': ')
    return value.strip() or current or ''
