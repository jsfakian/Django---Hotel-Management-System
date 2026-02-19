# Channel Integration - Quick Reference Card

**Date:** February 20, 2026  
**Keep this tab open during development and operations**

---

## 📋 Project Structure

```
HMS/
├── channels/              # OTA Integration App
│   ├── models.py         # Channel, ChannelBooking
│   ├── views.py          # API endpoints for channels
│   ├── serializers.py    # Request/response validation
│   ├── tasks.py          # Celery tasks for sync
│   ├── admin.py          # Django admin config
│   └── urls.py           # URL routing
│
├── inventory/             # Availability Management App
│   ├── models.py         # RoomAvailability, AvailabilitySyncLog
│   ├── views.py          # API endpoints for inventory
│   ├── serializers.py    # Request/response validation
│   ├── admin.py          # Django admin config
│   └── urls.py           # URL routing
│
├── notifications/         # Email & Alerts App
│   ├── tasks.py          # Celery tasks for emails
│   └── templates/        # Email templates
│
└── settings.py           # Django configuration
```

---

## 🚀 Quick Start Commands

### First Time Setup

```bash
# 1. Navigate to project
cd /home/jsfakian/Documents/src/Django---Hotel-Management-System
cd HMS

# 2. Create virtual environment (one time)
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r ../requirements.txt

# 4. Create database
createdb nephele_hms

# 5. Run migrations
python manage.py migrate

# 6. Create admin user
python manage.py createsuperuser

# 7. Start Django dev server
python manage.py runserver

# 8. Start Celery (in new terminal)
celery -A HMS worker --loglevel=info

# 9. Start Celery Beat (in another new terminal)
celery -A HMS beat --loglevel=info

# 10. Access Django admin
# http://localhost:8000/admin/
```

### Daily Operations

```bash
# Check health
python manage.py shell
>>> from django.db import connection
>>> cursor = connection.cursor()
>>> cursor.execute("SELECT 1")
>>> print("✓ Database OK")

# View logs
tail -f /var/log/nephele/django.log
tail -f /var/log/nephele/celery-worker.log

# Restart services
sudo systemctl restart nephele-gunicorn nephele-celery-worker

# Database backup
pg_dump nephele_hms > backup_$(date +%Y%m%d_%H%M%S).sql

# Database restore
psql nephele_hms < backup_20260220_120000.sql
```

---

## 🔌 Core API Endpoints

### Channels (OTA Management)

```bash
# List all channels
GET /api/v1/channels/
Authorization: Bearer {token}

# Create new channel
POST /api/v1/channels/
Content-Type: application/json
Authorization: Bearer {token}
{
  "property": 1,
  "channel_name": "trivago",
  "account_id": "ACC123",
  "api_key": "KEY123",
  "api_secret": "SEC123",
  "mapping_config": {"room_mappings": {"1": "room_001"}}
}

# Get channel details
GET /api/v1/channels/{id}/
Authorization: Bearer {token}

# Update channel
PATCH /api/v1/channels/{id}/
Authorization: Bearer {token}

# Delete channel
DELETE /api/v1/channels/{id}/
Authorization: Bearer {token}

# Receive webhook booking
POST /api/v1/channels/{id}/bookings/
X-Webhook-Signature: sha256=signature_here
Content-Type: application/json
{
  "channel_booking_id": "BKG123",
  "guest_first_name": "John",
  "guest_last_name": "Doe",
  "guest_email": "john@example.com",
  "check_in": "2026-03-15",
  "check_out": "2026-03-18",
  "room_id": 1,
  "total_price": 300.00
}

# Trigger availability sync
POST /api/v1/channels/{id}/availability/sync/
Authorization: Bearer {token}
{
  "sync_type": "full_sync",
  "date_from": "2026-03-15",
  "date_to": "2026-03-31"
}

# Get sync status
GET /api/v1/channels/{id}/availability/status/
Authorization: Bearer {token}
```

### Inventory (Availability Management)

```bash
# Get property availability
GET /api/v1/inventory/availability/{property_id}/?date_from=2026-03-15&date_to=2026-03-31
Authorization: Bearer {token}

# Update room availability
PUT /api/v1/inventory/rooms/{room_id}/availability/
Authorization: Bearer {token}
{
  "date_from": "2026-03-15",
  "date_to": "2026-03-20",
  "available_units": 0,
  "blocked_units": 1,
  "notes": "Maintenance"
}

# Create overbooking
POST /api/v1/inventory/overbook/
Authorization: Bearer {token}
{
  "room_id": 1,
  "date_from": "2026-03-15",
  "date_to": "2026-03-18",
  "reason": "VIP guest request",
  "notes": "Special accommodation"
}

# View sync logs
GET /api/v1/inventory/sync-log/{property_id}/?status=failed&days=7
Authorization: Bearer {token}
```

---

## 🗂️ Database Models

### Channel Model

