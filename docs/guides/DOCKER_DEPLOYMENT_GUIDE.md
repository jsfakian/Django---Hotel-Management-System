# Docker Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 2GB disk space for databases

## Quick Start

### 1. Prepare Environment

```bash
# Copy environment template to .env
cp .env.example .env

# Edit .env with your settings (optional, defaults work for local development)
nano .env
```

### 2. Build and Start Services

```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f django
```

The application will:
1. Wait for PostgreSQL to be ready
2. Run database migrations
3. Collect static files
4. Create superuser (if doesn't exist)
5. Start Django development server on http://localhost:8000

### 3. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Django Admin | http://localhost:8000/admin | admin / admin123 |
| Django App | http://localhost:8000 | — |
| PostgreSQL | localhost:5433 | hms / hms_password |
| Redis | localhost:6379 | — |
| Flower (Celery) | http://localhost:5555 | — |

## Service Architecture

```
┌─────────────────────────────────────────────────┐
│                  NGINX Reverse Proxy              │
│                  (Production Only)                │
└─────────────────────┬───────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
    ┌───▼──┐      ┌──▼──┐      ┌──▼──┐
    │Django│      │Redis│      │  PG │
    └───┬──┘      └──┬──┘      └──┬──┘
        │            │            │
        │   ┌────────┤            │
        │   │        │            │
    ┌───▼───▼──┐ ┌──▼───────────▼──┐
    │  Celery  │ │  Celery Beat     │
    │  Worker  │ │  (Scheduler)     │
    └──────────┘ └──────────────────┘
```

## Service Details

### Django (Web Server)
- Python 3.10-slim
- Runs on port 8000
- Auto-reloads on code changes (development)
- Handles HTTP requests

### PostgreSQL (Database)
- Postgres 15 Alpine
- Port 5433 (external), 5432 (internal)
- Volume: `postgres_data:`
- Auto-initializes with migrations

### Redis (Cache & Message Broker)
- Redis 7 Alpine
- Port 6379
- Used by Celery and caching layer
- Volume: `redis_data:`

### Celery Worker
- Processes background tasks
- Depends on Redis and Django
- Auto-retries failed tasks
- Respects task routing and queues

### Celery Beat (Scheduler)
- Schedules periodic tasks
- Daily auto-pricing predictions
- Weekly report generation
- Database-backed scheduler (django_celery_beat)

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f django
docker-compose logs -f celery
docker-compose logs -f postgres
```

### Database Management
```bash
# Run migrations
docker-compose exec django python manage.py migrate

# Shell access
docker-compose exec django python manage.py shell

# Backup database
docker-compose exec postgres pg_dump -U hms hms > backup.sql

# Restore database
docker-compose exec -T postgres psql -U hms hms < backup.sql
```

### Django Admin Tools
```bash
# Create superuser (if doesn't auto-create)
docker-compose exec django python manage.py createsuperuser

# Collect static files
docker-compose exec django python manage.py collectstatic --noinput

# Run tests
docker-compose exec django pytest tests/
```

### Celery Management
```bash
# Inspect active tasks
docker-compose exec django celery -A HMS inspect active

# Inspect stats
docker-compose exec django celery -A HMS inspect stats

# Purge queue
docker-compose exec django celery -A HMS purge

# View scheduled tasks
docker-compose exec django python manage.py shell
# >>> from django_celery_beat.models import PeriodicTask
# >>> PeriodicTask.objects.all()
```

## Development Workflow

### Modify Code
```bash
# Code changes are automatically reloaded
# Check logs to see reload
docker-compose logs -f django | grep "Watching for"
```

### Install New Python Package
```bash
# Add to requirements.docker.txt
echo "new-package==1.0.0" >> requirements.docker.txt

# Rebuild container
docker-compose build django

# Restart service
docker-compose up -d django
```

### Interactive Debugging
```bash
# Django shell
docker-compose exec django python manage.py shell

# Python REPL with Django context
docker-compose exec django python

# Bash shell in container
docker-compose bash django
```

## Production Deployment

### Key Changes for Production

1. **Update .env**
```bash
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CELERY_TASK_ALWAYS_EAGER=False
```

2. **Use Production docker-compose**
```bash
# Production config (add Nginx, security settings)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

3. **Enable HTTPS**
```bash
# Update Nginx config with SSL certificates
# Use Let's Encrypt for free certificates
```

4. **Database Backups**
```bash
# Daily backups
0 2 * * * /path/to/backup.sh
```

5. **Monitor Logs**
```bash
# Check application health
docker-compose ps
docker-compose logs django

# Monitor resource usage
docker stats hms-django hms-postgres hms-redis
```

## Troubleshooting

### Services Won't Start

**Issue**: `docker-compose up` fails
```bash
# Check logs
docker-compose logs

# Rebuild solutions
docker-compose down -v  # Remove volumes
docker-compose build --no-cache
docker-compose up -d
```

**Issue**: Permission denied errors
```bash
# Fix ownership
sudo chown -R $USER:$USER .

# Or run as current user
docker-compose config
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U hms -d hms -c "SELECT 1"

# Check Django connection
docker-compose exec django python manage.py dbshell
```

### Celery Tasks Not Running

```bash
# Check Redis is running
docker-compose exec redis redis-cli ping

# View celery logs
docker-compose logs -f celery

# Check task queue
docker-compose exec django celery -A HMS inspect active_queues
```

### Out of Disk Space

```bash
# Clean up Docker resources
docker system prune -a

# Or remove specific volumes
docker-compose down -v
```

### Ports Already in Use

```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Changed from 8000:8000
  - "5434:5432"  # Changed from 5433:5432

# Or kill the process
lsof -i :8000
kill -9 <PID>
```

## Monitoring and Performance

### View Resource Usage
```bash
docker stats hms-django hms-postgres hms-redis hms-celery
```

### View Container Details
```bash
docker-compose ps
docker inspect hms-django
```

### Check Health Status
```bash
docker-compose ps

# Status should be "healthy"
```

## Cleanup

### Stop All Services
```bash
docker-compose down
```

### Remove All Data (Warning: Destructive)
```bash
docker-compose down -v  # Removes volumes too
```

### Full Reset
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Environment Variables Reference

See `.env.example` for all available configuration options.

Key variables:
- `DEBUG` - Django debug mode (False for production)
- `SECRET_KEY` - Django secret key (change in production!)
- `POSTGRES_PASSWORD` - Database password
- `CELERY_TASK_ALWAYS_EAGER` - Async/sync task execution
- `ALLOWED_HOSTS` - Domain whitelist

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment](https://docs.djangoproject.com/en/4.2/howto/deployment/)
- [Celery Documentation](https://docs.celeryproject.org/)

## Support

For issues and questions:
1. Check Docker logs: `docker-compose logs -f`
2. Check application logs: `/app/logs/`
3. Review environment variables: `cat .env`
4. Check service health: `docker-compose ps`
