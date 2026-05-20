#!/usr/bin/env bash
# Shared venv resolution for repos on macOS Desktop (iCloud-synced).
# Sourcing is optional; functions are safe to call from other scripts.

venv_common_is_desktop_icloud_repo() {
  local root="${1:?repo root required}"
  [[ "$(uname -s)" == Darwin && "$root" == *"/Desktop/"* ]]
}

# Prefer a venv outside iCloud when the repo lives on Desktop.
venv_common_external_dir() {
  echo "${HOME}/.venvs/schwab-event-api-ledger"
}

venv_common_resolve_python() {
  local root="${1:?repo root required}"
  local external local_py

  external="$(venv_common_external_dir)/bin/python"
  if [[ -x "$external" ]]; then
    echo "$external"
    return 0
  fi

  local_py="${root}/.venv/bin/python"
  if [[ -x "$local_py" ]]; then
    echo "$local_py"
    return 0
  fi

  return 1
}

venv_common_warn_if_desktop() {
  local root="${1:?repo root required}"
  if venv_common_is_desktop_icloud_repo "$root"; then
  cat >&2 <<'EOF'
Note: repo is under Desktop (often iCloud-synced). If pytest/pip hang with no output,
run ./scripts/bootstrap-venv.sh (creates ~/.venvs/schwab-event-api-ledger) or move the
project to e.g. ~/Projects/ (not synced).
EOF
  fi
}
