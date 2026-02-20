# Channel Integration - Celery & Redis Setup

**Date:** February 20, 2026

## Overview

The channel integration system uses:
- **Celery** for asynchronous task processing (availability sync, notifications)
- **Redis** as the message broker and result backend
- **Flower** for monitoring Celery workers

## Installation

### 1. Install Redis (Production)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Windows (WSL recommended):**
```bash
# Inside WSL Ubuntu terminal
sudo apt-get install redis-server
redis-server
```

### 2. Verify Redis Installation

```bash
# Test Redis connectivity
redis-cli ping
# Expected output: PONG

# Check Redis info
redis-cli info server
```

## Django Configuration

### 1. Update settings.py

```python
# HMS/settings.py

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Task Routing
CELERY_TASK_ROUTES = {
    'channels.tasks.sync_availability_to_channel': {'queue': 'channel_sync'},
    'channels.tasks.sync_availability_to_channels': {'queue': 'channel_sync'},
    'notifications.tasks.send_channel_booking_alert': {'queue': 'notifications'},
    'notifications.tasks.send_travel_agent_availability_update': {'queue': 'notifications'},
    'notifications.tasks.send_booking_confirmation': {'queue': 'notifications'},
}

# Task Configuration
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_TASK_ACKS_LATE = True

# Retry Configuration
CELERY_TASK_RETRY_KWARGS = {'max_retries': 5}
CELERY_TASK_RETRY_BACKOFF = True
CELERY_TASK_RETRY_BACKOFF_MAX = 600  # Max 10 minutes between retries
CELERY_TASK_RETRY_JITTER = True  # Add randomness to prevent thundering herd

# Celery Beat Schedule (for periodic tasks)
CELERY_BEAT_SCHEDULE = {
    'sync-all-channels-hourly': {
        'task': 'channels.tasks.sync_availability_to_channels',
        'schedule': crontab(minute=0),  # Every hour at :00
        'args': (),
    },
    'cleanup-failed-syncs': {
        'task': 'channels.tasks.cleanup_failed_syncs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'args': (),
    },
}
```

### 2. Create celery.py (if not exists)

```python
# HMS/celery.py

import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.settings')

app = Celery('HMS')

# Load configuration from Django settings, all config keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

### 3. Update manage.py or __init__.py

```python
# HMS/__init__.py

from .celery import app as celery_app

__all__ = ('celery_app',)
```

## Running Celery

### Development Setup

**Terminal 1 - Celery Worker:**
```bash
cd HMS
python manage.py celery -A HMS worker --loglevel=info
```

**Terminal 2 - Celery Beat (Scheduler):**
```bash
cd HMS
python manage.py celery -A HMS beat --loglevel=info
```

**Terminal 3 - Flower (Monitoring):**
```bash
cd HMS
flower -A HMS --port=5555 --broker=redis://localhost:6379/0
```

Access Flower at: http://localhost:5555

### Production Setup (systemd)

**1. Create celery worker service**

```ini
# /etc/systemd/system/nephele-celery-worker.service

[Unit]
Description=NEPHELE Celery Worker
After=network.target

[Service]
Type=forking
User=nephele
Group=nephele
WorkingDirectory=/home/nephele/Django---Hotel-Management-System/HMS
ExecStart=/home/nephele/venv/bin/celery -A HMS worker \
          --logfile=/var/log/nephele/celery-worker.log \
          --pidfile=/var/run/nephele/celery-worker.pid \
          --concurrency=4 \
          --pool=prefork

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**2. Create celery beat service**

```ini
# /etc/systemd/system/nephele-celery-beat.service

[Unit]
Description=NEPHELE Celery Beat Scheduler
After=network.target

[Service]
Type=simple
User=nephele
Group=nephele
WorkingDirectory=/home/nephele/Django---Hotel-Management-System/HMS
ExecStart=/home/nephele/venv/bin/celery -A HMS beat \
          --logfile=/var/log/nephele/celery-beat.log \
          --pidfile=/var/run/nephele/celery-beat.pid \
          --scheduler django_celery_beat.schedulers:DatabaseScheduler

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**3. Enable and start services**

```bash
sudo systemctl daemon-reload
sudo systemctl enable nephele-celery-worker nephele-celery-beat
sudo systemctl start nephele-celery-worker nephele-celery-beat
sudo systemctl status nephele-celery-worker nephele-celery-beat
```

## Testing Celery Tasks

### Test 1: Send Test Notification Task

```python
# Django shell
python manage.py shell

