#!/bin/bash
# Compatibility entry point for the former bootstrap regression script.
set -euo pipefail
exec "$(dirname -- "${BASH_SOURCE[0]}")/test_bootstrap.sh" "$@"
