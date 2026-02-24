# Deployment Directory

This directory contains all files and configurations needed for production deployment of the NEPHELE HMS.

---

## Contents

### Docker Composition Files

- **`docker-compose.prod.yml`** - Production Docker Compose configuration with:
  - PostgreSQL database with optimized settings
  - Redis cache and message broker
  - Django application with resource limits
  - Celery worker and beat scheduler
  - Nginx reverse proxy with SSL/TLS
  - Health checks for all services
  - Proper logging configuration
  - Security best practices

### Configuration Files

- **`nginx.conf`** - Nginx reverse proxy configuration with:
  - HTTP to HTTPS redirect
  - SSL/TLS configuration
  - Security headers
  - Rate limiting
  - Gzip compression
  - Caching headers
  - Static file serving

- **`ssl/`** - Directory for SSL/TLS certificates
  - `cert.pem` - Certificate file (from Let's Encrypt or your CA)
  - `key.pem` - Private key file

### Documentation

- **`DEPLOYMENT_GUIDE.md`** - Complete step-by-step production deployment guide
  - Prerequisites and requirements
  - Environment setup
  - First-time deployment steps
  - Ongoing deployment procedures
  - Backup and recovery
  - Health checks
  - Troubleshooting
  - Security considerations

### Related Files (in root directory)

- **`Dockerfile.prod`** - Production-optimized Dockerfile with:
  - Multi-stage build for optimization
  - Non-root user for security
  - Minimal runtime dependencies
  - Gunicorn WSGI server
  - Health checks

- **`.env.prod.example`** - Template for production environment variables
  - All required configuration options
  - Security settings
  - Database credentials (template)
  - Email configuration
  - Stripe integration
  - MyData/AADE integration

### Scripts (in `scripts/` directory)

- **`backup-database.sh`** - Automated database backup script
  - Daily full backups with compression
  - Backup rotation by retention policy
  - Backup integrity verification
  - Encrypted backup option

- **`restore-database.sh`** - Database restore script
  - Restore from compressed or encrypted backups
  - Safety confirmations before destructive operations
  - Verification of restored data

- **`health-check.sh`** - System health verification script
  - Checks HTTP endpoints
  - Verifies database connectivity
  - Checks cache/Redis connectivity
  - Reports overall system health

### GitHub Actions Workflows (in `.github/workflows/`)

- **`deploy-staging.yml`** - Automated staging deployment
  - Triggered on `develop` branch pushes
  - Runs tests, security scans, and builds
  - Deploys to staging environment
  - Performs health checks

- **`deploy-production.yml`** - Automated production deployment
  - Triggered on `main` branch pushes
  - Comprehensive testing and security scanning
  - Requires environment approval
  - Pre-deployment backups
  - Health checks and smoke tests
  - Automatic rollback on failure

---

## Quick Start for Production Deployment

### 1. Prepare

```bash
# Copy from example
cp .env.prod.example .env.prod

# Edit with your production values
nano .env.prod
```

### 2. Set Up SSL Certificates

```bash
mkdir -p deployment/ssl
# Copy your certificates to deployment/ssl/cert.pem and deployment/ssl/key.pem
cp /path/to/cert.pem deployment/ssl/
cp /path/to/key.pem deployment/ssl/
```

### 3. Create Backup Directory

```bash
mkdir -p backup
chmod 755 backup
```

### 4. Make Scripts Executable

```bash
chmod +x scripts/backup-database.sh
chmod +x scripts/restore-database.sh
chmod +x scripts/health-check.sh
```

### 5. Deploy

```bash
# Build and start containers
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec django \
  python manage.py migrate

# Check health
./scripts/health-check.sh
```

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for complete instructions.

---

## Configuration Files Explained

### `.env.prod` Template

**Security Settings:**
```bash
SECRET_KEY=...              # Generate: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DEBUG=False                 # Must be False in production
ALLOWED_HOSTS=...           # Your domain(s)
```

**Database:**
```bash
DB_NAME=hms_production
DB_USER=hms_prod_user
DB_PASSWORD=...             # Strong password (20+ chars)
DB_HOST=postgres
DB_PORT=5432
```

**Email (SMTP):**
```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=...     # App-specific password
```

**Payments (Stripe):**
```bash
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
```

See `.env.prod.example` for all available options.

---

## Docker Compose Explained

### Services

1. **PostgreSQL** - Database
   - Persistent volume: `postgres_data_prod`
   - Health checks every 10s
   - Resource limits: 2 CPU / 2GB RAM

2. **Redis** - Cache & Message Broker
   - Persistent volume: `redis_data_prod`
   - Health checks every 10s
   - Configured with LRU eviction

3. **Django** - Web Application
   - Gunicorn WSGI server on port 8000
   - Resource limits: 2 CPU / 2GB RAM
   - Read-only filesystem for security
   - Health checks every 30s

4. **Celery** - Background Job Worker
   - 4 concurrent workers
   - 1000 tasks per worker limit
   - Resource limits: 2 CPU / 2GB RAM

5. **Celery Beat** - Task Scheduler
   - Triggers scheduled background tasks
   - Database scheduler for persistence
   - Resource limits: 0.5 CPU / 512MB RAM

6. **Nginx** - Reverse Proxy
   - HTTP/HTTPS handling
   - Static file serving
   - Rate limiting
   - Security headers
   - SSL termination

---

## Nginx Configuration Explained

### Key Features

1. **HTTP → HTTPS Redirect**
   ```nginx
   return 301 https://$host$request_uri;
   ```

2. **Security Headers**
   ```nginx
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
   add_header X-Frame-Options "SAMEORIGIN";
   add_header X-Content-Type-Options "nosniff";
   ```

3. **Rate Limiting**
   ```nginx
   limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
   limit_req zone=api_limit burst=20 nodelay;
   ```

4. **Gzip Compression**
   ```nginx
   gzip on;
   gzip_types text/plain text/css application/json application/javascript;
   ```

5. **Caching Headers**
   ```nginx
   location /static/ {
       expires 30d;
       add_header Cache-Control "public, max-age=2592000, immutable";
   }
   ```

---

## Backup Strategy

### Automated Daily Backups

Add to crontab:
```bash
0 2 * * * /path/to/scripts/backup-database.sh >> /var/log/nephele-backup.log 2>&1
```

### Backup Location

Default: `backup/` directory in project root

### Backup Format

```
backup/
├── hms_full_20260224_020000.sql.gz          # Timestamped backup
├── backup_20260224_020000.metadata          # Metadata with hash
├── hms_full_20260223_020000.sql.gz
└── backup.log                               # Backup log file
```

### Retention

- Default: 30 days (adjust with `--retention-days` parameter)
- Automates old backup cleanup

---

## Health Check Endpoints

Once deployed, these endpoints check system health:

```bash
# Complete health check (all services)
curl https://your-domain.com/health/

# Database connectivity only
curl https://your-domain.com/health/db/

# Cache connectivity only  
curl https://your-domain.com/health/cache/

# Legacy health check
curl https://your-domain.com/healthz/
```

Success response (HTTP 200):
```json
{
  "status": "healthy",
  "services": {
    "database": "ok",
    "cache": "ok",
    "celery": "ok"
  },
  "timestamp": "2026-02-24T12:00:00Z"
}
```

Failure response (HTTP 503):
```json
{
  "status": "unhealthy",
  "services": {
    "database": "down",
    "cache": "ok"
  },
  "timestamp": "2026-02-24T12:00:00Z"
}
```

---

## Setting Up GitHub Actions Deployment

### Required Secrets

Add these to GitHub repository settings → Secrets and variables → Actions:

```
STAGING_DEPLOY_KEY        # SSH private key for staging server
STAGING_DEPLOY_HOST       # Staging server hostname
STAGING_DEPLOY_USER       # SSH user for staging
STAGING_DEPLOY_PATH       # Path to app on staging server

PROD_DEPLOY_KEY           # SSH private key for production server
PROD_DEPLOY_HOST          # Production server hostname
PROD_DEPLOY_USER          # SSH user for production
PROD_DEPLOY_PATH          # Path to app on production server
PROD_ENV_FILE             # Entire .env.prod file contents
```

### Deployment Flow

**Staging (on `develop` branch push):**
1. Run tests and security scans
2. Build Docker image
3. Push to registry
4. SSH into staging server
5. Pull and deploy
6. Run migrations
7. Health checks

**Production (on `main` branch push):**
1. Comprehensive testing (80%+ coverage required)
2. Security scanning (Bandit, pip-audit, Semgrep)
3. Docker image vulnerability scan (Trivy)
4. Pre-deployment checks
5. Create database backup
6. SSH into production
7. Pull and deploy
8. Run migrations
9. Health checks and smoke tests
10. Automatic rollback on failure

---

## Monitoring & Logging

### Docker Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f django

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Log Files

Stored in `logs/` volume on server:
- `hms.log` - Application logs
- `errors.log` - Error logs
- Nginx logs in `nginx_logs/` volume

### Log Rotation

Configured automatically with Docker json-file driver
- Max 100MB per file
- Keep 10 rotated files

---

## Security Considerations

### Must Do Before Production

- [ ] Generate new `SECRET_KEY`
- [ ] Use strong database passwords (20+ chars)
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set `DEBUG=False`
- [ ] Update `ALLOWED_HOSTS`
- [ ] Review security headers
- [ ] Set up automated backups
- [ ] Test backup restoration
- [ ] Configure fail2ban or similar
- [ ] Set up log monitoring
- [ ] Enable audit logging

### Ongoing Security

- [ ] Keep Docker and images updated
- [ ] Monitor for dependency vulnerabilities
- [ ] Review logs regularly
- [ ] Test backups monthly
- [ ] Rotate passwords/keys periodically
- [ ] Monitor health checks
- [ ] Apply security patches promptly

---

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check disk space
docker system df

# Clean up
docker system prune -a
```

### Database connection errors

```bash
# Test connection
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U hms -d hms_production

# Check logs
docker-compose -f docker-compose.prod.yml logs postgres
```

### Performance issues

```bash
# Monitor resource usage
docker stats

# Check top processes
docker-compose -f docker-compose.prod.yml exec django \
  ps aux

# Clear cache
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli FLUSHALL
```

### SSL/TLS issues

```bash
# Check certificate validity
openssl x509 -in deployment/ssl/cert.pem -text -noout

# Test SSL connection
openssl s_client -connect yourdomain.com:443
```

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for more troubleshooting steps.

---

## Support Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/stable/howto/deployment/)
- [PostgreSQL Administration](https://www.postgresql.org/docs/current/admin.html)
- [Let's Encrypt](https://letsencrypt.org/)

---

**Last Updated:** February 24, 2026  
**Version:** 1.0  
**Status:** Production Ready
