#!/bin/bash
# Backup Automation Setup for NEPHELE HMS
# Sets up automated daily backups with cron scheduling and monitoring

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backup"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log "=== Backup Automation Setup ==="

# Create backup directory structure
log "Creating backup directory structure..."
mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly,emergency,logs}
chmod 700 "$BACKUP_DIR"

log "Directories created:"
log "  - $BACKUP_DIR/daily (daily backups - 7 day retention)"
log "  - $BACKUP_DIR/weekly (weekly backups - 4 week retention)"
log "  - $BACKUP_DIR/monthly (monthly backups - 12 month retention)"
log "  - $BACKUP_DIR/emergency (on-demand backups)"
log "  - $BACKUP_DIR/logs (backup logs)"

# Create backup scripts wrapper
log "Creating backup wrapper scripts..."

# Daily backup script
cat > "$SCRIPT_DIR/backup-daily.sh" << 'DAILY_BACKUP_EOF'
#!/bin/bash
# Daily backup wrapper script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backup/daily"

mkdir -p "$BACKUP_DIR"
cd "$PROJECT_DIR"

# Run daily backup
bash "$SCRIPT_DIR/backup-database.sh" \
    --retention-days 7 \
    --compress \
    2>&1 | tee -a "$BACKUP_DIR/$(date +%Y%m%d_%H%M%S).log"

exit $?
DAILY_BACKUP_EOF

# Weekly backup script
cat > "$SCRIPT_DIR/backup-weekly.sh" << 'WEEKLY_BACKUP_EOF'
#!/bin/bash
# Weekly backup wrapper script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backup/weekly"

mkdir -p "$BACKUP_DIR"
cd "$PROJECT_DIR"

# Run weekly backup
bash "$SCRIPT_DIR/backup-database.sh" \
    --retention-days 28 \
    --compress \
    --type full \
    2>&1 | tee -a "$BACKUP_DIR/$(date +%Y%m%d_%H%M%S).log"

exit $?
WEEKLY_BACKUP_EOF

# Monthly backup script
cat > "$SCRIPT_DIR/backup-monthly.sh" << 'MONTHLY_BACKUP_EOF'
#!/bin/bash
# Monthly backup wrapper script for long-term retention
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backup/monthly"

mkdir -p "$BACKUP_DIR"
cd "$PROJECT_DIR"

# Run monthly backup with encryption
bash "$SCRIPT_DIR/backup-database.sh" \
    --retention-days 365 \
    --compress \
    --encrypt \
    2>&1 | tee -a "$BACKUP_DIR/$(date +%Y%m%d_%H%M%S).log"

exit $?
MONTHLY_BACKUP_EOF

chmod +x "$SCRIPT_DIR/backup-daily.sh"
chmod +x "$SCRIPT_DIR/backup-weekly.sh"
chmod +x "$SCRIPT_DIR/backup-monthly.sh"

log "Backup wrapper scripts created:"
log "  - backup-daily.sh (runs daily, 7-day retention)"
log "  - backup-weekly.sh (runs weekly, 28-day retention)"
log "  - backup-monthly.sh (runs monthly, 365-day retention)"

# Cron entry template
info "Add the following to your crontab (sudo crontab -e):"
echo ""
echo "=================================================="
echo "# NEPHELE HMS Database Backups"
echo "# Daily backup at 2:00 AM"
echo "0 2 * * * cd $PROJECT_DIR && bash $SCRIPT_DIR/backup-daily.sh"
echo ""
echo "# Weekly backup every Sunday at 3:00 AM"
echo "0 3 * * 0 cd $PROJECT_DIR && bash $SCRIPT_DIR/backup-weekly.sh"
echo ""
echo "# Monthly backup on 1st of month at 4:00 AM"
echo "0 4 1 * * cd $PROJECT_DIR && bash $SCRIPT_DIR/backup-monthly.sh"
echo "=================================================="
echo ""

# Backup health check script
log "Creating backup health check script..."

cat > "$SCRIPT_DIR/backup-health-check.sh" << 'HEALTH_CHECK_EOF'
#!/bin/bash
# Backup Health Check Script
# Verifies backup integrity and retention policies

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backup"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Database Backup Health Check ==="
echo "Time: $(date)"
echo ""

check_passed=0
check_failed=0