from notifications.tasks import send_channel_booking_alert
from bookings.models import Booking

booking = Booking.objects.latest('id')

# Send async
task = send_channel_booking_alert.delay(booking.id)
print(f"Task ID: {task.id}")
print(f"Task Status: {task.status}")

# Get result
print(f"Result: {task.get()}")
```

### Test 2: Monitor Task Execution

```bash
# Watch Celery worker logs
tail -f /var/log/nephele/celery-worker.log

# Or check Flower at http://localhost:5555
# Look for "Tasks" tab to see execution history
```

### Test 3: Test Availability Sync Task

```python
# Django shell
from channels.tasks import sync_availability_to_channel
from channels.models import Channel

channel = Channel.objects.filter(is_active=True).first()

# Queue sync task
task = sync_availability_to_channel.delay(
    channel_id=channel.id,
    sync_type='full_sync',
    date_from='2026-03-15',
    date_to='2026-03-31'
)

print(f"Sync Task ID: {task.id}")
```

## Redis CLI Commands

### Monitor Active Connections

```bash
redis-cli
> INFO stats
> CLIENT LIST
```

### Check Queue Depth

```bash
redis-cli
> LLEN celery
> LLEN channel_sync
> LLEN notifications
```

### Clear Queue (WARNING: Removes pending tasks)

```bash
redis-cli
> DEL celery
> DEL channel_sync
> DEL notifications
```

### Monitor Real-time Activity

```bash
redis-cli --stat
```

## Troubleshooting

### Issue: "redis.exceptions.ConnectionError"

**Solution:**
```bash
# Verify Redis is running
redis-cli ping
# Should output: PONG

# If not running, start it
redis-server
```

### Issue: "Celery worker not picking up tasks"

**Solution:**
```bash
# Check worker logs
celery -A HMS worker --loglevel=debug

# Verify queue exists
redis-cli LLEN celery

# Restart worker
pkill -f "celery worker"
celery -A HMS worker --loglevel=info
```

### Issue: "Task stuck in PENDING state"

**Solution:**
```bash
# Check task status in Flower
# http://localhost:5555/tasks

# Or check via CLI
python manage.py shell
from celery.result import AsyncResult
from django_celery_results.models import TaskResult

# Find stuck tasks
stuck = TaskResult.objects.filter(status='PENDING', date_done__isnull=True)
for task in stuck:
    print(f"Task {task.id}: {task.task_name}")
    # Revoke if needed
    app.control.revoke(task.id, terminate=True)
```

### Issue: "Memory usage growing in Redis"

**Solution:**
```bash
# Set Redis memory limit in /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru

# Or via CLI
redis-cli CONFIG SET maxmemory 512mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## Performance Tuning

### Worker Concurrency

Multi-process (prefork) for CPU-bound tasks:
```bash
celery -A HMS worker --pool=prefork --concurrency=4
```

Gevent for I/O-bound tasks:
```bash
celery -A HMS worker --pool=gevent --concurrency=100
```

### Priority Queues

Configure in settings.py:
```python
CELERY_TASK_ROUTES = {
    'notifications.tasks.*': {'queue': 'high_priority'},
    'channels.tasks.*': {'queue': 'normal'},
}
```

Run separate workers:
```bash
# High priority worker
celery -A HMS worker -Q high_priority --concurrency=2

# Normal priority worker
celery -A HMS worker -Q normal --concurrency=4
```

### Result Backend Cleanup

```python
# settings.py
CELERY_RESULT_EXPIRES = 3600  # Delete results after 1 hour
CELERY_RESULT_PERSISTENT = False
```

## Monitoring Dashboard

Access Flower: http://localhost:5555

**Key Metrics:**
- Active tasks
- Task execution time
- Failed tasks
- Worker status
- Queue depth

## Production Checklist

- [ ] Redis configured with persistence (AOF or RDB)
- [ ] Redis password configured
- [ ] Celery workers running (systemd services)
- [ ] Celery Beat scheduler running
- [ ] Flower dashboard accessible
- [ ] Log rotation configured
- [ ] Memory limits set on Redis
- [ ] Task timeout values configured
- [ ] Error alerting configured
- [ ] Database monitoring configured

---

**Estimated Setup Time:** 15-20 minutes  
**Difficulty Level:** Medium

