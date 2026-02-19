# Channel Integration - Troubleshooting Guide

**Date:** February 20, 2026

## Quick Diagnostics

### Health Check Script

```python
# Run: python manage.py shell < health_check.py

from django.db import connection
from channels.models import Channel
from inventory.models import RoomAvailability
from bookings.models import Booking
import redis
from celery.app import shared_task
import os

print("=" * 60)
print("NEPHELE CHANNEL INTEGRATION - HEALTH CHECK")
print("=" * 60)

# 1. Database
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✓ Database: Connected")
except Exception as e:
    print(f"✗ Database: {e}")

# 2. Redis
try:
    r = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    r.ping()
    print("✓ Redis: Connected")
except Exception as e:
    print(f"✗ Redis: {e}")

# 3. Models
try:
    channel_count = Channel.objects.count()
    avail_count = RoomAvailability.objects.count()
    booking_count = Booking.objects.count()
    print(f"✓ Models: {channel_count} channels, {avail_count} availability records, {booking_count} bookings")
except Exception as e:
    print(f"✗ Models: {e}")

# 4. Active Channels
try:
    active = Channel.objects.filter(is_active=True)
    for ch in active:
        print(f"  - {ch.get_channel_name_display()}: {ch.property}")
except Exception as e:
    print(f"✗ Active Channels: {e}")

# 5. Email
try:
    from django.core.mail import send_mail
    # Don't actually send, just test backend
    from django.core.mail import get_connection
    conn = get_connection()
    conn.open()
    conn.close()
    print("✓ Email: Backend accessible")
except Exception as e:
    print(f"✗ Email: {e}")

print("=" * 60)
```

## Common Issues & Solutions

### 1. Webhook Signature Verification Fails

**Symptoms:**
```
400 Bad Request: Invalid webhook signature
```

**Cause:**
- API secret mismatch
- Signature header name wrong
- Payload encoding mismatch
- Signature algorithm mismatch

**Solution:**

```python
# Test signature generation
import hmac
import hashlib
import json

api_secret = "your_api_secret"
payload = json.dumps({
    "channel_booking_id": "TEST-001",
    "guest_first_name": "Test",
    # ... rest of payload
})

# Generate signature
signature = hmac.new(
    api_secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

print(f"Expected signature: {signature}")
```

**Verification:**
```bash
# 1. Verify channel.api_secret matches OTA platform
# Admin > Channels > Select channel > Check api_secret

# 2. Test with signature disabled
# Temporarily remove signature verification to test payload

# 3. Check header name
# OTA may send: "X-Webhook-Signature" or "X-Signature" or custom header
# Check Channel.verify_webhook_signature() for expected header

# 4. Log the signature attempt
# Add this to channels/views.py ChannelViewSet.receive_booking():
print(f"Received signature: {request.META.get('HTTP_X_WEBHOOK_SIGNATURE')}")
print(f"Payload: {request.body}")
```

---

### 2. Bookings Not Being Created

**Symptoms:**
```
POST /api/v1/channels/1/bookings/ returns 201
But booking not found in database
```

**Cause:**
- Room doesn't exist
- Transaction rollback due to constraint
- Availability validation failing
- Guest creation failing

**Solution:**

```python
# Step 1: Verify room exists and belongs to property
from room.models import Room
room = Room.objects.get(id=1)
print(f"Room: {room.room_number}, Property: {room.property}")

# Step 2: Verify availability record exists
from inventory.models import RoomAvailability
from datetime import date
avail = RoomAvailability.objects.get(
    room=room,
    date=date(2026, 3, 15)
)
print(f"Available: {avail.available_units}/{avail.total_units}")

# Step 3: Enable transaction logging
# settings.py:
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

# Step 4: Check ChannelBooking for duplicates
from channels.models import ChannelBooking
duplicate = ChannelBooking.objects.filter(
    channel_booking_id='TEST-001'
).first()
if duplicate:
    print(f"Duplicate found: {duplicate.nephele_booking_id}")
```

---

### 3. Availability Not Syncing to OTA

**Symptoms:**
```
RoomAvailability updated but OTA platform still shows old availability
```

**Cause:**
- Sync task not queued
- Sync task failed silently
- API credentials invalid
- OTA API changed format

**Solution:**

