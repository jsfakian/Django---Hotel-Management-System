# NEPHELE HMS - Production Deployment Guide
## Docker Compose Production Setup

**Date Created:** February 24, 2026  
**Last Updated:** February 24, 2026  
**Status:** Production Ready  
**Maintenance:** Gap #1 Implementation

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Deployment Process](#deployment-process)
4. [Verification Steps](#verification-steps)
5. [Production Operations](#production-operations)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Troubleshooting](#troubleshooting)
8. [Backup & Recovery](#backup--recovery)
9. [Scaling & Performance](#scaling--performance)
10. [Security Hardening](#security-hardening)

---

## Pre-Deployment Checklist

### Server Requirements

- [ ] **CPU:** Minimum 2 cores (4 cores recommended for production)
- [ ] **RAM:** Minimum 4GB (8GB recommended)
- [ ] **Disk:** Minimum 50GB SSD (100GB+ recommended)
- [ ] **Network:** Stable internet connection (100Mbps+)
- [ ] **OS:** Ubuntu 20.04+ or RHEL 8+ or similar Linux distribution

### Software Prerequisites

```bash
# Check Docker installation
docker --version
# Expected: Docker version 20.10+

# Check Docker Compose
docker-compose --version
# Expected: Docker Compose version 1.29+

# Check Git
git --version
# Expected: git version 2.30+
```

### Port Availability

Verify these ports are available and not blocked by firewall:

```bash
# Required ports
- 80 (HTTP)
- 443 (HTTPS)
- 9090 (Prometheus)
- 3000 (Grafana)
- 9093 (Alertmanager)

# Optional (internal only):
- 5432 (PostgreSQL - keep internal)
- 6379 (Redis - keep internal)
- 8000 (Django - keep internal)
```

### DNS Configuration

```bash
# Update your DNS records to point to the production server:
yourdomain.com          A  123.45.67.89
www.yourdomain.com      A  123.45.67.89
api.yourdomain.com      A  123.45.67.89
grafana.yourdomain.com  A  123.45.67.89
```

---

## Environment Setup

### Step 1: Clone and Prepare Repository

```bash
# Clone or update repository
cd /opt/hms
git clone https://github.com/your-org/hms.git .
git checkout main
git pull origin main

# Create required directories
mkdir -p deployment/ssl
mkdir -p logs
mkdir -p backup
chmod 700 deployment/ssl
```

### Step 2: Create Production Environment File

```bash
# Copy the environment template
cp deployment/.env.prod.example .env.prod

# Edit with your production values
nano .env.prod
```

**Critical Configuration Items:**

```bash
# 1. DJ ANGO SECRET KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > /tmp/secret.txt
# Copy the output into SECRET_KEY in .env.prod

# 2. DATABASE CREDENTIALS
# Generate strong password (min 16 chars):
openssl rand -base64 16

# 3. DJANGO SUPERUSER
# Change default admin credentials immediately

# 4. SSL CERTIFICATES
# See SSL Certificate section below
```

### Step 3: SSL/TLS Certificates

#### Option A: Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate (requires DNS to be pointing to server)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Copy certificates to deployment/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem deployment/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem deployment/ssl/key.pem
sudo chown 1000:1000 deployment/ssl/*
sudo chmod 600 deployment/ssl/*

# Auto-renewal setup
sudo certbot renew --quiet --no-self-upgrade
# Add to crontab: 0 2 * * * certbot renew --quiet --no-self-upgrade
```

#### Option B: Self-Signed Certificates (Testing Only)

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out deployment/ssl/cert.pem \
  -keyout deployment/ssl/key.pem -days 365 \
  -subj "/C=GR/ST=Crete/L=Rethymno/O=NEPHELE/CN=yourdomain.com"
```

### Step 4: Database Initialization (First-Time Only)

```bash
# Start only the database first
docker-compose -f docker-compose.prod.yml up -d postgres
docker-compose -f docker-compose.prod.yml up -d redis

# Wait for services to be ready
sleep 30

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm django \
  python manage.py migrate --noinput

# Create superuser
docker-compose -f docker-compose.prod.yml run --rm django \
  python manage.py create_superuser \
  --username admin \
  --email admin@yourdomain.com \
  --noinput
# Password will be set from DJANGO_SUPERUSER_PASSWORD in .env.prod

# Collect static files
docker-compose -f docker-compose.prod.yml run --rm django \
  python manage.py collectstatic --noinput

# Bootstrap metadata (one-time setup)
docker-compose -f docker-compose.prod.yml run --rm django \
  python manage.py bootstrap_metadata

# Load demo data (optional)
docker-compose -f docker-compose.prod.yml run --rm django \
  python manage.py load_demo_data --clear
```

---

## Deployment Process

### Step 1: Build Docker Images

```bash
# Build all images with production Dockerfile
docker-compose -f docker-compose.prod.yml build

# Verify images
docker images | grep hms
```

### Step 2: Start Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f --tail=50
```

### Step 3: Verify Services are Healthy

```bash
# Check each service
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U hms_prod_user
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
docker-compose -f docker-compose.prod.yml exec django curl -f http://localhost:8000/api/v1/health/
docker-compose -f docker-compose.prod.yml exec prometheus wget -q -O- http://localhost:9090/-/healthy
```

### Step 4: Enable Auto-Start on Reboot

```bash
# Create systemd service file
sudo tee /etc/systemd/system/hms-docker.service > /dev/null <<EOF
[Unit]
Description=NEPHELE HMS Docker Compose
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/opt/hms
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable hms-docker.service
sudo systemctl start hms-docker.service

# Verify
sudo systemctl status hms-docker.service
```

---

## Verification Steps

### Health Check Script

```bash
#!/bin/bash
# Save as scripts/health-check.sh

echo "=== NEPHELE HMS Production Health Check ==="
echo

# Check Docker
echo "1. Docker Status:"
docker ps -a | grep hms

echo
echo "2. Service Health:"
curl -s http://localhost:8000/api/v1/health/ | python -m json.tool

echo
echo "3. Database Connection:"
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U hms_prod_user -d hms_prod -c "SELECT version();"

echo
echo "4. Redis Connection:"
docker-compose -f docker-compose.prod.yml exec -T redis redis-cli INFO server

echo
echo "5. Prometheus Targets:"
curl -s http://localhost:9090/api/v1/targets | python -m json.tool | grep -A 5 '"labels"'

echo
echo "6. Grafana Status:"
curl -s http://localhost:3000/api/health | python -m json.tool

echo
echo "7. Disk Usage:"
df -h / | tail -1

echo
echo "8. Memory Usage:"
free -h | grep Mem

echo
echo "9. Docker Container Sizes:"
docker ps --format "{{.Names}}" | grep hms | while read container; do
  echo -n "$container: "
  docker ps --format "{{.Size}}" --filter "name=$container"
done

echo
echo "=== Health Check Complete ==="
```

Run it:
```bash
bash scripts/health-check.sh
```

### Access Points

After successful deployment:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Django API** | https://api.yourdomain.com | JWT Token |
| **Django Admin** | https://yourdomain.com/admin | admin / (from .env.prod) |
| **Grafana** | https://grafana.yourdomain.com | admin / (from .env.prod) |
| **Prometheus** | https://yourdomain.com/metrics | (internal only) |
| **Swagger UI** | https://yourdomain.com/api/v1/schema | (public) |

---

## Production Operations

### Daily Operations

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100 django

# Monitor resource usage
watch -n 5 'docker stats --no-stream'

# Check for errors
docker-compose -f docker-compose.prod.yml logs | grep ERROR

# Backup database (see Backup & Recovery section)
bash scripts/backup-database.sh
```

### Updating Application

```bash
# Pull latest code
cd /opt/hms
git pull origin main

# Rebuild images
docker-compose -f docker-compose.prod.yml build

# Stop old containers
docker-compose -f docker-compose.prod.yml down

# Start with new images (blue-green deployment)
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f --tail=50

# Run migrations if needed
docker-compose -f docker-compose.prod.yml run --rm django \
  python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml run --rm django \
  python manage.py collectstatic --noinput
```

### Rolling Back

```bash
# If update causes issues, rollback:
cd /opt/hms
git checkout previous-commit-hash

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

---

## Monitoring & Alerting

### Configure Monitoring

1. **Prometheus Dashboards:** http://localhost:9090
   - Check scrape targets status
   - Verify all services reporting metrics

2. **Grafana Dashboards:** http://localhost:3000
   - System Overview
   - Django Application
   - Database Performance  
   - Celery Tasks

3. **Test Alerts:**
   ```bash
   # Trigger a test alert (stop a service)
   docker-compose -f docker-compose.prod.yml stop redis
   
   # Wait 2-3 minutes and watch alerts in Grafana
   # Then restart
   docker-compose -f docker-compose.prod.yml start redis
   ```

### Alert Configuration

Update alerting destinations in `.env.prod`:

```bash
# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# PagerDuty
PAGERDUTY_SERVICE_KEY=your-pagerduty-key

# Email (configured via SMTP settings)
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Refused

```bash
# Check PostgreSQL status
docker-compose -f docker-compose.prod.yml logs postgres

# Restart database
docker-compose -f docker-compose.prod.yml restart postgres

# Verify connection
docker-compose -f docker-compose.prod.yml exec postgres pg_isready
```

#### 2. Celery Tasks Not Running

```bash
# Check Celery worker
docker-compose -f docker-compose.prod.yml logs celery

# Restart worker
docker-compose -f docker-compose.prod.yml restart celery

# Check Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

#### 3. Out of Disk Space

```bash
# Check disk usage
df -h

# Clean up old logs and containers
docker system prune -a --volumes

# Check container sizes
docker ps -a --format "{{.Names}}" | while read c; do
  echo -n "$c: "
  docker ps --filter "name=$c" --format "{{.Size}}"
done
```

#### 4. High Memory Usage

```bash
# Check memory by container
docker stats

# Increase memory limit in docker-compose.prod.yml
# Or reduce concurrency in .env.prod:
CELERY_WORKER_CONCURRENCY=2  # Reduce from 4
```

---

## Backup & Recovery

See [../scripts/backup-database.sh] for automated backups.

### Manual Backup

```bash
# Database backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump \
  -U hms_prod_user -d hms_prod > backup/hms_$(date +%Y%m%d_%H%M%S).sql

# Full backup including media files
tar -czf backup/hms_full_$(date +%Y%m%d).tar.gz \
  deployment/ \
  HMS/media/ \
  .env.prod
```

### Restore from Backup

```bash
# Restore database
docker-compose -f docker-compose.prod.yml exec -T postgres psql \
  -U hms_prod_user -d hms_prod < backup/hms_20260220_120000.sql

# Restore media files (if backup was full)
tar -xzf backup/hms_full_20260220.tar.gz
```

---

## Scaling & Performance

### Increase Resources

Edit `docker-compose.prod.yml`:

```yaml
services:
  django:
    deploy:
      resources:
        limits:
          cpus: '4'          # Increase from 2
          memory: 4G         # Increase from 2G
        reservations:
          cpus: '2'          # Increase from 1
          memory: 2G         # Increase from 1G
```

### Increase Celery Concurrency

In `.env.prod`:

```bash
CELERY_WORKER_CONCURRENCY=8  # Increase from 4
```

Then restart:

```bash
docker-compose -f docker-compose.prod.yml up -d celery
```

### Database Connection Pooling

In `.env.prod`:

```bash
DB_POOL_SIZE=20  # Increase from 10
DB_POOL_RECYCLE=3600
```

---

## Security Hardening

### 1. Enable HTTPS

✅ Already configured in `deployment/nginx.conf` with SSL/TLS

### 2. Set Strong Passwords

```bash
# Generate password
openssl rand -base64 16

# Update in .env.prod
POSTGRES_PASSWORD=your-new-strong-password
DJANGO_SUPERUSER_PASSWORD=your-new-strong-password
```

### 3. Restrict Network Access

```bash
# Update firewall to allow only required ports
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw default deny incoming
sudo ufw enable
```

### 4. Enable Audit Logging

```bash
# Check audit logs in Django admin
# /admin/audit/

# Monitor logs
docker-compose -f docker-compose.prod.yml logs django | grep "User logged in"
```

### 5. Regular Backups

```bash
# Enable automated backups
in .env.prod:
DB_BACKUP_ENABLED=true
DB_BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM UTC
```

---

## Maintenance Schedule

### Daily
- [ ] Check health status
- [ ] Review error logs
- [ ] Verify backup completion

### Weekly
- [ ] Review analytics dashboard
- [ ] Check disk usage
- [ ] Verify all services responding

### Monthly
- [ ] Test backup restoration
- [ ] Review security logs
- [ ] Performance optimization
- [ ] Database maintenance

### Quarterly
- [ ] Security audit
- [ ] Update dependencies
- [ ] Capacity planning
- [ ] Disaster recovery drill

---

## Support & Escalation

### Emergency Contacts

- **Production Alert:** @on-call-engineer
- **Database Issues:** @database-team
- **Security Issues:** security@yourdomain.com

### Escalation Path

1. **Level 1:** Check logs and health status
2. **Level 2:** Restart affected service
3. **Level 3:** Roll back recent changes
4. **Level 4:** Restore from backup
5. **Level 5:** Escalate to infrastructure team

---

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL  Backup & Recovery](https://www.postgresql.org/docs/current/backup.html)
- [Nginx Production Configuration](https://nginx.org/en/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

---

**Last Updated:** February 24, 2026  
**Maintained By:** DevOps Team  
**Review Date:** March 24, 2026

