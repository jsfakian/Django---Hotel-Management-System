#!/usr/bin/env bash
# React hygiene: ESLint complexity / hooks / unused directives.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}/frontend"

if [[ ! -d node_modules ]]; then
  npm ci
fi

echo "==> ESLint (complexity + React hygiene)"
npx eslint src --max-warnings 0

echo "==> Production build (catch broken imports)"
npm run build

echo "✓ React hygiene passed"
