#!/usr/bin/env bash
# Python/Django hygiene: cyclomatic complexity (radon/xenon) + flake8.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null; then
  PY="$(command -v python3)"
else
  PY="$(command -v python)"
fi

"${PY}" -m pip install -q -r "${ROOT}/nephele/requirements-hygiene.txt"

EXCLUDE='nephele/*/migrations/*,nephele/migrations/*,*/tests/*,nephele/tests/*,*/.venv/*,*/staticfiles/*,*/htmlcov/*,*/__pycache__/*'

echo "==> Radon average complexity"
"${PY}" -m radon cc nephele -a -s --exclude "${EXCLUDE}" | tail -5

echo "==> Xenon gates (no block worse than B / module worse than B / avg worse than A)"
"${PY}" -m xenon nephele \
  --max-absolute B \
  --max-modules B \
  --max-average A \
  --exclude "${EXCLUDE}"

echo "==> Flake8 (syntax + McCabe complexity <= 10)"
"${PY}" -m flake8 nephele \
  --max-line-length=100 \
  --extend-exclude=migrations,tests,.venv,staticfiles,htmlcov,__pycache__ \
  --select=E9,F63,F7,F82,C901 \
  --max-complexity=10

echo "✓ Python/Django hygiene passed"