```python
# Step 1: Check sync logs
from inventory.models import AvailabilitySyncLog
from channels.models import Channel

channel = Channel.objects.get(id=1)
logs = AvailabilitySyncLog.objects.filter(
    channel=channel
).order_by('-created_at')[:10]

for log in logs:
    print(f"Status: {log.get_status_display()}")
    print(f"Error: {log.error_message}")
    print(f"Response: {log.response_data}")

# Step 2: Check Celery task status
from celery.result import AsyncResult
task_id = "celery-task-uuid"
result = AsyncResult(task_id)
print(f"Task status: {result.status}")
print(f"Task result: {result.result}")

# Step 3: Manually trigger sync
from channels.tasks import sync_availability_to_channel
task = sync_availability_to_channel.delay(channel_id=1)
print(f"Sync queued: {task.id}")

# Step 4: Check API credentials
print(f"Channel account_id: {channel.account_id}")
print(f"API key masked: {channel.api_key[:10]}...")
print(f"Last sync: {channel.last_sync_at}")
print(f"Error count: {channel.error_count}")
print(f"Last error: {channel.last_error}")

# Step 5: Test API call directly
from channels.tasks import _sync_to_channel_api
try:
    result = _sync_to_channel_api(
        channel_id=1,
        room_ids=[1, 2],
        date_from='2026-03-15',
        date_to='2026-03-31'
    )
    print(f"API result: {result}")
except Exception as e:
    print(f"API error: {e}")
```

---

### 4. Staff Notification Emails Not Sending

**Symptoms:**
```
Booking created successfully
But staff didn't receive notification email
```

**Cause:**
- Email backend not configured
- Celery worker not running
- Invalid email addresses
- SMTP credentials wrong

**Solution:**

```python
# Step 1: Check email configuration
from django.conf import settings
print(f"Email backend: {settings.EMAIL_BACKEND}")
print(f"Default from: {settings.DEFAULT_FROM_EMAIL}")

# Step 2: Test email directly
from django.core.mail import send_mail
try:
    send_mail(
        'Test Subject',
        'Test Body',
        settings.DEFAULT_FROM_EMAIL,
        ['test@example.com'],
        fail_silently=False,
    )
    print("✓ Email sent successfully")
except Exception as e:
    print(f"✗ Email failed: {e}")

# Step 3: Check Celery is running
# Terminal 1: celery -A HMS worker --loglevel=info
# Should show: "celery@hostname ready"

# Step 4: Check task was queued
from celery.result import AsyncResult
from django_celery_results.models import TaskResult

tasks = TaskResult.objects.filter(
    task_name='notifications.tasks.send_channel_booking_alert'
).order_by('-date_done')[:5]

for task in tasks:
    print(f"Task {task.id}: {task.get_status_display()}")
    if task.result:
        print(f"  Result: {task.result}")

# Step 5: Check staff email addresses
from accounts.models import User
from hotel.models import Staff

staff = Staff.objects.filter(is_active=True)
for member in staff:
    print(f"{member.user.email}: {member.role}")

# Step 6: Test notification task directly
from notifications.tasks import send_channel_booking_alert
from bookings.models import Booking

booking = Booking.objects.latest('id')
result = send_channel_booking_alert(booking.id)
print(f"Task result: {result}")
```

---

### 5. Celery Worker Crashes

**Symptoms:**
```
[2026-02-20 10:30:00] CRITICAL/MainProcess] Unhandled exception in worker
```

**Cause:**
- Redis connection lost
- Database connection lost
- Task import error
- Memory exhaustion

**Solution:**

```bash
# Step 1: Check Redis
redis-cli ping
# Expected: PONG

# Step 2: Check Celery worker logs
tail -f /var/log/nephele/celery-worker.log

# Step 3: Start with debug logging
celery -A HMS worker --loglevel=debug

# Step 4: Check for import errors
python -c "from channels.tasks import sync_availability_to_channel; print('OK')"

# Step 5: Check memory usage
free -h
ps aux | grep celery

# Step 6: Restart worker
pkill -f "celery worker"
celery -A HMS worker --concurrency=2 --loglevel=info &
```

---

### 6. Database Queries Timing Out

**Symptoms:**
```
DatabaseError: server closed the connection unexpectedly
OperationalError: (psycopg2.OperationalError) server closed the connection
```

**Cause:**
- Long-running queries
- Database connection pool exhausted
- Network timeout
- Too many concurrent connections

