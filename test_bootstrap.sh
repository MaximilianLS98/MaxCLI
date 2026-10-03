#!/bin/bash
set -euo pipefail
MAXCLI_TEST_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$MAXCLI_TEST_ROOT"
bash -n bootstrap.sh
./bootstrap.sh --help >/dev/null
exec "${MAXCLI_PYTHON:-python3}" -m pytest -o addopts= tests/unit/test_installation.py tests/integration/test_installation_lifecycle.py "$@"
