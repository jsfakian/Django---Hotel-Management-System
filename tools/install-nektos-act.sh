#!/usr/bin/env bash
# Install nektos/act into tools/bin/act (not the unrelated /usr/bin/act genome tool).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN_DIR="${ROOT}/tools/bin"
VERSION="${NEKTOS_ACT_VERSION:-0.2.89}"
ARCH="$(uname -m)"
case "${ARCH}" in
  x86_64|amd64) ASSET="act_Linux_x86_64.tar.gz" ;;
  aarch64|arm64) ASSET="act_Linux_arm64.tar.gz" ;;
  *)
    echo "Unsupported architecture: ${ARCH}" >&2
    exit 1
    ;;
esac

mkdir -p "${BIN_DIR}"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

URL="https://github.com/nektos/act/releases/download/v${VERSION}/${ASSET}"
echo "Downloading nektos/act v${VERSION} (${ASSET})..."
curl -fsSL "${URL}" -o "${TMP}/act.tgz"
tar -xzf "${TMP}/act.tgz" -C "${TMP}" act
install -m 755 "${TMP}/act" "${BIN_DIR}/act"
echo "Installed: ${BIN_DIR}/act ($("${BIN_DIR}/act" --version))"
