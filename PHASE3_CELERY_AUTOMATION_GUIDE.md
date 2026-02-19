# Phase 3: Automated Pricing - Celery Setup & Configuration

## Overview

Phase 3 implements automated pricing recommendations using Django Celery tasks. This document covers:

1. **Auto-Pricing Task** - Daily automatic pricing predictions
2. **Alert System** - Low confidence pricing alerts  
3. **Report Generation** - Weekly/monthly pricing analysis
4. **Task Cleanup** - Database maintenance and archival
5. **Celery Configuration** - Queues, scheduling, and routing

## System Requirements

### Required Services

1. **Redis** (Broker & Result Backend)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   
   # Docker
   docker run -d -p 6379:6379 redis:7
   ```

2. **Python Dependencies**
   ```bash
   pip install celery[redis]==5.3.4
   pip install django-celery-beat==2.5.0
   pip install django-celery-results==2.5.0
   ```

### Environment Variables

Add to your `.env` file:

```bash
# Celery Broker Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Development: Run tasks synchronously (no async)
CELERY_TASK_ALWAYS_EAGER=True
CELERY_TASK_EAGER_PROPAGATES=True

# Production: Run tasks asynchronously
CELERY_TASK_ALWAYS_EAGER=False
CELERY_TASK_EAGER_PROPAGATES=False
```

## Configured Tasks

### 1. Auto-Price All Rooms

**Task**: `bookings.tasks.auto_price_all_rooms`

**Schedule**: Daily at midnight UTC

**Function**:
- Predicts optimal price for each active room
- Stores predictions in PricingHistory
- Tracks model confidence scores
- Alerts on low-confidence predictions

**Queue**: `pricing` (priority: 10)

**Time Limit**: 30 minutes

**Parameters**:
- `date_str` (optional): Target date in YYYY-MM-DD format (defaults to today)

**Example**:
```python
from bookings.tasks import auto_price_all_rooms

# Run immediately with default date
result = auto_price_all_rooms.delay()

# Run for specific date
result = auto_price_all_rooms.delay(date_str='2025-12-25')

# Check result
print(result.get())  # Returns {'total_rooms': 50, 'predictions_made': 45, ...}
```

### 2. Low Confidence Alert

**Task**: `bookings.tasks.alert_low_confidence`

**Trigger**: Auto-pricing task when confidence < 80%

**Function**:
- Creates notification records for managers
- Alerts when pricing confidence is below threshold
- Allows manual review before applying price

**Queue**: `notifications` (priority: 8)

**Time Limit**: No specific limit

**Parameters**:
- `room_id`: Room to alert for
- `date`: Date of low-confidence prediction
- `confidence`: Confidence score (0-1)

**Auto-triggered by**: `auto_price_all_rooms` task

### 3. Generate Pricing Report

**Task**: `bookings.tasks.generate_pricing_report`

**Schedules**:
- Weekly (Mondays 1 AM UTC)
- Monthly (1st of month 2 AM UTC)

**Function**:
- Analyzes pricing performance over period
- Calculates revenue uplift from dynamic pricing
- Tracks model accuracy and confidence
- Summarizes AI vs manual pricing

**Queue**: `reports` (priority: 5)

**Time Limit**: 15 minutes

**Parameters**:
- `period_days`: Analysis period in days (default: 30)

**Output**:
```json
{
  "period": "2025-02-20 to 2025-03-21",
  "period_days": 30,
  "total_pricing_records": 1500,
  "ai_driven_count": 1450,
  "ai_driven_percent": 96.67,
  "revenue_uplift_percent": 12.45,
  "average_confidence": 0.8734,
  "generated_at": "2025-03-22T02:00:00"
}
```

**Example**:
```python
from bookings.tasks import generate_pricing_report

# Generate 30-day report
result = generate_pricing_report.delay(period_days=30)

# Generate 7-day report
result = generate_pricing_report.delay(period_days=7)
```

### 4. Cleanup Old Predictions

**Task**: `bookings.tasks.cleanup_old_predictions`

**Schedule**: Daily at 1:30 AM UTC

**Function**:
- Deletes PricingHistory records older than retention period
- Frees database space
- Maintains database performance

**Queue**: `cleanup` (priority: 1)

**Time Limit**: 10 minutes

**Parameters**:
- `days`: Keep predictions more recent than this (default: 90)

**Recommendation**: Keep last 90 days of data for analysis

## Running Celery

### Development Mode (Synchronous)

For development, tasks execute synchronously (no background queue):

```bash
# Set in .env or environment
CELERY_TASK_ALWAYS_EAGER=True