**Solution:**

```python
# Step 1: Identify slow queries
from django.db import connection
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    # Run your query
    from channels.models import Channel
    channels = Channel.objects.all()
    
    for query in connection.queries:
        print(f"Time: {query['time']}, SQL: {query['sql'][:100]}")

# Step 2: Add database indexes (if needed)
# models.py:
class RoomAvailability(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['room', 'date']),
            models.Index(fields=['date', 'available_units']),
        ]

# Step 3: Optimize connection pooling
# settings.py:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 300,  # 5 minutes
        'OPTIONS': {
            'connect_timeout': 10,
            'pool': {
                'min_size': 10,
                'max_size': 20,
            }
        }
    }
}

# Step 4: Use select_related/prefetch_related
channels = Channel.objects.select_related(
    'property'
).prefetch_related(
    'channel_bookings'
)

# Step 5: Check active connections
# PostgreSQL:
psql -d nephele_hms -c "SELECT count(*) FROM pg_stat_activity;"
```

---

### 7. Overbooking Not Working

**Symptoms:**
```
POST /api/v1/inventory/overbook/ returns 400
"Room already overbooked"
```

**Cause:**
- Already at max overbook level
- Date already has booking
- Staff permissions issue

**Solution:**

```python
# Step 1: Check current overbooking status
from inventory.models import RoomAvailability
from datetime import date

avail = RoomAvailability.objects.get(
    room_id=1,
    date=date(2026, 3, 15)
)
print(f"Total: {avail.total_units}")
print(f"Available: {avail.available_units}")
print(f"Booked: {avail.booked_units}")
print(f"Overbooked: {avail.overbooked_units}")
print(f"Blocked: {avail.blocked_units}")

# Step 2: Check max overbook setting
# Should be in settings.py or property settings
MAX_OVERBOOK_PERCENT = 10

allowed_overbook = avail.total_units * (MAX_OVERBOOK_PERCENT / 100)
current_overbook = avail.overbooked_units
print(f"Max allowed overbook: {allowed_overbook}")
print(f"Current overbooked: {current_overbook}")

# Step 3: Check staff permissions
from accounts.models import User
user = User.objects.get(id=request.user.id)
print(f"User role: {user.role}")
print(f"Can overbook: {user.can_manage_availability}")

# Step 4: Create overbook with lower quantity
# Try 0.5 units instead of 1
```

---

### 8. Admin Interface Not Loading

**Symptoms:**
```
404: Not Found when accessing /admin/
```

**Cause:**
- Static files not collected
- URL patterns not configured
- Debug mode disabled

**Solution:**

```bash
# Step 1: Collect static files
python manage.py collectstatic --noinput

# Step 2: Check URL configuration
# HMS/urls.py should include:
# path('admin/', admin.site.urls),

# Step 3: Check DEBUG = True for development
# settings.py: DEBUG = True

# Step 4: Check INSTALLED_APPS
# Should include: 'django.contrib.admin'

# Step 5: Verify permissions
# Django admin requires superuser or staff status
from accounts.models import User
user = User.objects.get(id=1)
print(f"Is staff: {user.is_staff}")
print(f"Is superuser: {user.is_superuser}")
```

---

### 9. API Token Not Working

**Symptoms:**
```
401 Unauthorized: Invalid token
```

**Cause:**
- Token expired
- Token revoked
- Wrong authorization header format
- User inactive

**Solution:**

```python
# Step 1: Get new token
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User

user = User.objects.get(id=1)
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)
print(f"Access Token: {access_token}")

# Step 2: Check token expiration
from rest_framework_simplejwt.tokens import AccessToken
token = AccessToken(access_token)
print(f"Expires: {token['exp']}")

# Step 3: Use correct header format
# Correct: Authorization: Bearer <token>
# Wrong: Authorization: Token <token>
# Wrong: Authorization: <token>

# Step 4: Check user active status
print(f"User active: {user.is_active}")

# Step 5: Refresh token if expired
refresh_token = "your_refresh_token"
client.post('/api/v1/token/refresh/', {
    'refresh': refresh_token
})
```

---

### 10. Memory Leak in Celery Worker

**Symptoms:**
```
Celery worker memory usage grows to GBs
Worker becomes unresponsive
```

**Cause:**
- Tasks not releasing connections
- Large objects in task memory
- Database connection pooling issue

