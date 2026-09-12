#!/bin/sh
# Native KiCad workflow for the existing routed board.
set -eu
TASK_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$TASK_ROOT"
exec python3 "tools/export_release.py" "$@"