# Run Django dev server normally
python manage.py runserver
```

All tasks will execute immediately when called.

### Production Mode (Async with Queues)

For production deployment:

**Step 1: Start Redis Broker**
```bash
Redis should be running and accessible at CELERY_BROKER_URL
```

**Step 2: Start Celery Worker(s)**

Option A: Single worker with all queues
```bash
celery -A HMS worker -l info
```

Option B: Multiple workers, one per queue (recommended for production)
```bash
# Terminal 1: Pricing tasks (high priority)
celery -A HMS worker -l info -Q pricing,notifications,default --concurrency=4

# Terminal 2: Report generation
celery -A HMS worker -l info -Q reports --concurrency=2

# Terminal 3: Cleanup tasks (low priority)
celery -A HMS worker -l info -Q cleanup --concurrency=1

# Terminal 4: ML training tasks
celery -A HMS worker -l info -Q training --concurrency=1
```

Option C: With prefork pool and max concurrency
```bash
celery -A HMS worker \
  -l info \
  --pool=prefork \
  --concurrency=4 \
  -Q pricing,notifications,reports,cleanup,default
```

**Step 3: Start Celery Beat (Scheduler)**

In a separate terminal:
```bash
celery -A HMS beat -l info
```

Or with persistence to avoid duplicate tasks:
```bash
celery -A HMS beat -l info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Complete Production Setup (Docker)

```dockerfile
# Celery Worker Service
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["celery", "-A", "HMS", "worker", "-l", "info", "-Q", "pricing,notifications,default"]

# Or for beat scheduler:
CMD ["celery", "-A", "HMS", "beat", "-l", "info", "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"]
```

Or with docker-compose:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  celery-worker:
    build: .
    command: celery -A HMS worker -l info -Q pricing,notifications,default
    depends_on:
      - redis
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
      CELERY_TASK_ALWAYS_EAGER: 'False'
  
  celery-beat:
    build: .
    command: celery -A HMS beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on:
      - redis
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
      CELERY_TASK_ALWAYS_EAGER: 'False'
```

## Monitoring Tasks

### Check Task Status

```python
from celery.result import AsyncResult

# From task ID
task_id = 'abc123def456'
result = AsyncResult(task_id)

print(f"Status: {result.status}")        # PENDING, STARTED, SUCCESS, FAILURE
print(f"Result: {result.result}")        # Task output
print(f"Type: {result.result_type}")     # Type of result
```

### View Task Logs

```bash
# Tail celery worker logs
tail -f /var/log/celery/worker.log

# In Docker
docker logs -f celery-worker

# With live tail
celery -A HMS events
```

### Flower - Task Monitoring Dashboard

Flower provides a web UI for monitoring Celery tasks:

```bash
# Install
pip install flower

# Start Flower
celery -A HMS flower

# Access at http://localhost:5555
```

Flower shows:
- Active tasks
- Task history
- Worker status
- Queue depth
- Task details and metrics

## Testing Tasks

### Manual Task Execution

```python
# In Django shell
python manage.py shell

from bookings.tasks import auto_price_all_rooms, generate_pricing_report
from datetime import datetime

# Test auto-pricing
result = auto_price_all_rooms()
print(result)

# Test with future date
result = auto_price_all_rooms(date_str='2025-12-25')

# Generate report
report = generate_pricing_report(period_days=7)
print(report)
```

### Testing with Pytest

```python
# tests/test_pricing_tasks.py
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from bookings.tasks import auto_price_all_rooms, generate_pricing_report
from room.models import Room
from bookings.models import PricingHistory

@pytest.mark.django_db
def test_auto_price_all_rooms():
    # Create test room
    room = Room.objects.create(name='Test Room', price=100)
    
    # Run task
    result = auto_price_all_rooms()
    
    # Verify
    assert result['total_rooms'] >= 1
    assert result['predictions_made'] >= 0
    
    # Check PricingHistory was created
    history = PricingHistory.objects.filter(room=room, date=datetime.now().date())
    assert history.exists()

