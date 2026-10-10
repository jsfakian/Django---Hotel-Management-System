#!/usr/bin/env bash
# Daily database backup wrapper (used by cron and `make backup-daily`).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.env.prod}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

export ENV_FILE COMPOSE_FILE

exec "$SCRIPT_DIR/backup-database.sh" \
  --env-file "$ENV_FILE" \
  --compose-file "$COMPOSE_FILE" \
  --subdir daily \
  --retention-days "$RETENTION_DAYS"
