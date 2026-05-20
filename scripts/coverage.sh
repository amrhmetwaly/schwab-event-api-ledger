#!/usr/bin/env bash
# Run the full test suite with coverage and refresh coverage/REPORT.md.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck source=venv-common.sh
source "$(dirname "$0")/venv-common.sh"

export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

if ! PYTHON_BIN="$(venv_common_resolve_python "$ROOT")"; then
  echo "error: no virtualenv found. Run: ./scripts/bootstrap-venv.sh" >&2
  exit 1
fi

mkdir -p coverage

echo "coverage: running tests…" >&2
"$PYTHON_BIN" -m pytest --assert=plain \
  --cov=event_ledger_api \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=html:coverage/html \
  --cov-report=json:coverage/coverage.json \
  "$@"

echo "coverage: writing REPORT.md…" >&2
"$PYTHON_BIN" "$(dirname "$0")/generate_coverage_report.py"
