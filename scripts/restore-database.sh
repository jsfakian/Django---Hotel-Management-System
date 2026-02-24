#!/bin/bash
# Database Restore Script for NEPHELE HMS
# Restore PostgreSQL database from backup

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backup"
ENV_FILE="${PROJECT_DIR}/.env.prod"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Load environment variables
if [ ! -f "$ENV_FILE" ]; then
    error "Environment file not found: $ENV_FILE"
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

# Validate required environment variables
required_vars=("DB_NAME" "DB_USER" "DB_PASSWORD" "DB_HOST")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error "Required environment variable not set: $var"
        exit 1
    fi
done

# Check if backup file is provided
if [ -z "$1" ]; then
    error "Usage: $0 <backup-file>"
    echo "Available backups in $BACKUP_DIR:"
    ls -lht "$BACKUP_DIR"/hms_*.sql* 2>/dev/null | head -10 || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

log "=== Database Restore Started ==="
log "Backup file: $BACKUP_FILE"
log "Target database: $DB_NAME"
log "Target host: $DB_HOST"

# Confirm before restoring
warning "This will DELETE all data in database '$DB_NAME' and restore from backup."
read -p "Are you sure you want to continue? Type 'yes' to confirm: " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log "Restore cancelled"
    exit 1
fi

warning "Last chance to cancel. This action cannot be undone!"
read -p "Type the database name '$DB_NAME' to confirm: " -r
if [[ ! $REPLY == "$DB_NAME" ]]; then
    error "Database name mismatch. Restore cancelled."
    exit 1
fi

{
    log "Connecting to database server..."
    
    # Check database connection
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "${DB_PORT:-5432}" \
        -U "$DB_USER" \
        -d postgres \
        -c "SELECT 1" > /dev/null 2>&1 || {
        error "Cannot connect to database server!"
        exit 1
    }
    log "Database connection successful"

    # Check if backup needs decompression
    RESTORE_FILE="$BACKUP_FILE"
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    if [[ "$BACKUP_FILE" == *.sql.gz ]]; then
        log "Decompressing backup file..."
        RESTORE_FILE="$TEMP_DIR/backup.sql"
        gunzip -c "$BACKUP_FILE" > "$RESTORE_FILE"
        log "Backup decompressed"
    elif [[ "$BACKUP_FILE" == *.sql.gpg ]]; then
        log "Decrypting backup file..."
        if ! command -v gpg &> /dev/null; then
            error "GPG not found, cannot decrypt backup"
            exit 1
        fi
        RESTORE_FILE="$TEMP_DIR/backup.sql"
        gpg --decrypt "$BACKUP_FILE" > "$RESTORE_FILE"
        log "Backup decrypted"
    fi

    # Drop existing connections to the database
    log "Terminating existing connections to $DB_NAME..."
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "${DB_PORT:-5432}" \
        -U "$DB_USER" \
        -d postgres \
        -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
        > /dev/null 2>&1 || true

    # Drop and recreate database
    log "Dropping existing database $DB_NAME..."
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "${DB_PORT:-5432}" \
        -U "$DB_USER" \
        -d postgres \
        -c "DROP DATABASE IF EXISTS \"$DB_NAME\";" \
        > /dev/null 2>&1 || true

    log "Creating new database $DB_NAME..."
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "${DB_PORT:-5432}" \
        -U "$DB_USER" \
        -d postgres \
        -c "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\";" \
        > /dev/null 2>&1 || {
        error "Failed to create database"
        exit 1
    }

    # Restore database from backup
    log "Restoring database from backup... This may take a while..."
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "${DB_PORT:-5432}" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        < "$RESTORE_FILE" || {
        error "Database restore failed!"
        exit 1
    }

    log "=== Database Restore Completed Successfully ==="
    log "Database: $DB_NAME"
    log "Restored from: $BACKUP_FILE"
    log "Restored at: $(date)"

    # Verify restore integrity
    log "Verifying restore integrity..."
    TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "${DB_PORT:-5432}" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
    
    log "Restored tables count: $TABLE_COUNT"

    if [ "$TABLE_COUNT" -eq 0 ]; then
        warning "No tables found in restored database. Restore may have failed."
    else
        log "✓ Restore verification passed"
    fi

} 2>&1

log "=== Restore Process Complete ==="

exit 0
