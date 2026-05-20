#!/usr/bin/env bash
# Recreate a local .venv that is not broken by iCloud "dataless" placeholders.
# Use when pip/pytest/uvicorn hang with no output, or imports stall on macOS Desktop.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck source=venv-common.sh
source "$(dirname "$0")/venv-common.sh"

if venv_common_is_desktop_icloud_repo "$ROOT"; then
  echo "Note: This repo is under Desktop (iCloud). Creating the virtualenv outside iCloud:"
  echo "      $(venv_common_external_dir)"
  echo "      (.venv will be a symlink). Move the project to ~/Projects/ for a simpler layout."
  echo
fi

echo "Removing old virtualenv ..."
rm -rf .venv
if venv_common_is_desktop_icloud_repo "$ROOT"; then
  rm -rf "$(venv_common_external_dir)"
fi

# Prefer 3.12 on macOS; 3.14 works but is newer than interview baseline (3.11+).
if [[ -z "${PY:-}" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    PY=python3.12
  else
    PY=python3
  fi
fi
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "error: $PY not found" >&2
  exit 1
fi

if venv_common_is_desktop_icloud_repo "$ROOT"; then
  VENV_DIR="$(venv_common_external_dir)"
  mkdir -p "$(dirname "$VENV_DIR")"
  echo "Creating virtualenv with $PY at $VENV_DIR ..."
  "$PY" -m venv "$VENV_DIR"
  ln -sfn "$VENV_DIR" .venv
else
  VENV_DIR="${ROOT}/.venv"
  echo "Creating virtualenv with $PY ..."
  "$PY" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

export PIP_DISABLE_PIP_VERSION_CHECK=1
pip install -U pip wheel

# Non-editable install: avoids hatchling .pth files that iCloud often evicts.
# Tests and ./scripts/run-dev.sh use src/ via pyproject pythonpath / PYTHONPATH.
echo "Installing dependencies (non-editable) ..."
pip install ".[dev]"

if [[ "$(uname -s)" == Darwin ]]; then
  chflags -R nohidden "${VENV_DIR}" 2>/dev/null || true
fi

echo
echo "Done. Activate and verify:"
echo "  source .venv/bin/activate"
echo "  pytest -q"
echo "  ./scripts/run-dev.sh"
