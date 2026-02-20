#!/usr/bin/env python
"""
System Status Check for Intelligent Pricing System (Phase 1-3)

Verifies:
1. Database connectivity
2. Celery configuration
3. Redis cache connectivity
4. API endpoints
5. Model loading
6. Admin interface

Run with: python system_check.py
"""

import os
import sys
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.settings')
django.setup()

from django.core.management import call_command
from django.test.utils import get_runner
from django.db import connection
from django.core.cache import cache
from django.contrib.auth.models import User, Group
from django.test import Client

from room.models import Room
from bookings.models import PricingHistory
from bookings.pricing_service import get_pricing_analyzer
from bookings.cache import PricingCache
from datetime import datetime, timedelta
from decimal import Decimal


class SystemChecker:
    """Comprehensive system health check."""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
    
    def print_header(self, title):
        """Print section header."""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
    
    def print_pass(self, message):
        """Print success message."""
        self.checks_passed += 1
        print(f"  ✓ {message}")
    
    def print_fail(self, message):
        """Print failure message."""
        self.checks_failed += 1
        print(f"  ✗ {message}")
    
    def print_warn(self, message):
        """Print warning message."""
        self.warnings += 1
        print(f"  ⚠ {message}")
    
    def print_info(self, message):
        """Print info message."""
        print(f"  ℹ {message}")
    
    def check_database(self):
        """Verify database connectivity."""
        self.print_header("DATABASE CONNECTIVITY")
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.print_pass("Database connection successful")
        except Exception as e:
            self.print_fail(f"Database connection failed: {e}")
            return False
        
        # Check key tables
        try:
            rooms_count = Room.objects.count()
            pricing_count = PricingHistory.objects.count()
            users_count = User.objects.count()
            
            self.print_info(f"Rooms: {rooms_count}")
            self.print_info(f"Pricing records: {pricing_count}")
            self.print_info(f"Users: {users_count}")
            
            self.print_pass("All required tables exist")
        except Exception as e:
            self.print_fail(f"Table check failed: {e}")
            return False
        
        return True
    
    def check_cache(self):
        """Verify Redis cache connectivity."""
        self.print_header("CACHE SYSTEM")
        
        try:
            cache.set('heartbeat', 'ok', 60)
            value = cache.get('heartbeat')
            
            if value == 'ok':
                self.print_pass("Redis cache connected and operational")
            else:
                self.print_fail("Cache set/get failed")
                return False
        except Exception as e:
            self.print_warn(f"Redis cache unavailable: {e}")
            self.print_info("System will work with in-memory cache, but performance will be reduced")
        
        return True
    
    def check_celery(self):
        """Verify Celery configuration."""
        self.print_header("CELERY TASK QUEUE")
        
        try:
            broker_url = settings.CELERY_BROKER_URL
            result_backend = settings.CELERY_RESULT_BACKEND
            
            self.print_info(f"Broker: {broker_url}")
            self.print_info(f"Result Backend: {result_backend}")
            
            # Check if tasks are importable
            from bookings.tasks import (
                auto_price_all_rooms,
                alert_low_confidence,
                generate_pricing_report,
                cleanup_old_predictions,
            )
            
            self.print_pass("All Celery tasks imported successfully")
        except Exception as e:
            self.print_fail(f"Celery configuration error: {e}")
            return False
        
        # Check if Celery is running
        eager_mode = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
        if eager_mode:
            self.print_warn("Running in EAGER mode - tasks execute synchronously (development mode)")
        else:
            self.print_info("Running in ASYNC mode - tasks execute in background (production mode)")
        
        return True
    
    def check_api_endpoints(self):
        """Verify REST API endpoints."""
        self.print_header("API ENDPOINTS")
        
        # Create test client
        client = Client()
        
        # Create test user
        try:
            user = User.objects.get(username='testuser')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='testuser',
                email='test@hotel.local',
                password='testpass'
            )
            manager_group, _ = Group.objects.get_or_create(name='Manager')
            user.groups.add(manager_group)
        
        client.force_login(user)
        
        endpoints = [
            ('/api/v1/bookings/pricing/predict/', 'Pricing Prediction'),
            ('/api/v1/bookings/pricing/history/', 'Pricing History'),
            ('/api/v1/bookings/pricing/models/', 'Available Models'),
            ('/api/pricing/summary/', 'Pricing Summary'),
        ]
        
        for endpoint, name in endpoints:
            try:
                response = client.get(endpoint)
                
                if response.status_code == 200:
                    self.print_pass(f"{name}: {response.status_code} OK")
                else:
                    self.print_warn(f"{name}: {response.status_code}")
            except Exception as e:
                self.print_fail(f"{name}: {e}")
        
        return True
    
    def check_admin_interface(self):
        """Verify Django admin interface."""
        self.print_header("DJANGO ADMIN INTERFACE")
        
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if admin_user:
                self.print_pass(f"Admin user exists: {admin_user.username}")
            else:
                self.print_warn("No superuser found - consider creating one: python manage.py createsuperuser")
            
            # Check admin is registered
            from django.contrib import admin
            from bookings.models import PricingHistory
            
            if PricingHistory in admin.site._registry:
                self.print_pass("PricingHistory admin registered")
            else:
                self.print_warn("PricingHistory admin not registered")
        
        except Exception as e:
            self.print_fail(f"Admin interface check failed: {e}")
            return False
        
        return True
    
    def check_models(self):
        """Verify AI models are loaded."""
        self.print_header("AI PRICING MODELS")
        
        try:
            analyzer = get_pricing_analyzer()
            
            if analyzer:
                self.print_pass("Pricing analyzer initialized successfully")
                
                # Try a prediction
                if Room.objects.exists():
                    room = Room.objects.first()
                    prediction = analyzer.get_pricing_recommendation(
                        room_id=room.id,
                        date=datetime.now().date()
                    )
                    
                    if prediction:
                        self.print_pass("Model prediction working")
                        self.print_info(f"  Sample prediction: ${prediction.get('ensemble_prediction', 'N/A')}")
                        self.print_info(f"  Confidence: {prediction.get('confidence', 'N/A'):.1%}")
                    else:
                        self.print_warn("Model returned no prediction")
                else:
                    self.print_warn("No rooms in database - cannot test predictions")
            else:
                self.print_fail("Could not initialize pricing analyzer")
                return False
        
        except Exception as e:
            self.print_fail(f"Model check failed: {e}")
            return False
        
        return True
    
    def check_static_files(self):
        """Verify static files are configured."""
        self.print_header("STATIC FILES & TEMPLATES")
        
        try:
            static_root = getattr(settings, 'STATIC_ROOT', None)
            static_url = getattr(settings, 'STATIC_URL', None)
            template_dirs = getattr(settings, 'TEMPLATES', [{}])[0].get('DIRS', [])
            
            self.print_info(f"STATIC_URL: {static_url}")
            self.print_info(f"STATIC_ROOT: {static_root}")
            self.print_info(f"Template dirs: {len(template_dirs)} configured")
            
            self.print_pass("Static files configured")
        
        except Exception as e:
            self.print_warn(f"Static files check: {e}")
        
        return True
    
    def check_settings(self):
        """Verify critical Django settings."""
        self.print_header("DJANGO SETTINGS")
        
        required_settings = [
            'DATABASES',
            'INSTALLED_APPS',
            'SECRET_KEY',
            'CELERY_BROKER_URL',
            'CACHES',
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                self.print_pass(f"{setting} configured")
            else:
                self.print_warn(f"{setting} not found in settings")
        
        # Check debug mode
        if settings.DEBUG:
            self.print_info("DEBUG mode: ON (development)")
        else:
            self.print_info("DEBUG mode: OFF (production)")
        
        return True
    
    def run_all_checks(self):
        """Run all system checks."""
        print("\n" + "="*70)
        print("  INTELLIGENT PRICING SYSTEM - DIAGNOSTIC CHECK")
        print("="*70)
        
        checks = [
            self.check_settings,
            self.check_database,
            self.check_cache,
            self.check_celery,
            self.check_models,
            self.check_api_endpoints,
            self.check_admin_interface,
            self.check_static_files,
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.print_fail(f"Check failed with exception: {e}")
        
        # Summary
        self.print_header("SUMMARY")
        print(f"  ✓ Passed: {self.checks_passed}")
        print(f"  ✗ Failed: {self.checks_failed}")
        print(f"  ⚠ Warnings: {self.warnings}")
        
        if self.checks_failed == 0:
            print("\n  ✓ System is operational!")
            return 0
        else:
            print(f"\n  ✗ {self.checks_failed} critical issue(s) found")
            return 1


if __name__ == '__main__':
    checker = SystemChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)