```python
Channel
├── id: Integer (PK)
├── property: ForeignKey → Property
├── channel_name: Choice (trivago, booking_com, airbnb, etc.)
├── channel_type: Choice (OTA, META_SEARCH, DIRECT)
├── account_id: String
├── api_key: String (encrypted)
├── api_secret: String (encrypted)
├── mapping_config: JSONField (room/rate mappings)
├── is_active: Boolean
├── sync_enabled: Boolean
├── accept_bookings: Boolean
├── last_sync_at: DateTime
├── error_count: Integer
├── last_error: Text
├── created_at: DateTime
└── updated_at: DateTime
```

### RoomAvailability Model

```python
RoomAvailability
├── id: Integer (PK)
├── room: ForeignKey → Room
├── date: Date
├── total_units: Integer
├── available_units: Integer
├── booked_units: Integer
├── blocked_units: Integer
├── overbooked_units: Integer
├── base_price: Decimal
├── dynamic_price: Decimal
├── is_override: Boolean
├── override_notes: Text
├── updated_by: ForeignKey → User
├── created_at: DateTime
└── updated_at: DateTime
```

### ChannelBooking Model

```python
ChannelBooking
├── id: Integer (PK)
├── channel: ForeignKey → Channel
├── channel_booking_id: String (OTA booking ID)
├── nephele_booking_id: Integer (NEPHELE booking ID)
├── sync_status: Choice (pending, synced, failed, cancelled)
├── channel_data: JSONField (full OTA response)
├── created_at: DateTime
└── updated_at: DateTime
```

### AvailabilitySyncLog Model

```python
AvailabilitySyncLog
├── id: Integer (PK)
├── channel: ForeignKey → Channel
├── sync_type: Choice (full_sync, incremental, date_range)
├── status: Choice (pending, in_progress, success, failed, retry)
├── rooms_affected: Integer
├── date_from: Date
├── date_to: Date
├── attempt_count: Integer
├── error_message: Text
├── response_code: Integer
├── response_data: JSONField
├── next_retry_at: DateTime
├── completed_at: DateTime
├── created_at: DateTime
└── updated_at: DateTime
```

---

## 🔧 Configuration Variables

### Settings to Check

```python
# settings.py must have:

INSTALLED_APPS = [
    # ...
    'channels',
    'inventory',
    'notifications',
]

# Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_TIME_LIMIT = 30 * 60

# Email
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = 'SG.xxx'
DEFAULT_FROM_EMAIL = 'noreply@nephele.io'

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nephele_hms',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 📊 Key Commands for Developers

### Database

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# View migration status
python manage.py showmigrations

# Revert migration
python manage.py migrate channels 0001  # Go to specific migration

# Check for issues
python manage.py check

# Shell (Python REPL with Django)
python manage.py shell
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test channels
python manage.py test inventory

# Run with coverage
coverage run --source='.' manage.py test
coverage report -m

# Test specific class or method
python manage.py test channels.tests.ChannelViewSetTestCase.test_receive_booking
```

### Administration

```bash
# Create admin user
python manage.py createsuperuser

# Change password
python manage.py changepassword admin

# Remove user
python manage.py shell
>>> from accounts.models import User
>>> User.objects.get(username='admin').delete()

# Database shell
python manage.py dbshell  # Opens psql/sqlite prompt
```

### Debugging

```bash
# Enable SQL query logging
python manage.py runserver --verbosity 2

# Profile code
python -m cProfile manage.py runserver

# Memory profiling
python -m memory_profiler manage.py runserver

# Django Debug Toolbar (development only)
# Already configured in settings_dev.py
```

---

## 🔑 Celery Task Commands

### Task Management

```bash
# List all tasks
python manage.py shell
>>> from celery.app import current_app
>>> current_app.tasks

# Inspect active tasks
celery -A HMS inspect active

# Inspect scheduled tasks
celery -A HMS inspect scheduled

# Inspect registered tasks
celery -A HMS inspect registered

# Revoke (cancel) a task
celery -A HMS revoke 'task-id-here' --terminate

# Purge queue (delete all tasks)
celery -A HMS purge

# Check worker status
celery -A HMS inspect ping
```

### Task Monitoring

```bash
# Flower dashboard
flower -A HMS --port=5555

# Command line monitoring
watch -n 1 'celery -A HMS inspect active'

# Check task history
python manage.py shell
>>> from django_celery_results.models import TaskResult
>>> TaskResult.objects.all().order_by('-date_done')[:10]
```

---

## 🐛 Common Troubleshooting Commands

### Quick Diagnostics

```bash
# Check all services running
ps aux | grep -E 'gunicorn|celery|nginx|redis'

# Check ports
lsof -i :8000  # Django
lsof -i :5555  # Flower
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Check disk space
df -h

# Check memory
free -h

# Check logs
tail -100f /var/log/nephele/django.log
tail -100f /var/log/nephele/celery-worker.log
tail -100f /var/log/nephele/error.log
```

### Service Management

```bash
# Start/stop/restart
sudo systemctl start nephele-gunicorn
sudo systemctl stop nephele-gunicorn
sudo systemctl restart nephele-gunicorn

sudo systemctl start nephele-celery-worker
sudo systemctl start nephele-celery-beat

# Check status
sudo systemctl status nephele-*

# View logs
sudo journalctl -u nephele-gunicorn -n 100 -f
sudo journalctl -u nephele-celery-worker -n 100 -f

# Enable on boot
sudo systemctl enable nephele-gunicorn nephele-celery-worker nephele-celery-beat
```

