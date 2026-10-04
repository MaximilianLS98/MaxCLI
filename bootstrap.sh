#!/bin/bash
# Install releases and editable checkouts through one isolated environment manager.
set -euo pipefail
MAXCLI_PYTHON="${MAXCLI_PYTHON:-python3}"
if ! command -v "$MAXCLI_PYTHON" >/dev/null 2>&1; then
    echo 'Python 3.10+ is required. Install Python, then run this script again.' >&2
    exit 1
fi
MAXCLI_SCRIPT_DIR=''
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
    MAXCLI_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
fi
if [[ -n "$MAXCLI_SCRIPT_DIR" && -f "$MAXCLI_SCRIPT_DIR/maxcli/installation.py" ]]; then
    exec "$MAXCLI_PYTHON" "$MAXCLI_SCRIPT_DIR/maxcli/installation.py" "$@"
fi
MAXCLI_TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$MAXCLI_TEMP_DIR"' EXIT
curl --fail --silent --show-error --location \
    https://raw.githubusercontent.com/MaximilianLS98/MaxCLI/main/maxcli/installation.py \
    --output "$MAXCLI_TEMP_DIR/install.py"
"$MAXCLI_PYTHON" "$MAXCLI_TEMP_DIR/install.py" "$@"
