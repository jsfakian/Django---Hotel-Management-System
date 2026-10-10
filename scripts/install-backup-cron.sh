#!/usr/bin/env bash
# Install / remove / show the daily DB backup cron job.
#
# Usage:
#   ./scripts/install-backup-cron.sh install   # default: 02:00 daily
#   ./scripts/install-backup-cron.sh remove
#   ./scripts/install-backup-cron.sh status
#   CRON_SCHEDULE="0 3 * * *" ./scripts/install-backup-cron.sh install
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DAILY_SCRIPT="$SCRIPT_DIR/backup-daily.sh"
CRON_MARKER="# NEPHELE-DAILY-BACKUP"
CRON_SCHEDULE="${CRON_SCHEDULE:-0 2 * * *}"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.env.prod}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
LOG_FILE="${BACKUP_CRON_LOG:-$PROJECT_DIR/backup/logs/cron-daily.log}"
ACTION="${1:-install}"

mkdir -p "$(dirname "$LOG_FILE")"
chmod +x "$DAILY_SCRIPT" "$SCRIPT_DIR/backup-database.sh"

CRON_LINE="${CRON_SCHEDULE} ENV_FILE=${ENV_FILE} COMPOSE_FILE=${COMPOSE_FILE} ${DAILY_SCRIPT} >> ${LOG_FILE} 2>&1 ${CRON_MARKER}"

current_crontab() {
  crontab -l 2>/dev/null || true
}

strip_marker() {
  current_crontab | grep -vF "$CRON_MARKER" || true
}

case "$ACTION" in
  install)
    TMP="$(mktemp)"
    strip_marker > "$TMP"
    echo "$CRON_LINE" >> "$TMP"
    crontab "$TMP"
    rm -f "$TMP"
    echo "Installed daily backup cron:"
    echo "  $CRON_LINE"
    echo "Logs: $LOG_FILE"
    ;;
  remove)
    TMP="$(mktemp)"
    strip_marker > "$TMP"
    if [[ -s "$TMP" ]]; then
      crontab "$TMP"
    else
      crontab -r 2>/dev/null || true
    fi
    rm -f "$TMP"
    echo "Removed NEPHELE daily backup cron job (if present)."
    ;;
  status)
    echo "Marked cron entries:"
    current_crontab | grep -F "$CRON_MARKER" || echo "(none)"
    ;;
  *)
    echo "Usage: $0 {install|remove|status}" >&2
    exit 1
    ;;
esac
