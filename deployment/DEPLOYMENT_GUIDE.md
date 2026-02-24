# Production Deployment Guide for NEPHELE HMS

**Last Updated:** February 24, 2026  
**Version:** 1.0  
**Environment:** Production

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Setup](#environment-setup)
4. [First-Time Deployment](#first-time-deployment)
5. [Ongoing Deployments](#ongoing-deployments)
6. [Backup & Recovery](#backup--recovery)
7. [Health Checks](#health-checks)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)

---

## Prerequisites

### Infrastructure Requirements

- **Server/Cloud Hosting**: AWS, Google Cloud, or Azure
- **OS**: Ubuntu 20.04 LTS or later, or equivalent Linux distribution
- **Resources**:
  - CPU: Minimum 2 cores (4+ recommended)
  - RAM: Minimum 4GB (8GB+ recommended)
  - Disk: Minimum 50GB (100GB+ for backups)
  - Network: Static IP address or domain name

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- git 2.0+
- PostgreSQL client tools (`psql`, `pg_dump`) - for manual operations
- SSL/TLS certificates (Let's Encrypt recommended)

### Network Requirements

- Port 80 (HTTP) - for automatic HTTPS redirect
- Port 443 (HTTPS) - for secure connections
- Port 5432 (PostgreSQL) - internal only (not exposed)
- Port 6379 (Redis) - internal only (not exposed)

---

## Pre-Deployment Checklist

Before deploying to production, ensure:

### Security
- [ ] Generate new `SECRET_KEY` for production
- [ ] Update all database credentials with strong passwords (20+ chars)
- [ ] Generate SSL/TLS certificates (or use Let's Encrypt)
- [ ] Configure firewall rules
- [ ] Set up fail2ban or similar rate limiting
- [ ] Review and update security headers in `deployment/nginx.conf`

### Configuration
- [ ] Create `.env.prod` from `.env.prod.example`
- [ ] Update all environment variables with production values
- [ ] Update `ALLOWED_HOSTS` in `.env.prod`
- [ ] Update `CORS_ALLOWED_ORIGINS` for frontend domain
- [ ] Configure email settings (SMTP credentials)
- [ ] Set up Stripe keys (if payments enabled)
- [ ] Configure MyData/AADE integration (if using)

### Database
- [ ] Create backup of development/staging database
- [ ] Plan database initialization strategy
- [ ] Test database migration procedures
- [ ] Set up backup directory with proper permissions

### Monitoring & Logs
- [ ] Set up log rotation (Docker json-file driver configured)
- [ ] Plan monitoring and alerting setup (optional: Prometheus/Grafana)
- [ ] Configure centralized logging (optional: ELK Stack)
- [ ] Set up uptime monitoring

### SSL/TLS Certificates
- [ ] Obtain SSL certificates (e.g., from Let's Encrypt)
- [ ] Place certificates in `deployment/ssl/`
- [ ] Update paths in `deployment/nginx.conf`
- [ ] Set up certificate auto-renewal

---

## Environment Setup

### 1. Clone the Repository

```bash
cd /opt  # or your preferred location
git clone https://github.com/your-organization/nephele-hms.git
cd nephele-hms
```

### 2. Create Production Environment File

```bash
cp .env.prod.example .env.prod
# Edit with your production values
nano .env.prod
```

**Critical settings to update:**

```bash
# Security
SECRET_KEY=<generate-new-random-secret-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# Database
DB_PASSWORD=<strong-password-20-chars-minimum>
POSTGRES_PASSWORD=<strong-password-20-chars-minimum>

# Django Admin
DJANGO_SUPERUSER_PASSWORD=<strong-password-20-chars-minimum>

# Email (SMTP)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password

# Stripe (if using payments)
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
```

### 3. Set Up SSL Certificates

#### Using Let's Encrypt

```bash
mkdir -p deployment/ssl
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  -d api.yourdomain.com

# Copy certificates to deployment directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem deployment/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem deployment/ssl/key.pem
sudo chown $(whoami):$(whoami) deployment/ssl/*
```

#### Or provide existing certificates

```bash
mkdir -p deployment/ssl
cp /path/to/your/cert.pem deployment/ssl/
cp /path/to/your/key.pem deployment/ssl/
```

### 4. Create Backup Directory

```bash
mkdir -p backup
chmod 755 backup
```

### 5. Make Scripts Executable

```bash
chmod +x scripts/backup-database.sh
chmod +x scripts/restore-database.sh
chmod +x scripts/health-check.sh
```

---

## First-Time Deployment

### 1. Build Docker Images

```bash
docker-compose -f docker-compose.prod.yml build
```

This creates the production Docker images optimized for deployment.

### 2. Start Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Monitor startup with:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

Wait for messages like:
```
hms-django-prod    | Django application started
hms-postgres-prod  | PostgreSQL container ready
```

### 3. Run Database Migrations

```bash
docker-compose -f docker-compose.prod.yml exec django \
  python manage.py migrate
```

### 4. Bootstrap Metadata

```bash
docker-compose -f docker-compose.prod.yml exec django \
  python manage.py bootstrap_metadata
```

### 5. Create Superuser

```bash
docker-compose -f docker-compose.prod.yml exec django \
  python manage.py createsuperuser
```

Or use auto-creation from environment variables (should already be created):

```bash
docker-compose -f docker-compose.prod.yml exec django \
  python manage.py shell -c "from django.contrib.auth import get_user_model; \
  User = get_user_model(); \
  User.objects.get_or_create(username='admin')"
```

### 6. Collect Static Files

```bash
docker-compose -f docker-compose.prod.yml exec django \
  python manage.py collectstatic --noinput
```

### 7. Health Check

```bash
./scripts/health-check.sh http://localhost:8000

# Or check directly
curl -v http://localhost:8000/health/
```

All services should show as "ok".

### 8. Verify Access

- Admin panel: `https://yourdomain.com/admin/`
- API schema: `https://yourdomain.com/api/v1/schema/`
- Health check: `https://yourdomain.com/health/`

---

## Ongoing Deployments

### Deploy New Code

```bash
# 1. Get latest code
git pull origin main

# 2. Rebuild images (if dependencies changed)
docker-compose -f docker-compose.prod.yml build

# 3. Stop services gracefully
docker-compose -f docker-compose.prod.yml down

# 4. Start updated services
docker-compose -f docker-compose.prod.yml up -d

# 5. Run migrations if needed
docker-compose -f docker-compose.prod.yml exec django \
  python manage.py migrate

# 6. Verify health
./scripts/health-check.sh
```

### View Logs

```bash
# Last 100 lines, follow new logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Specific service
docker-compose -f docker-compose.prod.yml logs -f django

# Django errors only
docker-compose -f docker-compose.prod.yml logs django | grep ERROR
```

### Stop Services

```bash
docker-compose -f docker-compose.prod.yml down
```

### Restart Services

```bash
docker-compose -f docker-compose.prod.yml restart
```

---

## Backup & Recovery

### Automated Backups

Set up cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add this line for nightly backup at 2 AM
0 2 * * * /path/to/nephele-hms/scripts/backup-database.sh >> /var/log/nephele-backup.log 2>&1
```

### Manual Backup

```bash
# Full backup with compression
./scripts/backup-database.sh

# Backup with encryption
./scripts/backup-database.sh --encrypt

# Keep backups for 60 days
./scripts/backup-database.sh --retention-days 60
```

Backups are stored in `backup/` directory.

### Restore from Backup

```bash
# List available backups
ls -lh backup/hms_*.sql*

# Restore from specific backup
./scripts/restore-database.sh backup/hms_full_20260224_020000.sql.gz
```

**Warning**: This will DELETE all data and replace with backup contents.

### Verify Backups

```bash
# Check backup integrity
gzip -t backup/hms_full_*.sql.gz

# Check backup size
du -sh backup/hms_full_*.sql*

# View backup log
tail -f backup/backup.log
```

---

## Health Checks

### Automated Health Checks

Configure monitoring to hit the health endpoint every 30 seconds:

```bash
# Basic health check (all services)
curl -v http://localhost:8000/health/

# Database only
curl -v http://localhost:8000/health/db/

# Cache only
curl -v http://localhost:8000/health/cache/
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "cache": "ok"
  },
  "timestamp": "2026-02-24T12:00:00+00:00"
}
```

### Manual Health Check Script

```bash
./scripts/health-check.sh

# Or with custom URL
./scripts/health-check.sh https://yourdomain.com
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs for errors
docker-compose -f docker-compose.prod.yml logs django

# Check Docker disk space
docker system df

# Clean up unused images/volumes
docker system prune -a

# Rebuild from scratch
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Database Not Responding

```bash
# Check database connection
docker-compose -f docker-compose.prod.yml exec django \
  python manage.py dbshell

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Check disk space
docker exec hms-postgres-prod df -h /var/lib/postgresql/data
```

### Memory Issues

```bash
# Monitor memory usage
docker stats

# Check resource limits in docker-compose.prod.yml
# Adjust if needed and restart

# Clear cache
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli FLUSHALL
```

### High CPU Usage

```bash
# Check running tasks
docker-compose -f docker-compose.prod.yml exec django \
  ps aux

# Check Celery workers
docker-compose -f docker-compose.prod.yml exec celery \
  celery -A HMS inspect active

# Reduce worker concurrency if needed (in docker-compose.prod.yml)
```

### SSL Certificate Issues

```bash
# Test SSL configuration
openssl s_client -connect yourdomain.com:443

# Check certificate validity
openssl x509 -in deployment/ssl/cert.pem -text -noout

# Renew certificate
sudo certbot renew --force-renewal

# Copy renewed certificate
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem \
  deployment/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem \
  deployment/ssl/key.pem
sudo chown $(whoami):$(whoami) deployment/ssl/*

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## Security Considerations

### Security Checklist

- [ ] **Never commit `.env.prod` to version control** - Use secure secrets management
- [ ] **Use strong passwords** - Minimum 20 characters, mixed case, numbers, symbols
- [ ] **Keep Docker updated** - Regularly update Docker and base images
- [ ] **Monitor logs** - Set up alerting for errors and suspicious activity
- [ ] **Regular backups** - Automated daily backups with testing
- [ ] **Firewall rules** - Only expose ports 80 and 443
- [ ] **SSH hardening** - Use key-based auth, disable password login
- [ ] **Database backups** - Test restore procedures monthly
- [ ] **SSL certificates** - Auto-renew before expiration
- [ ] **Security updates** - Apply patches promptly

### Running Security Scans

```bash
# Scan Docker images for vulnerabilities
trivy image hms-django:latest

# Check system for security issues
docker-compose -f docker-compose.prod.yml exec django \
  python manage.py check --deploy

# Run security tests
cd HMS && python manage.py test --tag=security
```

### Updating Production Code Safely

1. Test all changes in staging environment first
2. Create full database backup before deployment
3. Deploy during low-traffic period
4. Monitor logs closely for errors
5. Be prepared to rollback quickly
6. Verify all health checks pass

---

## Monitoring & Alerts

### Set Up Monitoring (Optional but Recommended)

### Email Alerts

Configure in `.env.prod`:
```bash
ADMINS=admin@yourdomain.com
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SERVER_EMAIL=errors@yourdomain.com
```

### External Monitoring

Consider using:
- **Uptimerobot**: Free uptime monitoring
- **DataDog**: APM and infrastructure monitoring
- **Sentry**: Error tracking
- **Prometheus + Grafana**: Metrics and visualization

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [PostgreSQL Administration](https://www.postgresql.org/docs/current/admin.html)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [SSL/TLS Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

## Support

For issues or questions:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Run health check: `./scripts/health-check.sh`
3. Check troubleshooting section above
4. Review [INFRASTRUCTURE_TASKS_ANALYSIS.md](../INFRASTRUCTURE_TASKS_ANALYSIS.md)

**Last Updated:** February 24, 2026