**Solution:**

```bash
# Step 1: Monitor memory usage
# Terminal 1: watch 'ps aux | grep celery'

# Step 2: Set memory limits in settings.py
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Step 3: Use max_tasks_per_child
celery -A HMS worker --max-tasks-per-child=100

# Step 4: Check for connection leaks
# In tasks.py:
from django import db

@shared_task
def my_task():
    try:
        # Do work
        pass
    finally:
        db.connections.close_all()

# Step 5: Restart worker periodically
# Add cron job:
# * * * * * pkill -f "celery worker" && sleep 2 && celery -A HMS worker &

# Step 6: Profile with memory_profiler
pip install memory-profiler
python -m memory_profiler channels/tasks.py
```

---

### 11. Duplicate Bookings Being Created

**Symptoms:**
```
Multiple NEPHELE bookings from single OTA booking
```

**Cause:**
- Webhook retried multiple times
- Duplicate check failing
- Race condition in booking creation

**Solution:**

```python
# Step 1: Verify duplicate detection
from channels.models import ChannelBooking

# Check for duplicates
duplicates = ChannelBooking.objects.values('channel_booking_id').filter(
    channel_booking_id='OTA-123'
).count()
print(f"Duplicates: {duplicates}")

# Step 2: Add transaction isolation
# channels/views.py - receive_booking():
from django.db import transaction

with transaction.atomic():
    # Atomic booking creation

# Step 3: Add unique constraint at database level
# Already in ChannelBooking.Meta.unique_together

# Step 4: Log webhook attempts
import logging
logger = logging.getLogger(__name__)

logger.info(f"Webhook received: channel_booking_id={channel_booking_id}")

# Step 5: Verify constraint in database
# PostgreSQL:
psql -d nephele_hms -c "\d channels_channelbooking"

# Should show unique constraint on (channel_id, channel_booking_id)
```

---

### 12. Property Timezone Issues

**Symptoms:**
```
Availability shows for wrong date
Check-in/out times off by hours
```

**Cause:**
- Django timezone not set to property timezone
- OTA sending UTC instead of local time
- Database storing times without timezone

**Solution:**

```python
# Step 1: Set USE_TZ = True in settings.py
USE_TZ = True
TIME_ZONE = 'UTC'  # Store in UTC

# Step 2: Convert property timezone
from zoneinfo import ZoneInfo
from datetime import datetime

property_tz = property.timezone  # e.g., 'America/New_York'
check_in_local = datetime(2026, 3, 15, 15, 0, tzinfo=ZoneInfo(property_tz))
check_in_utc = check_in_local.astimezone()
print(f"Local: {check_in_local}, UTC: {check_in_utc}")

# Step 3: Update webhook handling
# channels/views.py:
from zoneinfo import ZoneInfo
property_tz = channel.property.timezone
check_in = datetime.fromisoformat(data['check_in']).astimezone()
# Or convert from OTA timezone to property timezone
```

---

## Debug Mode Diagnostics

### Enable Full Django Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/nephele/debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'channels': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'inventory': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    },
}
```

### Check System Resources

```bash
# Disk space
df -h

# Memory
free -h

# CPU
top -b -n 1 | head -20

# Network connections
netstat -an | grep ESTABLISHED | wc -l

# Database connections
psql -d nephele_hms -c "SELECT usename, count(*) FROM pg_stat_activity GROUP BY usename;"

# Redis memory
redis-cli INFO memory
```

---

## When All Else Fails

### Emergency Reset

```bash
# WARNING: This will delete all data. Use only as last resort.

# 1. Stop all services
sudo systemctl stop nephele-*

# 2. Backup database
pg_dump nephele_hms > /backup/nephele_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Reset database
dropdb nephele_hms
createdb nephele_hms

# 4. Run migrations
python manage.py migrate

# 5. Restart services
sudo systemctl start nephele-gunicorn nephele-celery-worker nephele-celery-beat
```

### Rollback to Previous Version

```bash
# 1. Find previous commit
git log --oneline -n 10

# 2. Checkout previous version
git checkout abc1234

# 3. Restart services
sudo systemctl restart nephele-gunicorn

# 4. Run migrations if needed
python manage.py migrate

# 5. Verify health
curl https://your-domain/api/v1/health/
```

---

**Last Updated:** February 20, 2026  
**Version:** 1.0

