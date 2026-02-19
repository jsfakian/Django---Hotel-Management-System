# Channel Integration - Configuration & Deployment Checklist

**Date:** February 20, 2026  
**Version:** 1.0

## Pre-Deployment Checklist

### Phase 1: Django Configuration ✓

- [ ] **Python Environment**
  - [ ] Python 3.9+ installed
  - [ ] Virtual environment created: `python -m venv hms`
  - [ ] Dependencies installed: `pip install -r requirements.txt`
  - [ ] Test import: `python manage.py check`

- [ ] **Database**
  - [ ] PostgreSQL 12+ installed and running
  - [ ] Database created: `createdb nephele_hms`
  - [ ] User created with proper permissions
  - [ ] settings.py DATABASE config updated with credentials
  - [ ] Migrations created: `python manage.py makemigrations`
  - [ ] Migrations applied: `python manage.py migrate`
  - [ ] Superuser created: `python manage.py createsuperuser`

- [ ] **Django Settings**
  - [ ] `DEBUG = False` for production
  - [ ] `ALLOWED_HOSTS` configured properly
  - [ ] `SECRET_KEY` changed from default
  - [ ] `CSRF_TRUSTED_ORIGINS` configured
  - [ ] `SECURE_SSL_REDIRECT = True`
  - [ ] `SESSION_COOKIE_SECURE = True`
  - [ ] `CSRF_COOKIE_SECURE = True`
  - [ ] Static files configured: `python manage.py collectstatic --noinput`

- [ ] **Logging**
  - [ ] Logging directory created: `/var/log/nephele/`
  - [ ] Log rotation configured
  - [ ] Error log level set to WARNING in production
  - [ ] Sentry configuration (optional): `SENTRY_DSN` set

### Phase 2: Channel Integration Setup ✓

- [ ] **Admin Interface**
  - [ ] Access Django admin: http://your-domain/admin/
  - [ ] Navigate to "Channels > Channels"
  - [ ] Verify "Channel", "ChannelBooking" models appear

- [ ] **Create Test Channel**
  - [ ] Property selected
  - [ ] Channel name selected (e.g., "Trivago")
  - [ ] Account ID entered
  - [ ] API Key entered (masked in UI)
  - [ ] API Secret entered (masked in UI)
  - [ ] Room mappings JSON configured:
    ```json
    {
      "room_mappings": {
        "1": "channel_room_id_001",
        "2": "channel_room_id_002"
      }
    }
    ```
  - [ ] Channel saved successfully

- [ ] **Initialize Availability**
  - [ ] All rooms have RoomAvailability records
  - [ ] Date range covers next 90 days
  - [ ] Total units set correctly per room
  - [ ] Base prices configured
  - [ ] Run Django shell check:
    ```python
    from inventory.models import RoomAvailability
    from datetime import date
    count = RoomAvailability.objects.filter(date__gte=date.today()).count()
    print(f"Availability records: {count}")
    ```

### Phase 3: Email Configuration ✓

- [ ] **Email Backend Setup**
  - [ ] Choose email service: SendGrid / AWS SES / SMTP
  - [ ] Update settings.py EMAIL_BACKEND

**Option A: SendGrid**
```python
# settings.py
EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
SENDGRID_API_KEY = "SG.your-api-key-here"

EMAIL_FROM_USER = "noreply@nephele.io"
EMAIL_FROM_ADDRESS = "noreply@nephele.io"
```

**Option B: AWS SES**
```python
# settings.py
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'
DEFAULT_FROM_EMAIL = 'noreply@nephele.io'
```

**Option C: SMTP (Gmail/Custom)**
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Use app password, not account password
DEFAULT_FROM_EMAIL = 'noreply@nephele.io'
```

- [ ] **Test Email Configuration**
  ```bash
  python manage.py shell
  from django.core.mail import send_mail
  send_mail(
      'Test Email',
      'This is a test message.',
      'noreply@nephele.io',
      ['test@example.com'],
      fail_silently=False,
  )
  print("Email sent successfully!")
  ```

- [ ] **Configure Staff Email Recipients**
  ```python
  # Django shell - Set staff email addresses
  from accounts.models import User
  from hotel.models import Staff
  
  # Get staff team at property
  staff = Staff.objects.filter(property=your_property, status='active')
  for member in staff:
      print(f"{member.user.email} - {member.role}")
  
  # Verify emails are correct before going live
  ```

### Phase 4: API Keys & External Services ✓

- [ ] **OTA Channel Setup**

**Trivago:**
- [ ] Registered with Trivago Partner Center
- [ ] Account ID obtained
- [ ] API Key generated
- [ ] Webhook URL configured: `https://your-domain/api/v1/channels/{channel_id}/bookings/`
- [ ] Webhook signature secret saved in Channel model

**Booking.com:**
- [ ] Registered with Booking.com Extranet
- [ ] Property ID obtained
- [ ] API Key generated (XML feed / API access)
- [ ] Password generated for OAuth
- [ ] Webhook secret configured

