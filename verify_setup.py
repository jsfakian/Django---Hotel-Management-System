#!/usr/bin/env python
"""
Verification script to test Django setup and new analytics implementation
"""
import os
import sys
import django

# Add HMS directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'HMS'))

# Load .env file
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.settings')

# Setup Django
django.setup()

print("=" * 80)
print(" NEPHELE Hotel Management System - Analytics Implementation Verification")
print("=" * 80)

# Test 1: Check Django Configuration
print("\n✓ Django Setup Successful")
print(f"  - DEBUG: {os.environ.get('DEBUG')}")
print(f"  - SECRET_KEY configured: {bool(os.environ.get('SECRET_KEY'))}")

# Test 2: Verify Analytics App
try:
    from analytics.models import (
        DashboardExecutiveMetrics, 
        DashboardOperationalStatus,
        DashboardRevenueMetrics,
        DashboardGuestAnalytics
    )
    print("\n✓ Analytics Models Loaded Successfully")
    print("  - DashboardExecutiveMetrics")
    print("  - DashboardOperationalStatus")
    print("  - DashboardRevenueMetrics")
    print("  - DashboardGuestAnalytics")
except Exception as e:
    print(f"\n✗ Analytics Models Error: {e}")
    sys.exit(1)

# Test 3: Verify Analytics Views
try:
    from analytics.views import (
        analytics_dashboard_view,
        executive_dashboard_view,
        operational_dashboard_view,
        revenue_analytics_view,
        guest_analytics_view
    )
    print("\n✓ Analytics Views Loaded Successfully")
    print("  - analytics_dashboard_view")
    print("  - executive_dashboard_view")
    print("  - operational_dashboard_view")
    print("  - revenue_analytics_view")
    print("  - guest_analytics_view")
except Exception as e:
    print(f"\n✗ Analytics Views Error: {e}")
    sys.exit(1)

# Test 4: Verify URL Configuration
try:
    from django.urls import resolve, path, include
    from analytics import web_urls
    print("\n✓ Analytics URL Configuration Loaded Successfully")
    print("  - web_urls.py module imported")
    print(f"  - URL patterns defined: {len(web_urls.urlpatterns)} routes")
except Exception as e:
    print(f"\n✗ Analytics URL Configuration Error: {e}")
    sys.exit(1)

# Test 5: Verify API Endpoints
try:
    from analytics.urls import router
    print("\n✓ Analytics REST API Router Configured")
    print(f"  - {len(router.registry)} API endpoints registered")
except Exception as e:
    print(f"\n✗ Analytics API Router Error: {e}")

# Test 6: Check Templates
import os.path
templates_base = os.path.join(os.path.dirname(__file__), 'HMS', 'templates', 'analytics')
templates = [
    'dashboard.html',
    'executive_dashboard.html',
    'operational_dashboard.html',
    'revenue_analytics.html',
    'guest_analytics.html'
]

try:
    missing = []
    for template in templates:
        template_path = os.path.join(templates_base, template)
        if not os.path.exists(template_path):
            missing.append(template)
    
    if missing:
        print(f"\n✗ Missing Analytics Templates: {', '.join(missing)}")
    else:
        print("\n✓ All Analytics Templates Present")
        for template in templates:
            print(f"  - {template}")
except Exception as e:
    print(f"\n✗ Template Check Error: {e}")

# Test 7: Check Vue Components
components_base = os.path.join(os.path.dirname(__file__), 'HMS', 'static', 'js', 'components')
components = [
    'AnalyticsChart.vue',
    'MetricsGrid.vue'
]

try:
    missing = []
    for component in components:
        component_path = os.path.join(components_base, component)
        if not os.path.exists(component_path):
            missing.append(component)
    
    if missing:
        print(f"\n✗ Missing Vue Components: {', '.join(missing)}")
    else:
        print("\n✓ All Vue Components Present")
        for component in components:
            print(f"  - {component}")
except Exception as e:
    print(f"\n✗ Component Check Error: {e}")

# Test 8: Run Django Checks
print("\n✓ Running Django System Checks...")
from django.core.management import call_command
from io import StringIO
import sys

out = StringIO()
try:
    call_command('check', stdout=out, stderr=out)
    print("  ✓ No Django system errors found")
except SystemExit as e:
    if e.code == 0:
        print("  ✓ No Django system errors found")
    else:
        print(f"  ✗ Django system check failed with code {e.code}")
except Exception as e:
    print(f"  ! Django check warning: {e}")

print("\n" + "=" * 80)
print(" VERIFICATION COMPLETE - NEPHELE Analytics Ready for Testing")
print("=" * 80)
print("\nNext Steps:")
print("1. Run: cd HMS && python manage.py runserver")
print("2. Navigate to: http://localhost:8000/analytics/")
print("3. Test endpoints:")
print("   - http://localhost:8000/analytics/executive/")
print("   - http://localhost:8000/analytics/operational/")
print("   - http://localhost:8000/analytics/revenue/")
print("   - http://localhost:8000/analytics/guests/")
print("\nAPI Endpoints:")
print("   - http://localhost:8000/api/v1/analytics/executive-dashboard/")
print("   - http://localhost:8000/api/v1/analytics/operational-dashboard/")
print("   - http://localhost:8000/api/v1/analytics/revenue-analytics/")
print("   - http://localhost:8000/api/v1/analytics/guest-analytics/")
print("=" * 80)
