#!/usr/bin/env bash
# PostgreSQL backup for Nephele (Docker Compose preferred).
#
# Usage:
#   ./scripts/backup-database.sh
#   ENV_FILE=.env COMPOSE_FILE=docker-compose.yml ./scripts/backup-database.sh
#   ./scripts/backup-database.sh --retention-days 7 --subdir daily
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.env.prod}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
COMPOSE="${COMPOSE:-docker compose}"
BACKUP_ROOT="${BACKUP_DIR:-$PROJECT_DIR/backup}"
RETENTION_DAYS=30
SUBDIR=""
COMPRESS=true

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
die() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --retention-days) RETENTION_DAYS="$2"; shift 2 ;;
    --subdir) SUBDIR="$2"; shift 2 ;;
    --no-compress) COMPRESS=false; shift ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    --compose-file) COMPOSE_FILE="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *) die "Unknown option: $1" ;;
  esac
done

[[ -f "$ENV_FILE" ]] || die "Environment file not found: $ENV_FILE"
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

DB_NAME="${POSTGRES_DB:-${DB_NAME:-}}"
DB_USER="${POSTGRES_USER:-${DB_USER:-}}"
DB_PASSWORD="${POSTGRES_PASSWORD:-${DB_PASSWORD:-}}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-${POSTGRES_HOST_PORT:-5432}}"

[[ -n "$DB_NAME" && -n "$DB_USER" && -n "$DB_PASSWORD" ]] \
  || die "Need POSTGRES_DB/USER/PASSWORD (or DB_*) in $ENV_FILE"

OUT_DIR="$BACKUP_ROOT"
[[ -n "$SUBDIR" ]] && OUT_DIR="$BACKUP_ROOT/$SUBDIR"
mkdir -p "$OUT_DIR" "$BACKUP_ROOT/logs"
chmod 700 "$BACKUP_ROOT" 2>/dev/null || true

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RAW_SQL="$OUT_DIR/nephele_full_${TIMESTAMP}.sql"
LOG_FILE="$BACKUP_ROOT/logs/backup_${TIMESTAMP}.log"

postgres_container_running() {
  (cd "$PROJECT_DIR" && $COMPOSE -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -qx postgres)
}

dump_via_docker() {
  log "Dumping via Docker Compose ($COMPOSE_FILE → postgres)"
  (cd "$PROJECT_DIR" && $COMPOSE -f "$COMPOSE_FILE" exec -T \
    -e PGPASSWORD="$DB_PASSWORD" \
    postgres \
    pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner --no-acl) \
    > "$RAW_SQL"
}

dump_via_host() {
  command -v pg_dump >/dev/null || die "pg_dump not found and postgres container is not running"
  log "Dumping via host pg_dump → ${DB_HOST}:${DB_PORT}/${DB_NAME}"
  PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --clean --if-exists --no-owner --no-acl \
    > "$RAW_SQL"
}

{
  log "=== Database backup started ==="
  log "Env: $ENV_FILE | Compose: $COMPOSE_FILE | Retention: ${RETENTION_DAYS}d"

  if postgres_container_running; then
    dump_via_docker
  else
    warn "Postgres service not running in compose; trying host pg_dump"
    dump_via_host
  fi

  [[ -s "$RAW_SQL" ]] || die "Backup file is empty: $RAW_SQL"
  FINAL="$RAW_SQL"

  if [[ "$COMPRESS" == true ]]; then
    log "Compressing…"
    gzip -f "$RAW_SQL"
    FINAL="${RAW_SQL}.gz"
  fi

  SIZE="$(du -h "$FINAL" | cut -f1)"
  MD5="$(md5sum "$FINAL" | awk '{print $1}')"
  cat > "${FINAL}.metadata" <<EOF
Backup Date: $(date -Iseconds)
Database: $DB_NAME
File: $(basename "$FINAL")
Size: $SIZE
MD5: $MD5
Compose: $COMPOSE_FILE
Env: $ENV_FILE
EOF

  log "Cleaning backups older than ${RETENTION_DAYS} days in $OUT_DIR"
  find "$OUT_DIR" -maxdepth 1 \( -name 'nephele_full_*.sql' -o -name 'nephele_full_*.sql.gz' -o -name 'nephele_full_*.metadata' \) \
    -mtime "+$RETENTION_DAYS" -delete 2>/dev/null || true

  if [[ "$FINAL" == *.gz ]]; then
    gzip -t "$FINAL" || die "gzip integrity check failed"
  fi

  log "=== Backup OK: $FINAL ($SIZE) ==="
} 2>&1 | tee -a "$LOG_FILE"
