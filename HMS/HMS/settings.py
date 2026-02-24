"""
NEPHELE Hotel Management System - Django Settings

Configuration for Phase 2 development aligning with deliverables:
- DELIVERABLES-Task4-SystemArchitecture.md
- tasks/phase-2-development/task-5a-backend-core.md
"""

import os
import logging
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']  # Configure via environment in production


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',  # OpenAPI/Swagger documentation

    # Our apps
    'properties',
    'payments',
    'notifications',
    'hotel',
    'accounts',
    'room',
    'bookings',
    'contracts',
    'analytics',  # Business Intelligence & Analytics
    'channels',  # Channel Integration (OTA platforms)
    'inventory',  # Centralized Availability Management
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'HMS.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'HMS.wsgi.application'


# Database
# Per Task 4: Recommended to use PostgreSQL in production
# Falls back to SQLite for development

DB_ENGINE = os.environ.get('DB_ENGINE', 'django.db.backends.postgresql')

DATABASES = {
    'default': {
        'ENGINE': DB_ENGINE,
        'NAME': os.environ.get('DB_NAME', 'hms'),
        'USER': os.environ.get('DB_USER', 'hms'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'hms_password'),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        **({'CONN_MAX_AGE': 600, 'ATOMIC_REQUESTS': True}
           if 'postgresql' in DB_ENGINE
           else {}),
        **({'TEST': {'NAME': ':memory:'}}
           if 'sqlite3' in DB_ENGINE
           else {}),
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# REST Framework Configuration
# Per Task 4 API Design Specifications

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'HMS.exceptions.custom_exception_handler',
    'TEST_REQUEST_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# JWT Configuration
# Per Task 4 Security Architecture: JWT Tokens

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS Configuration
# For frontend integration

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000',
]

# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Logging Configuration
# Per Task 5a: Comprehensive logging and error handling

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'hms.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'HMS': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []


# Security Settings
# Per Task 4 Security Architecture

SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin-allow-popups'
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "'unsafe-inline'"),
    'style-src': ("'self'", "'unsafe-inline'"),
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'NEPHELE Hotel Management System API',
    'DESCRIPTION': 'RESTful API for NEPHELE HMS',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'NEPHELE Support',
        'email': 'support@nephele.io',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'True') == 'True'
CELERY_TASK_EAGER_PROPAGATES = True

CELERY_BEAT_SCHEDULE = {
    'analytics-nightly-etl': {
        'task': 'analytics.tasks.nightly_etl_pipeline',
        'schedule': timedelta(days=1),
    },
    'analytics-process-scheduled-reports': {
        'task': 'analytics.tasks.process_pending_scheduled_reports',
        'schedule': timedelta(hours=1),
    },
    'analytics-cleanup-old-reports': {
        'task': 'analytics.tasks.cleanup_old_reports',
        'schedule': timedelta(days=1),
    },
    'task3-weekly-model-training': {
        'task': 'bookings.tasks.train_task3_models',
        'schedule': timedelta(days=7),
    },
    
    # ============ PHASE 3: Automated Pricing Tasks ============
    'auto-price-all-rooms': {
        'task': 'bookings.tasks.auto_price_all_rooms',
        'schedule': timedelta(hours=24),  # Daily at same time
        'options': {'queue': 'pricing', 'priority': 10}
    },
    'generate-pricing-report-weekly': {
        'task': 'bookings.tasks.generate_pricing_report',
        'schedule': timedelta(days=7),  # Weekly
        'kwargs': {'period_days': 7},
        'options': {'queue': 'reports', 'priority': 5}
    },
    'cleanup-old-predictions': {
        'task': 'bookings.tasks.cleanup_old_predictions',
        'schedule': timedelta(hours=24),  # Daily
        'kwargs': {'days': 90},
        'options': {'queue': 'cleanup', 'priority': 1}
    },
}

# ============ MyData (AADE) Integration ============
# Greek tax authority electronic invoicing system
# See: https://www.aade.gr/mydata

MYDATA_API_BASE = os.environ.get('MYDATA_API_BASE', 'https://www1.mydata.aade.gr/api')
MYDATA_USERNAME = os.environ.get('MYDATA_USERNAME', '')  # AADE username
MYDATA_PASSWORD = os.environ.get('MYDATA_PASSWORD', '')  # AADE password
MYDATA_API_KEY = os.environ.get('MYDATA_API_KEY', '')    # AADE API key
MYDATA_TIMEOUT = int(os.environ.get('MYDATA_TIMEOUT', '30'))  # API timeout in seconds

# Hotel's tax ID (AFM - Α.Φ.Μ.) for MyData transmission
# Format: 9-digit Greek tax identification number
HOTEL_TAX_ID = os.environ.get('HOTEL_TAX_ID', '')

# MyData transmission settings
MYDATA_AUTO_TRANSMISSION = os.environ.get('MYDATA_AUTO_TRANSMISSION', 'False') == 'True'
MYDATA_SANDBOX_MODE = os.environ.get('MYDATA_SANDBOX_MODE', 'True') == 'True'  # Use sandbox for testing
MYDATA_TRANSMISSION_RETRIES = int(os.environ.get('MYDATA_TRANSMISSION_RETRIES', '3'))
