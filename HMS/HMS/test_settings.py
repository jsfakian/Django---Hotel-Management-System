"""
Django test settings for running pytest
Inherits from main settings but overrides to use SQLite for testing
"""

from .settings import *  # noqa: F401, F403

# Override database to use SQLite for testing (faster and no external dependency)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Use in-memory database for fast tests
        'ATOMIC_REQUESTS': True,
    }
}

# Disable migrations for faster tests (will just create tables)
# This is safe for testing since we use in-memory database
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Speed up testing by using a fast password hasher
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable other slow settings for tests
DEBUG = True
LOGGING_CONFIG = None  # Disable logging during tests

# Use simple cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# In-memory session storage for tests
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# Simplified storage for tests
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATIC_ROOT = '/tmp/hms_test_static/'

# Disable email sending in tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Get SECRET_KEY from environment or use test key
if 'secret_key' not in (SK := os.environ.get('SECRET_KEY', 'test-secret-key-task5f')):
    SECRET_KEY = 'test-secret-key-task5f'
