#!/usr/bin/env bash
# Reliable test run on macOS (iCloud Desktop): plain assertions, src on PYTHONPATH.
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

if venv_common_is_desktop_icloud_repo "$ROOT" && [[ "$PYTHON_BIN" != "$(venv_common_external_dir)/bin/python" ]]; then
  echo "pytest: Desktop repo with .venv on iCloud — imports can take 5+ minutes with no output." >&2
  echo "pytest: run ./scripts/bootstrap-venv.sh to use ~/.venvs/schwab-event-api-ledger instead." >&2
else
  echo "pytest: starting (loading dependencies)…" >&2
fi

exec "$PYTHON_BIN" -m pytest --assert=plain "$@"
