#!/usr/bin/env bash
# Run GitHub Actions workflows locally via nektos/act (tools/bin/act).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

ACT_BIN="${ROOT}/tools/bin/act"
if [[ ! -x "${ACT_BIN}" ]]; then
  echo "nektos/act missing; installing into tools/bin ..."
  bash "${ROOT}/tools/install-nektos-act.sh"
fi

# Prefer repo binary over /usr/bin/act (Artemis Comparison Tool).
export PATH="${ROOT}/tools/bin:${PATH}"

WORKFLOW="${ACT_WORKFLOW:-.github/workflows/tests.yml}"
JOB="${ACT_JOB:-}"
EVENT="${ACT_EVENT:-push}"
PYTHON_VERSION="${ACT_PYTHON_VERSION:-3.14}"

ARGS=(
  "${EVENT}"
  -W "${WORKFLOW}"
  --container-architecture linux/amd64
)

if [[ -n "${JOB}" ]]; then
  ARGS+=(-j "${JOB}")
fi

# Default: one Python matrix cell for faster local feedback on the test job.
if [[ -z "${ACT_FULL_MATRIX:-}" ]]; then
  if [[ -z "${JOB}" || "${JOB}" == "test" ]]; then
    ARGS+=(--matrix "python-version:${PYTHON_VERSION}")
  fi
fi

# Extra args: make ci-local ARGS='-j integration'
if [[ $# -gt 0 ]]; then
  ARGS+=("$@")
fi

echo "Running: ${ACT_BIN} ${ARGS[*]}"
exec "${ACT_BIN}" "${ARGS[@]}"
