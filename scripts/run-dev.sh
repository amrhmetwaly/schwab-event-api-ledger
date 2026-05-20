#!/usr/bin/env bash
# Dev server: PYTHONPATH=src works even when macOS marks the editable .pth as hidden.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec uvicorn event_ledger_api.main:app --reload --reload-dir src "$@"