# Check 1: Backup directory exists
echo -n "✓ Backup directory exists: "
if [ -d "$BACKUP_DIR" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((check_passed++))
else
    echo -e "${RED}FAIL${NC}"
    ((check_failed++))
fi

# Check 2: Recent daily backups
DAILY_COUNT=$(find "$BACKUP_DIR" -name "hms_full_*.sql*" -mtime -1 2>/dev/null | wc -l)
echo -n "✓ Recent daily backups (< 24h): "
if [ "$DAILY_COUNT" -gt 0 ]; then
    echo -e "${GREEN}PASS${NC} ($DAILY_COUNT found)"
    ((check_passed++))
else
    echo -e "${RED}FAIL${NC} (expected at least 1)"
    ((check_failed++))
fi

# Check 3: Backup files have content
echo -n "✓ Backup files are not empty: "
EMPTY_BACKUPS=$(find "$BACKUP_DIR" -name "hms_*.sql*" -not -name "*.metadata" -size 0 2>/dev/null | wc -l)
if [ "$EMPTY_BACKUPS" -eq 0 ]; then
    echo -e "${GREEN}PASS${NC}"
    ((check_passed++))
else
    echo -e "${RED}FAIL${NC} ($EMPTY_BACKUPS empty files found)"
    ((check_failed++))
fi

# Check 4: Total backup size reasonable
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "✓ Total backup directory size: $TOTAL_SIZE"

# Check 5: Oldest backup date
OLDEST_BACKUP=$(find "$BACKUP_DIR" -name "hms_*.sql*" -not -name "*.metadata" -printf '%T@\n' | sort -n | head -1)
if [ -n "$OLDEST_BACKUP" ]; then
    OLDEST_DATE=$(date -d "@${OLDEST_BACKUP%.*}" '+%Y-%m-%d %H:%M:%S')
    echo "✓ Oldest backup: $OLDEST_DATE"
    ((check_passed++))
else
    echo -e "${RED}✗ No backups found${NC}"
    ((check_failed++))
fi

# Check 6: Verify backup integrity
echo ""
echo "Sample backup integrity checks:"
SAMPLE_BACKUPS=$(find "$BACKUP_DIR" -name "hms_*.sql.gz" -not -name "*.metadata" | head -3)
for backup in $SAMPLE_BACKUPS; do
    echo -n "  - $(basename "$backup"): "
    if gzip -t "$backup" 2>/dev/null; then
        echo -e "${GREEN}OK${NC}"
        ((check_passed++))
    else
        echo -e "${RED}CORRUPTED${NC}"
        ((check_failed++))
    fi
done

# Summary
echo ""
echo "=== Health Check Summary ==="
echo -e "Passed: ${GREEN}$check_passed${NC}"
echo -e "Failed: ${RED}$check_failed${NC}"

if [ "$check_failed" -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    exit 1
fi
HEALTH_CHECK_EOF

chmod +x "$SCRIPT_DIR/backup-health-check.sh"
log "Backup health check script created: backup-health-check.sh"

# Restore from latest backup script
log "Creating quick-restore script..."

cat > "$SCRIPT_DIR/restore-latest.sh" << 'RESTORE_LATEST_EOF'
#!/bin/bash
# Quick restore from latest backup script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Quick Restore from Latest Backup ==="

# Find latest backup
LATEST_BACKUP=$(find "$PROJECT_DIR/backup" -name "hms_*.sql*" -not -name "*.metadata" | sort -r | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "No backups found!"
    exit 1
fi

echo "Latest backup: $LATEST_BACKUP"
echo "Backup date: $(stat -c %y "$LATEST_BACKUP")"

# Restore using restore script
bash "$SCRIPT_DIR/restore-database.sh" --file "$LATEST_BACKUP"

exit $?
RESTORE_LATEST_EOF

chmod +x "$SCRIPT_DIR/restore-latest.sh"
log "Quick restore script created: restore-latest.sh"

log "=== Backup Automation Setup Complete ==="
log ""
log "Next steps:"
log "1. Review the cron entries above"
log "2. Run: sudo crontab -e"
log "3. Add the backup cron entries"
log "4. Test backups: bash $SCRIPT_DIR/backup-daily.sh"
log "5. Check health: bash $SCRIPT_DIR/backup-health-check.sh"
log ""

exit 0
