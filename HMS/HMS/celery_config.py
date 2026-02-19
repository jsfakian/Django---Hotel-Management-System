"""
Celery Configuration and Beat Schedule

This module configures:
1. Celery task routing and execution
2. Periodic task schedules (Celery Beat)
3. Task result backends and brokers
"""

from celery.schedules import crontab
from datetime import timedelta

# ============================================================================
# CELERY BEAT SCHEDULE - Periodic Tasks
# ============================================================================

CELERY_BEAT_SCHEDULE = {
    # Daily auto-pricing at midnight UTC
    'auto-price-all-rooms': {
        'task': 'bookings.tasks.auto_price_all_rooms',
        'schedule': crontab(hour=0, minute=0),  # Midnight UTC
        'options': {
            'queue': 'pricing',
            'priority': 10,
        }
    },
    
    # Generate pricing report weekly (Monday at 1 AM UTC)
    'generate-pricing-report-weekly': {
        'task': 'bookings.tasks.generate_pricing_report',
        'schedule': crontab(day_of_week=0, hour=1, minute=0),  # Monday 1 AM UTC
        'kwargs': {'period_days': 7},
        'options': {
            'queue': 'reports',
            'priority': 5,
        }
    },
    
    # Generate pricing report monthly (1st of month at 2 AM UTC)
    'generate-pricing-report-monthly': {
        'task': 'bookings.tasks.generate_pricing_report',
        'schedule': crontab(day_of_month=1, hour=2, minute=0),  # 1st at 2 AM UTC
        'kwargs': {'period_days': 30},
        'options': {
            'queue': 'reports',
            'priority': 5,
        }
    },
    
    # Clean up old predictions daily (1 AM UTC)
    'cleanup-old-predictions': {
        'task': 'bookings.tasks.cleanup_old_predictions',
        'schedule': crontab(hour=1, minute=30),  # 1:30 AM UTC
        'kwargs': {'days': 90},
        'options': {
            'queue': 'cleanup',
            'priority': 1,
        }
    },
    
    # Run Task3 model training weekly (Friday 3 AM UTC)
    'train-task3-models-weekly': {
        'task': 'bookings.tasks.train_task3_models',
        'schedule': crontab(day_of_week=4, hour=3, minute=0),  # Friday 3 AM UTC
        'options': {
            'queue': 'training',
            'priority': 8,
            'time_limit': 3600,  # 1 hour timeout
        }
    },
}

# ============================================================================
# CELERY TASK ROUTING
# ============================================================================

CELERY_TASK_ROUTES = {
    # Route pricing tasks to dedicated queue
    'bookings.tasks.auto_price_all_rooms': {
        'queue': 'pricing',
        'routing_key': 'pricing.#',
    },
    'bookings.tasks.alert_low_confidence': {
        'queue': 'notifications',
        'routing_key': 'notifications.#',
    },
    
    # Route report generation to reports queue
    'bookings.tasks.generate_pricing_report': {
        'queue': 'reports',
        'routing_key': 'reports.#',
    },
    
    # Route cleanup to separate queue
    'bookings.tasks.cleanup_old_predictions': {
        'queue': 'cleanup',
        'routing_key': 'cleanup.#',
    },
    
    # Route training tasks to training queue
    'bookings.tasks.train_task3_models': {
        'queue': 'training',
        'routing_key': 'training.#',
    },
    'bookings.tasks.train_task3_pricing_model': {
        'queue': 'training',
        'routing_key': 'training.#',
    },
    'bookings.tasks.train_task3_forecasting_model': {
        'queue': 'training',
        'routing_key': 'training.#',
    },
    'bookings.tasks.train_task3_recommendation_model': {
        'queue': 'training',
        'routing_key': 'training.#',
    },
}

# ============================================================================
# CELERY TASK TIME LIMITS
# ============================================================================

CELERY_TASK_TIME_LIMIT = {
    'default': 3600,  # 1 hour default
    'bookings.tasks.auto_price_all_rooms': 1800,  # 30 minutes
    'bookings.tasks.generate_pricing_report': 900,  # 15 minutes
    'bookings.tasks.cleanup_old_predictions': 600,  # 10 minutes
    'bookings.tasks.train_task3_models': 3600,  # 1 hour
}

CELERY_TASK_SOFT_TIME_LIMIT = {
    'default': 3000,  # 50 minutes
    'bookings.tasks.auto_price_all_rooms': 1500,  # 25 minutes
    'bookings.tasks.generate_pricing_report': 800,  # 13 minutes
}

# ============================================================================
# CELERY QUEUE CONFIGURATION
# ============================================================================

CELERY_QUEUES = [
    {
        'name': 'default',
        'exchange': 'default',
        'routing_key': 'default',
        'priority': 5,
    },
    {
        'name': 'pricing',
        'exchange': 'pricing',
        'routing_key': 'pricing.#',
        'priority': 10,  # High priority for pricing tasks
    },
    {
        'name': 'notifications',
        'exchange': 'notifications',
        'routing_key': 'notifications.#',
        'priority': 8,  # Medium-high priority
    },
    {
        'name': 'reports',
        'exchange': 'reports',
        'routing_key': 'reports.#',
        'priority': 5,  # Normal priority
    },
    {
        'name': 'cleanup',
        'exchange': 'cleanup',
        'routing_key': 'cleanup.#',
        'priority': 1,  # Low priority for maintenance tasks
    },
    {
        'name': 'training',
        'exchange': 'training',
        'routing_key': 'training.#',
        'priority': 8,  # Medium-high priority for ML training
    },
]

# ============================================================================
# CELERY WORKER SETTINGS
# ============================================================================

# Set these in Django settings.py or environment:
# CELERY_BROKER_URL = 'redis://localhost:6379/0'  # or amqp://guest:guest@localhost:5672//
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
# CELERY_ACCEPT_CONTENT = ['json', 'msgpack']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = 'UTC'

# Example worker command (from shell):
# celery -A HMS worker -l info -Q pricing,notifications,default
# celery -A HMS worker -l info -Q reports,cleanup
# celery -A HMS worker -l info -Q training
# celery -A HMS beat -l info

# Or to run single worker with all queues:
# celery -A HMS worker -l info

print("✓ Celery configuration loaded")
print(f"  - Tasks: {len(CELERY_BEAT_SCHEDULE)} scheduled")
print(f"  - Queues: {len(CELERY_QUEUES)} configured")
print(f"  - Routes: {len(CELERY_TASK_ROUTES)} task routes")
