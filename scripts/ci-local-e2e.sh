#!/usr/bin/env bash
# Run Playwright e2e against the local docker-compose stack (same intent as CI e2e job).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

VENV_PY="${ROOT}/.venv/bin/python"
if [[ ! -x "${VENV_PY}" ]]; then
  echo "Creating .venv and installing CI + e2e deps..."
  python3 -m venv "${ROOT}/.venv"
  "${VENV_PY}" -m pip install -U pip
  "${VENV_PY}" -m pip install -r "${ROOT}/requirements-ci.txt"
  "${VENV_PY}" -m pip install -r "${ROOT}/nephele/requirements-test.txt"
fi

"${VENV_PY}" -m pip install -q -r "${ROOT}/nephele/requirements-e2e.txt"
"${ROOT}/.venv/bin/playwright" install --with-deps chromium

E2E_FRONTEND_URL="${E2E_FRONTEND_URL:-http://localhost:3000}"
E2E_API_URL="${E2E_API_URL:-http://localhost:8000}"

echo "Checking API at ${E2E_API_URL} ..."
for i in $(seq 1 60); do
  if curl -fsS "${E2E_API_URL}/" >/dev/null 2>&1 \
    || curl -fsS "${E2E_API_URL}/api/v1/schema/" >/dev/null 2>&1; then
    break
  fi
  if [[ "${i}" -eq 60 ]]; then
    echo "API not reachable. Start the stack first: make up" >&2
    exit 1
  fi
  sleep 2
done

echo "Checking frontend at ${E2E_FRONTEND_URL} ..."
for i in $(seq 1 60); do
  if curl -fsS "${E2E_FRONTEND_URL}/" >/dev/null 2>&1; then
    break
  fi
  if [[ "${i}" -eq 60 ]]; then
    echo "Frontend not reachable. Start the stack first: make up" >&2
    exit 1
  fi
  sleep 2
done

export E2E_FRONTEND_URL E2E_API_URL
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.test_settings}"
export SECRET_KEY="${SECRET_KEY:-test-secret-key-for-ci}"
export DJANGO_SUPERUSER_USERNAME="${DJANGO_SUPERUSER_USERNAME:-admin}"
export DJANGO_SUPERUSER_PASSWORD="${DJANGO_SUPERUSER_PASSWORD:-admin123}"

echo "Running Playwright e2e suite..."
cd "${ROOT}/nephele"
exec "${VENV_PY}" -m pytest tests/e2e/ -v --tb=short -m e2e "$@"
