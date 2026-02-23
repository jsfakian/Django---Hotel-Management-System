#!/bin/bash
# Production Deployment & Verification Script
# This script validates the system is ready for production deployment

set -e

echo "=============================================="
echo "  PRODUCTION DEPLOYMENT VALIDATOR"
echo "=============================================="

echo ""
echo "Step 1: Checking Docker services..."
docker compose ps

echo ""
echo "Step 2: Running system health check..."
docker compose exec -T django python system_check.py

echo ""
echo "Step 3: Running integration tests..."
docker compose exec -T django python integration_test.py

echo ""
echo "=============================================="
echo "  ✅ DEPLOYMENT VALIDATION COMPLETE"
echo "=============================================="
echo ""
echo "Next steps for production:"
echo "1. Change admin password: docker compose exec django python manage.py changepassword admin"
echo "2. Update environment variables in .env with production values"
echo "3. Set DEBUG=False in Django settings"
echo "4. Configure SSL/HTTPS with nginx reverse proxy"
echo "5. Set up database backups"
echo "6. Configure monitoring/alerting"
echo ""
echo "Access the application at: http://localhost:8000"
echo "Admin interface at:        http://localhost:8000/admin"
echo ""
