"""
Test configuration for Django and pytest
"""

import os
import django
from django.conf import settings

# Configure Django settings for pytest - use test settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.test_settings')

# Setup Django
django.setup()

# pytest configuration
pytest_plugins = ['pytest_django']

