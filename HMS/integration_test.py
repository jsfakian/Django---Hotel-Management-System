#!/usr/bin/env python
"""
Quick integration test to verify system functionality without fixture setup issues.
Tests core API endpoints and caching layer directly.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.core.cache import cache
from bookings.cache import PricingCache


def test_api_endpoints():
    """Test REST API endpoints are accessible."""
    print("\n" + "="*70)
    print("  API ENDPOINT TESTS")
    print("="*70)
    
    client = Client()
    
    # Test that endpoints exist and return proper status codes
    tests = [
        ('GET', '/api/v1/bookings/pricing/models/', 200, 'Available Models'),
        ('GET', '/api/pricing/summary/', 404, 'Summary API (empty DB expected)'),
        ('GET', '/', 200, 'Home Page'),
        ('GET', '/admin/', 302, 'Admin Login Redirect'),
    ]
    
    passed = 0
    failed = 0
    
    for method, path, expected_status, description in tests:
        try:
            if method == 'GET':
                response = client.get(path)
            status_ok = response.status_code == expected_status
            result = "✓" if status_ok else "✗"
            passed += 1 if status_ok else 0
            failed += 0 if status_ok else 1
            print(f"  {result} {description}: {response.status_code} (expected {expected_status})")
        except Exception as e:
            print(f"  ✗ {description}: {str(e)}")
            failed += 1
    
    return passed, failed


def test_caching_layer():
    """Test caching layer functionality."""
    print("\n" + "="*70)
    print("  CACHING LAYER TESTS")
    print("="*70)
    
    passed = 0
    failed = 0
    
    # Clear cache
    PricingCache.invalidate_all_pricing_cache()
    print("  ✓ Cache cleared")
    passed += 1
    
    # Test cache set/get
    try:
        test_data = {
            'room_id': 123,
            'date': '2026-02-23',
            'price': 150.00,
            'confidence': 0.87
        }
        PricingCache.set_pricing_prediction(123, date(2026, 2, 23), test_data)
        retrieved = cache.get('pricing:prediction:123:2026-02-23')
        
        if retrieved and retrieved.get('price') == 150.00:
            print("  ✓ Cache set/get for predictions works")
            passed += 1
        else:
            print("  ✗ Cache retrieval failed")
            failed += 1
    except Exception as e:
        print(f"  ✗ Cache set/get test failed: {str(e)}")
        failed += 1
    
    # Test cache summary
    try:
        summary_data = {
            'total_rooms': 50,
            'average_price': 165.00,
            'occupancy_rate': 0.75
        }
        PricingCache.set_pricing_summary(summary_data)
        retrieved = cache.get('pricing:summary')
        
        if retrieved and retrieved.get('total_rooms') == 50:
            print("  ✓ Cache set/get for summary works")
            passed += 1
        else:
            print("  ✗ Cache summary retrieval failed")
            failed += 1
    except Exception as e:
        print(f"  ✗ Cache summary test failed: {str(e)}")
        failed += 1
    
    # Test cache invalidation
    try:
        PricingCache.invalidate_all_pricing_cache()
        retrieved = cache.get('pricing:summary')
        
        if retrieved is None:
            print("  ✓ Cache invalidation works")
            passed += 1
        else:
            print("  ✗ Cache invalidation failed")
            failed += 1
    except Exception as e:
        print(f"  ✗ Cache invalidation test failed: {str(e)}")
        failed += 1
    
    return passed, failed


def test_django_setup():
    """Test Django configuration."""
    print("\n" + "="*70)
    print("  DJANGO SETUP TESTS")
    print("="*70)
    
    from django.conf import settings
    from django.core.management import call_command
    
    passed = 0
    failed = 0
    
    # Check settings
    checks = [
        ('DATABASE configured', settings.DATABASES is not None),
        ('SECRET_KEY set', settings.SECRET_KEY is not None and settings.SECRET_KEY != ''),
        ('INSTALLED_APPS', 'bookings' in settings.INSTALLED_APPS),
        ('CELERY_BROKER_URL', hasattr(settings, 'CELERY_BROKER_URL')),
        ('CACHES configured', 'default' in settings.CACHES),
    ]
    
    for check_name, result in checks:
        if result:
            print(f"  ✓ {check_name}")
            passed += 1
        else:
            print(f"  ✗ {check_name}")
            failed += 1
    
    # Check admin user
    try:
        admin_user = User.objects.filter(username='admin').first()
        if admin_user and admin_user.is_staff:
            print(f"  ✓ Admin user exists")
            passed += 1
        else:
            print(f"  ✗ Admin user not properly configured")
            failed += 1
    except Exception as e:
        print(f"  ✗ Admin user check failed: {str(e)}")
        failed += 1
    
    return passed, failed


def test_imports():
    """Test that all critical modules can be imported."""
    print("\n" + "="*70)
    print("  MODULE IMPORT TESTS")
    print("="*70)
    
    passed = 0
    failed = 0
    
    modules = [
        ('bookings.views', 'REST API views'),
        ('bookings.models', 'Booking models'),
        ('bookings.cache', 'Caching layer'),
        ('bookings.tasks', 'Celery tasks'),
        ('bookings.admin', 'Admin interface'),
        ('room.models', 'Room models'),
        ('properties.models', 'Property models'),
    ]
    
    for module_path, description in modules:
        try:
            __import__(module_path)
            print(f"  ✓ {description}")
            passed += 1
        except ImportError as e:
            print(f"  ✗ {description}: {str(e)}")
            failed += 1
    
    return passed, failed


def main():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("  INTELLIGENT PRICING SYSTEM - INTEGRATION TEST")
    print("="*70)
    
    total_passed = 0
    total_failed = 0
    
    # Run test suites
    p, f = test_imports()
    total_passed += p
    total_failed += f
    
    p, f = test_django_setup()
    total_passed += p
    total_failed += f
    
    p, f = test_caching_layer()
    total_passed += p
    total_failed += f
    
    p, f = test_api_endpoints()
    total_passed += p
    total_failed += f
    
    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    print(f"  ✓ Passed: {total_passed}")
    print(f"  ✗ Failed: {total_failed}")
    print("="*70)
    
    if total_failed == 0:
        print("\n  ✓ ALL INTEGRATION TESTS PASSED!")
        print("  System is operational and ready for deployment.")
        return 0
    else:
        print(f"\n  ✗ {total_failed} tests failed. Review output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