### Redis Monitoring

```bash
# Check Redis
redis-cli ping

# Monitor real-time
redis-cli --stat

# Check queue depth
redis-cli LLEN celery
redis-cli LLEN channel_sync
redis-cli LLEN notifications

# Monitor keys
redis-cli KEYS '*'

# Monitor commands
redis-cli MONITOR

# Clear specific queue
redis-cli DEL channel_sync
```

---

## 📝 Important File Locations

```
/home/jsfakian/Documents/src/Django---Hotel-Management-System/
├── HMS/
│   ├── settings.py          ← UPDATE HERE for config
│   ├── celery.py            ← Celery configuration
│   ├── urls.py              ← Main URL routing
│   └── api_urls.py          ← API URL routing
├── channels/
│   ├── models.py            ← Channel models
│   ├── views.py             ← Channel API views
│   ├── tasks.py             ← Celery tasks
│   └── admin.py             ← Admin config
├── inventory/
│   ├── models.py            ← Availability models
│   ├── views.py             ← Inventory API views
│   └── admin.py             ← Admin config
├── notifications/
│   ├── tasks.py             ← Email tasks
│   └── templates/           ← Email templates
├── requirements.txt         ← Python dependencies
├── manage.py                ← Django management
└── [GUIDES]
    ├── SETUP_TESTING_GUIDE.md
    ├── CELERY_REDIS_SETUP.md
    ├── DEPLOYMENT_CHECKLIST.md
    ├── TROUBLESHOOTING_GUIDE.md
    ├── CHANNEL_INTEGRATION_GUIDE.md
    └── QUICK_REFERENCE.md (← YOU ARE HERE)
```

---

## 🔐 Security Checklist

```
□ API Keys stored in environment variables only
□ Database password not in code
□ SECRET_KEY changed from default
□ DEBUG = False in production
□ HTTPS/TLS enabled
□ CSRF protection enabled
□ JWT tokens use secure algorithm
□ Webhook signatures verified (HMAC-SHA256)
□ Database backups encrypted
□ Logs don't contain sensitive data
□ Admin interface password-protected
□ Staff email addresses validated
□ Regular security updates applied
```

---

## 📞 Support Resources

### Files to Read First

1. **SETUP_TESTING_GUIDE.md** - Local development setup
2. **CELERY_REDIS_SETUP.md** - Async task configuration
3. **DEPLOYMENT_CHECKLIST.md** - Production deployment
4. **TROUBLESHOOTING_GUIDE.md** - Problem solving
5. **CHANNEL_INTEGRATION_GUIDE.md** - Full API reference

### Django Documentation

- **Django Docs:** https://docs.djangoproject.com/en/4.2/
- **Django REST Framework:** https://www.django-rest-framework.org/
- **Celery:** https://docs.celeryproject.org/

### Useful Django Commands

```bash
python manage.py help              # List all commands
python manage.py help migrate      # Help for specific command
python manage.py shell             # Python REPL with Django
python manage.py dbshell           # Database REPL
python manage.py runserver 0:8000  # Run on all interfaces
python manage.py collectstatic     # Collect static files
python manage.py test --keepdb     # Faster tests (keeps DB)
```

---

## 🎯 Critical Checklist for Go-Live

```
BEFORE DEPLOYING TO PRODUCTION:

Database:
  □ PostgreSQL configured and backed up
  □ All migrations applied
  □ Database user has limited permissions
  □ Regular backup schedule configured

Django:
  □ DEBUG = False
  □ SECRET_KEY changed
  □ ALLOWED_HOSTS configured
  □ SECURE_SSL_REDIRECT = True
  □ Static files collected
  □ Email backend configured and tested

Celery/Redis:
  □ Redis running and monitoring enabled
  □ Celery workers configured with systemd
  □ Celery Beat scheduler running
  □ Task timeouts configured
  □ Memory limits set

OTA Channels:
  □ At least 1 channel configured
  □ Webhook URLs deployed
  □ API keys securely stored
  □ Room mappings configured
  □ Test booking received and processed

Notifications:
  □ Email backend tested and working
  □ Staff email addresses verified
  □ Email templates reviewed
  □ Notifications queued and sent

Monitoring:
  □ Logging configured
  □ Error tracking enabled (Sentry)
  □ Health check endpoint working
  □ Alerts configured for critical errors
  □ Database query performance checked

API:
  □ All endpoints tested with real data
  □ Rate limiting configured
  □ CORS properly configured
  □ Authentication working
  □ Error messages don't leak sensitive info

Security:
  □ HTTPS/TLS certificate installed
  □ Firewall properly configured
  □ SQL injection prevention via ORM
  □ CSRF protection enabled
  □ Webhook signatures verified

Operations:
  □ Backup/restore process documented
  □ Team trained on operations
  □ Runbook created for common issues
  □ On-call rotation established
  □ Rollback plan prepared
```

---

**Last Updated:** February 20, 2026  
**Print This Page** - Keep it handy during development and operations!

