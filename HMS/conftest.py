"""
Test configuration for Django and pytest
"""

import os
import django
from django.conf import settings

# Configure Django settings for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.settings')
django.setup()

# pytest configuration
pytest_plugins = ['pytest_django']

def pytest_configure(config):
    """Configure pytest for Django testing"""
    # Set up test database configuration
    if not hasattr(settings, 'DATABASES'):
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'test_hms',
                'USER': 'hms',
                'PASSWORD': 'hms_password',
                'HOST': 'postgres',
                'PORT': '5432',
            }
        }

