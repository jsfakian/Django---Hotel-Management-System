#!/bin/bash
# Database Backup Script for NEPHELE HMS
# Automated backup of PostgreSQL database with rotation

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backup"
ENV_FILE="${PROJECT_DIR}/.env.prod"

# Default values
RETENTION_DAYS=30
BACKUP_TYPE="full"  # full, incremental
COMPRESS=true
ENCRYPT=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --type)
            BACKUP_TYPE="$2"
            shift 2
            ;;
        --encrypt)
            ENCRYPT=true
            shift
            ;;
        --no-compress)
            COMPRESS=false
            shift
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Load environment variables
if [ ! -f "$ENV_FILE" ]; then
    error "Environment file not found: $ENV_FILE"
    exit 1
fi

# Source env file safely
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

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Log file
LOG_FILE="$BACKUP_DIR/backup.log"

{
    log "=== Database Backup Started ==="
    log "Database: $DB_NAME"
    log "Backup Type: $BACKUP_TYPE"
    log "Retention: $RETENTION_DAYS days"
    log "Compression: $COMPRESS"
    log "Encryption: $ENCRYPT"

    # Create timestamp for backup file
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/hms_${BACKUP_TYPE}_${TIMESTAMP}"

    # Check if we can connect to the database
    log "Attempting to connect to database..."
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "${DB_PORT:-5432}" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        -n public \
        > "$BACKUP_FILE.sql" 2>&1 || {
        error "Database backup failed!"
        exit 1
    }

    log "Database dump created: $BACKUP_FILE.sql"

    # Compress if enabled
    if [ "$COMPRESS" = true ]; then
        log "Compressing backup..."
        gzip -f "$BACKUP_FILE.sql"
        BACKUP_FILE="${BACKUP_FILE}.sql.gz"
        log "Backup compressed: $BACKUP_FILE"
    else
        BACKUP_FILE="${BACKUP_FILE}.sql"
    fi

    # Encrypt if enabled (using GPG)
    if [ "$ENCRYPT" = true ]; then
        if ! command -v gpg &> /dev/null; then
            warning "GPG not found, skipping encryption"
        else
            log "Encrypting backup..."
            # Encrypt with symmetric cipher (password-based)
            # For production, consider using GPG keys instead
            gpg --symmetric --cipher-algo AES256 "$BACKUP_FILE"
            BACKUP_FILE="${BACKUP_FILE}.gpg"
            log "Backup encrypted: $BACKUP_FILE"
        fi
    fi

    # Calculate backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup size: $BACKUP_SIZE"

    # Create backup metadata file
    METADATA_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.metadata"
    cat > "$METADATA_FILE" << EOF
Backup Date: $(date)
Database: $DB_NAME
Type: $BACKUP_TYPE
File: $(basename "$BACKUP_FILE")
Size: $BACKUP_SIZE
Compression: $COMPRESS
Encryption: $ENCRYPT
MD5: $(md5sum "$BACKUP_FILE" | awk '{print $1}')
EOF
    log "Metadata file created: $METADATA_FILE"

    # Cleanup old backups based on retention policy
    log "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
    find "$BACKUP_DIR" -name "hms_*.sql*" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "backup_*.metadata" -mtime +$RETENTION_DAYS -delete
    log "Old backups cleaned up"

    # Verify backup integrity
    log "Verifying backup integrity..."
    if [[ "$BACKUP_FILE" == *.sql.gz ]]; then
        if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
            error "Backup integrity check failed!"
            exit 1
        fi
        log "Backup integrity verified"
    fi

    # Log successful completion
    log "=== Backup Completed Successfully ==="
    log "Backup file: $BACKUP_FILE"
    
} | tee -a "$LOG_FILE"

exit 0
