#!/usr/bin/env bash
# Restore PostgreSQL from a backup created by backup-database.sh.
#
# Usage:
#   ./scripts/restore-database.sh backup/daily/nephele_full_YYYYMMDD_HHMMSS.sql.gz
#   CONFIRM=yes ./scripts/restore-database.sh path/to/backup.sql.gz
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.env.prod}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
COMPOSE="${COMPOSE:-docker compose}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
die() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

BACKUP_FILE="${1:-}"
[[ -n "$BACKUP_FILE" ]] || {
  echo "Usage: $0 <backup-file.sql|.sql.gz>"
  echo "Available:"
  ls -lht "$PROJECT_DIR"/backup/daily/nephele_full_*.sql* 2>/dev/null | head -10 || true
  ls -lht "$PROJECT_DIR"/backup/nephele_full_*.sql* 2>/dev/null | head -10 || true
  exit 1
}
[[ -f "$BACKUP_FILE" ]] || die "Backup not found: $BACKUP_FILE"
[[ -f "$ENV_FILE" ]] || die "Environment file not found: $ENV_FILE"

# shellcheck source=scripts/lib/load-dotenv.sh
source "$SCRIPT_DIR/lib/load-dotenv.sh"
load_dotenv "$ENV_FILE" || die "Failed to load $ENV_FILE"

DB_NAME="${POSTGRES_DB:-${DB_NAME:-}}"
DB_USER="${POSTGRES_USER:-${DB_USER:-}}"
DB_PASSWORD="${POSTGRES_PASSWORD:-${DB_PASSWORD:-}}"
[[ -n "$DB_NAME" && -n "$DB_USER" && -n "$DB_PASSWORD" ]] \
  || die "Need POSTGRES_DB/USER/PASSWORD (or DB_*) in $ENV_FILE"

if [[ "${CONFIRM:-}" != "yes" ]]; then
  warn "This will REPLACE all data in database '$DB_NAME'."
  read -r -p "Type 'yes' to continue: " reply
  [[ "$reply" == "yes" ]] || { log "Cancelled"; exit 1; }
  read -r -p "Type the database name '$DB_NAME' to confirm: " reply
  [[ "$reply" == "$DB_NAME" ]] || die "Name mismatch; cancelled"
fi

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
RESTORE_SQL="$TEMP_DIR/backup.sql"

if [[ "$BACKUP_FILE" == *.sql.gz ]]; then
  log "Decompressing…"
  gunzip -c "$BACKUP_FILE" > "$RESTORE_SQL"
elif [[ "$BACKUP_FILE" == *.sql ]]; then
  cp "$BACKUP_FILE" "$RESTORE_SQL"
else
  die "Unsupported backup format (use .sql or .sql.gz)"
fi

postgres_running() {
  (cd "$PROJECT_DIR" && $COMPOSE -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -qx postgres)
}

psql_docker() {
  (cd "$PROJECT_DIR" && $COMPOSE -f "$COMPOSE_FILE" exec -T \
    -e PGPASSWORD="$DB_PASSWORD" \
    postgres \
    psql -U "$DB_USER" -d "$1")
}

log "=== Restore started → $DB_NAME ==="

if postgres_running; then
  log "Restoring via Docker Compose ($COMPOSE_FILE)"
  # Dump uses --clean/--if-exists so apply into the existing DB
  psql_docker "$DB_NAME" < "$RESTORE_SQL"
else
  command -v psql >/dev/null || die "psql not found and postgres container is not running"
  DB_HOST="${DB_HOST:-localhost}"
  DB_PORT="${DB_PORT:-${POSTGRES_HOST_PORT:-5432}}"
  log "Restoring via host psql → ${DB_HOST}:${DB_PORT}"
  PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$RESTORE_SQL"
fi

log "=== Restore complete from $BACKUP_FILE ==="