**Airbnb:**
- [ ] Registered with Airbnb Partner API
- [ ] Client ID obtained
- [ ] Client Secret obtained
- [ ] OAuth redirect URI set: `https://your-domain/auth/airbnb/callback/`

**Expedia (EAN API):**
- [ ] EAN API key obtained
- [ ] API secret obtained
- [ ] Property ID mapped

**Additional OTA Platforms:**
- [ ] [ ] Agoda
- [ ] [ ] VRBO
- [ ] [ ] Hotwire
- [ ] [ ] Priceline
- [ ] [ ] Kayak
- [ ] [ ] Others configured as needed

### Phase 5: Celery & Redis Setup ✓

- [ ] **Redis Installation**
  - [ ] Redis server installed
  - [ ] Redis running: `redis-cli ping` → PONG
  - [ ] Redis persistence enabled (AOF or RDB)
  - [ ] Redis password configured in settings.py if needed
  - [ ] Memory limit set: `maxmemory 512mb`

- [ ] **Celery Configuration**
  - [ ] settings.py updated with Celery config
  - [ ] CELERY_BROKER_URL set to Redis
  - [ ] CELERY_RESULT_BACKEND set to Redis
  - [ ] celery.py file created in HMS/
  - [ ] HMS/__init__.py imports celery_app

- [ ] **Celery Workers**
  - [ ] Worker 1: `celery -A HMS worker -Q channel_sync --concurrency=2`
  - [ ] Worker 2: `celery -A HMS worker -Q notifications --concurrency=4`
  - [ ] Celery Beat: `celery -A HMS beat`
  - [ ] Flower: `flower -A HMS --port=5555` (optional monitoring)

- [ ] **Database Scheduler** (Optional)
  - [ ] Run: `python manage.py migrate django_celery_beat`
  - [ ] Schedule periodic syncs in admin: Periodic tasks

### Phase 6: API Security ✓

- [ ] **JWT Authentication**
  - [ ] SIMPLE_JWT settings configured
  - [ ] ACCESS_TOKEN_LIFETIME = 1 hour
  - [ ] REFRESH_TOKEN_LIFETIME = 7 days
  - [ ] Signing algorithm: HS256 (default)
  - [ ] Update algorithm key: `settings.py SIGNING_KEY`

- [ ] **Webhook Signature Verification**
  - [ ] HMAC-SHA256 configured
  - [ ] api_secret stored securely (read-only in admin)
  - [ ] Signature verification in Channel.verify_webhook_signature()
  - [ ] Request signature checked before processing

- [ ] **API Rate Limiting**
  - [ ] Install: `pip install djangorestframework-ratelimit`
  - [ ] Configure in settings.py:
    ```python
    REST_FRAMEWORK = {
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle'
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '100/hour',
            'user': '1000/hour'
        }
    }
    ```

- [ ] **CORS Configuration**
  - [ ] CORS_ALLOWED_ORIGINS configured in settings.py
  - [ ] Only trusted domains listed
  - [ ] CORS_ALLOW_CREDENTIALS = True if needed

- [ ] **API Documentation Access**
  - [ ] Swagger UI accessible (development): `/api/schema/swagger-ui/`
  - [ ] ReDoc accessible: `/api/schema/redoc/`
  - [ ] Schema endpoint: `/api/schema/openapi.json`
  - [ ] Documentation restricted to authenticated users (if needed)

### Phase 7: Monitoring & Logging ✓

- [ ] **Application Logging**
  - [ ] Log directory created: `/var/log/nephele/`
  - [ ] Django logs: `/var/log/nephele/django.log`
  - [ ] Celery logs: `/var/log/nephele/celery-worker.log`
  - [ ] Error logs: `/var/log/nephele/error.log`
  - [ ] Log rotation configured (logrotate)

- [ ] **Error Tracking**
  - [ ] Option A: Sentry configured
    ```python
    import sentry_sdk
    sentry_sdk.init(dsn="your-sentry-dsn")
    ```
  - [ ] Option B: CloudWatch (AWS)
  - [ ] Option C: Custom error logging to database

- [ ] **Performance Monitoring**
  - [ ] Django Debug Toolbar (development only)
  - [ ] Database query logging enabled
  - [ ] Slow query alerts configured
  - [ ] API response time tracking

- [ ] **Health Check Endpoint**
  - [ ] Create `/api/v1/health/` endpoint
  - [ ] Checks: DB, Redis, Celery
  - [ ] Returns 200 OK when healthy

### Phase 8: Production Deployment ✓

- [ ] **Web Server Setup**
  - [ ] Nginx installed and configured
  - [ ] Gunicorn installed
  - [ ] systemd service file created for Gunicorn
  - [ ] Gunicorn running on socket: `/run/nephele/gunicorn.sock`
  - [ ] Nginx proxy_pass configured