@pytest.mark.django_db
@freeze_time("2025-02-20")
def test_generate_pricing_report():
    # Create pricing data
    room = Room.objects.create(name='Test', price=100)
    
    for i in range(10):
        date = datetime.now().date() - timedelta(days=i)
        PricingHistory.objects.create(
            room=room,
            date=date,
            base_price=100,
            dynamic_price=105,
            confidence_score=0.85
        )
    
    # Generate report
    report = generate_pricing_report(period_days=7)
    
    assert 'period' in report
    assert report['total_pricing_records'] > 0
    assert 'revenue_uplift_percent' in report
```

## Task Configuration Details

### Queue Configuration

```python
# HMS/settings.py
CELERY_QUEUES = [
    {
        'name': 'pricing',
        'priority': 10,        # Highest priority
        'routing_key': 'pricing.#'
    },
    {
        'name': 'notifications',
        'priority': 8,         # High priority
        'routing_key': 'notifications.#'
    },
    {
        'name': 'reports',
        'priority': 5,         # Normal priority
        'routing_key': 'reports.#'
    },
    {
        'name': 'cleanup',
        'priority': 1,         # Low priority
        'routing_key': 'cleanup.#'
    },
    {
        'name': 'training',
        'priority': 8,         # High priority
        'routing_key': 'training.#'
    },
]
```

### Task Routing

```python
CELERY_TASK_ROUTES = {
    'bookings.tasks.auto_price_all_rooms': {'queue': 'pricing'},
    'bookings.tasks.alert_low_confidence': {'queue': 'notifications'},
    'bookings.tasks.generate_pricing_report': {'queue': 'reports'},
    'bookings.tasks.cleanup_old_predictions': {'queue': 'cleanup'},
}
```

## Error Handling & Retries

### Auto-Retry Configuration

The `auto_price_all_rooms` task is configured with automatic retries:

```python
@shared_task(bind=True, max_retries=3)
def auto_price_all_rooms(self, date_str=None):
    try:
        # ... task logic ...
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

**Retry Strategy**:
- Attempt 1: Fails, retry in 60 seconds
- Attempt 2: Fails, retry in 120 seconds  
- Attempt 3: Fails, retry in 240 seconds
- Final failure: Task marked as failed

### Task Failure Handling

Failed tasks are stored in the result backend and can be retrieved:

```python
from celery.result import AsyncResult

task_id = 'abc123'
result = AsyncResult(task_id)

if result.status == 'FAILURE':
    print(f"Task failed: {result.info}")  # Exception info
    
# Get traceback
print(result.traceback)  # Full traceback
```

## Production Checklist

- [ ] Redis installed and running
- [ ] Celery and dependencies installed
- [ ] Environment variables configured
- [ ] Celery worker process running
- [ ] Celery beat scheduler running
- [ ] Task logs being written to files
- [ ] Flower monitoring installed and running
- [ ] Database scheduler (django_celery_beat) initialized
- [ ] Task retry policies configured
- [ ] Error alerts/notifications enabled
- [ ] Backup strategy for task failures

## Troubleshooting

### Tasks Not Running

1. **Check Redis connection**:
   ```bash
   redis-cli ping
   ```

2. **Check Celery worker**:
   ```bash
   celery -A HMS inspect active
   celery -A HMS inspect stats
   ```

3. **Check scheduled tasks**:
   ```bash
   celery -A HMS inspect scheduled
   ```

4. **Check beat scheduler**:
   ```bash
   logs should show "Scheduler: Sending due task..."
   ```

### Tasks Running Slowly

1. Check worker concurrency: `celery -A HMS inspect active`
2. Monitor queue depth: `celery -A HMS events`
3. Check CPU/memory on worker: `top`, `htop`
4. Increase worker concurrency: `--concurrency=8`

### Tasks Always Failing

1. Check task logs in Flower or worker output
2. Run task manually in Django shell to see error
3. Check database connection from worker
4. Verify all imports in tasks.py are available

### Scheduled Tasks Not Running

1. **Verify beat is running**: Check for "Scheduler:" messages in logs
2. **Check schedule in database**:
   ```python
   from django_celery_beat.models import PeriodicTask
   PeriodicTask.objects.all()
   ```
3. **Reset beat schedule**:
   ```bash
   celery -A HMS beat purge
   python manage.py migrate django_celery_beat
   ```

## Next Steps

1. ✅ Celery automation configured
2. ⏭ Admin pricing configuration interface - Coming next
3. ⏭ Notification system integration
4. ⏭ Performance optimization & caching

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Django Celery Beat](https://github.com/celery/django-celery-beat)
- [Flower Monitoring](https://flower.readthedocs.io/)
