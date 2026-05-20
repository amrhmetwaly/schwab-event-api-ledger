#!/usr/bin/env bash
# Render the design PDF to a README-friendly PNG (macOS Quick Look).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PDF="${ROOT}/assets/Idempotent_Event_Ledger_Design.pdf"
OUT_DIR="${ROOT}/assets/design-pdf"
PREVIEW="${OUT_DIR}/design-document-preview.png"

mkdir -p "${OUT_DIR}"
qlmanage -t -s 1400 -o "${OUT_DIR}" "${PDF}" >/dev/null
sips -Z 1100 "${OUT_DIR}/Idempotent_Event_Ledger_Design.pdf.png" --out "${PREVIEW}" >/dev/null
rm -f "${OUT_DIR}/Idempotent_Event_Ledger_Design.pdf.png"
echo "Wrote ${PREVIEW}"