- [ ] **SSL/TLS**
  - [ ] SSL certificate obtained (Let's Encrypt)
  - [ ] Nginx SSL configuration set
  - [ ] HSTS header configured: `Strict-Transport-Security`
  - [ ] Redirect HTTP→HTTPS configured

- [ ] **System Services** (systemd)
  - [ ] [ ] nephele-gunicorn.service
  - [ ] [ ] nephele-celery-worker.service
  - [ ] [ ] nephele-celery-beat.service
  - [ ] [ ] nephele-nginx.service
  - [ ] [ ] All services enabled: `sudo systemctl enable nephele-*`

- [ ] **Backups**
  - [ ] Database backup script created
  - [ ] Automated backup schedule (daily at 2 AM)
  - [ ] Backup verification process documented
  - [ ] Off-site backup storage configured

### Phase 9: Testing ✓

- [ ] **Unit Tests**
  - [ ] Run tests: `python manage.py test channels inventory`
  - [ ] Coverage > 80%: `coverage run manage.py test`

- [ ] **Integration Tests**
  - [ ] Test webhook receipt with sample payload
  - [ ] Test availability sync to test OTA
  - [ ] Test staff notification email sending
  - [ ] Test overbooking scenarios

- [ ] **Webhook Testing**
  - [ ] Generate test signature with Python script
  - [ ] Send test booking via curl
  - [ ] Verify booking created in database
  - [ ] Verify availability decremented
  - [ ] Verify notification email sent

- [ ] **Load Testing**
  - [ ] Load test: 100 bookings/hour
  - [ ] Verify availability sync completes < 5 min
  - [ ] Monitor Redis memory usage
  - [ ] Monitor CPU usage on workers

### Phase 10: Documentation & Handoff ✓

- [ ] **API Documentation**
  - [ ] Swagger/OpenAPI spec updated
  - [ ] All endpoints documented with examples
  - [ ] Authentication requirements documented
  - [ ] Error codes documented

- [ ] **Operational Documentation**
  - [ ] Setup guide complete: SETUP_TESTING_GUIDE.md ✓
  - [ ] Celery/Redis guide complete: CELERY_REDIS_SETUP.md ✓
  - [ ] Channel integration guide: CHANNEL_INTEGRATION_GUIDE.md ✓
  - [ ] Troubleshooting guide created
  - [ ] Runbook for common issues created

- [ ] **Runbooks Created**
  - [ ] Adding a new OTA channel
  - [ ] Debugging failed availability sync
  - [ ] Recovering from database issues
  - [ ] Scaling Celery workers
  - [ ] Emergency shutdown procedures

- [ ] **Team Training**
  - [ ] Admin team trained on Django admin interface
  - [ ] Operations team trained on service management
  - [ ] Development team trained on codebase
  - [ ] Support team trained on troubleshooting

## Critical Configuration Values

### Environment Variables (.env file)

```bash
# Django
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key-here
ALLOWED_HOSTS=api.nephele.io,nephele.io

# Database
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=nephele_hms
DATABASE_USER=nephele_user
DATABASE_PASSWORD=secure-password-here
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=sendgrid_backend.SendgridBackend
SENDGRID_API_KEY=SG.your-key-here
DEFAULT_FROM_EMAIL=noreply@nephele.io

# JWT
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ACCESS_TOKEN_LIFETIME=3600  # 1 hour in seconds

# Sentry (Optional)
SENTRY_DSN=https://your-sentry-dsn-here

# AWS (if using AWS services)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1

# OTA API Keys (store securely)
# Don't store in code - use environment or vault
# Reference: Channel model admin for sensitive data
```

## Post-Deployment Verification

✅ **Immediate (Day 1)**
- [ ] Django admin accessible
- [ ] API endpoints responding (401 without auth)
- [ ] Health check endpoint returning 200
- [ ] Celery workers running
- [ ] Logs being written successfully

✅ **First Week**
- [ ] Create test channel and verify
- [ ] Send test webhook and verify booking created
- [ ] Verify notification email received
- [ ] Monitor for errors in logs
- [ ] Verify sync logs populated

✅ **First Month**
- [ ] Run load test
- [ ] Verify no memory leaks in workers
- [ ] Check database growth rate
- [ ] Review error logs for patterns
- [ ] Verify backup restoration

## Rollback Plan

If critical issue discovered:

1. **Stop Traffic**
   - [ ] Disable DNS or remove from load balancer
   - [ ] Prevent new API requests

2. **Revert Code**
   - [ ] Git checkout previous working version
   - [ ] Rebuild and restart services

3. **Restore Data** (if needed)
   - [ ] Restore database from backup
   - [ ] Verify availability data integrity

4. **Communication**
   - [ ] Notify stakeholders of incident
   - [ ] Post status update on status page
   - [ ] Schedule post-mortem

---

**Estimated Completion Time:** 4-6 hours  
**Difficulty Level:** High (Production Deployment)  
**Recommended:** Follow checklist in order, don't skip sections

