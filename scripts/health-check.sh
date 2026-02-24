#!/bin/bash
# Health Check Script for NEPHELE HMS
# Verifies that all services are running and healthy

set -e

SERVICE_URL="${1:-http://localhost:8000}"
TIMEOUT=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
log() {
    echo -e "${GREEN}[✓]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo "=== NEPHELE HMS Health Check ==="
echo "Service URL: $SERVICE_URL"
echo ""

FAILED=0

# 1. Check HTTP status
echo "Checking HTTP health endpoint..."
if curl -sf --max-time $TIMEOUT "$SERVICE_URL/health/" > /dev/null 2>&1; then
    log "HTTP health endpoint is responding"
else
    error "HTTP health endpoint is not responding"
    FAILED=$((FAILED + 1))
fi

# 2. Check API schema
echo -n "Checking API schema... "
if curl -sf --max-time $TIMEOUT "$SERVICE_URL/api/v1/schema/" > /dev/null 2>&1; then
    log "API schema is accessible"
else
    error "API schema is not accessible"
    FAILED=$((FAILED + 1))
fi

# 3. Check Django admin
echo -n "Checking Django admin... "
if curl -sf --max-time $TIMEOUT "$SERVICE_URL/admin/" > /dev/null 2>&1; then
    log "Django admin is accessible"
else
    error "Django admin is not accessible"
    FAILED=$((FAILED + 1))
fi

# 4. Check static files
echo -n "Checking static files... "
if curl -sf --max-time $TIMEOUT "$SERVICE_URL/static/admin/" > /dev/null 2>&1; then
    log "Static files are being served"
else
    warning "Static files may not be served (this is OK if using CDN)"
fi

# 5. Check database connectivity
echo -n "Checking database connectivity... "
if timeout $TIMEOUT curl -sf "$SERVICE_URL/health/db/" > /dev/null 2>&1; then
    log "Database connection is working"
else
    error "Database connection failed"
    FAILED=$((FAILED + 1))
fi

# 6. Check cache connectivity
echo -n "Checking Redis/cache connectivity... "
if timeout $TIMEOUT curl -sf "$SERVICE_URL/health/cache/" > /dev/null 2>&1; then
    log "Cache connection is working"
else
    error "Cache connection failed"
    FAILED=$((FAILED + 1))
fi

# Results
echo ""
echo "=== Health Check Results ==="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All health checks passed${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILED health check(s) failed${NC}"
    exit 1
fi
