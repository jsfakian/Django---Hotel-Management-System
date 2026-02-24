"""
NEPHELE Hotel Management System - URL Configuration

Per deliverables:
- DELIVERABLES-Task4-SystemArchitecture.md
- tasks/phase-2-development/task-5a-backend-core.md

Routes:
- Legacy views: / (for backward compatibility)
- REST API v1: /api/v1/
"""

from django.contrib import admin
from django.urls import path, include
from HMS.health import healthz, health_check, health_db, health_cache
from HMS.web_views import landing_page, home_page, backend_navigation, module_portal, module_crud_page
from accounts.views import login_page, logout_user, register_page

urlpatterns = [
    path('', landing_page, name='landing'),
    path('home/', home_page, name='home'),
    path('login/', login_page, name='login'),
    path('logout/', logout_user, name='logout'),
    path('register/', register_page, name='register'),
    path('portal/<str:module_key>/<str:action>/<int:pk>/', module_crud_page, name='module-crud-detail'),
    path('portal/<str:module_key>/<str:action>/', module_crud_page, name='module-crud'),
    path('portal/<str:module_key>/', module_portal, name='module-portal'),
    path('backend-navigation/', backend_navigation, name='backend-navigation'),
    
    # Health check endpoints
    path('health/', health_check, name='health'),
    path('health/db/', health_db, name='health-db'),
    path('health/cache/', health_cache, name='health-cache'),
    path('healthz/', healthz, name='healthz'),  # Legacy endpoint
    
    # Django Admin
    path('admin/', admin.site.urls),
    
    # Analytics Dashboard Web Views
    path('analytics/', include('analytics.web_urls')),
    
    # API v1 (REST)
    path('api/v1/', include('HMS.api_urls')),
    
    # Legacy app routes kept during transition
    path('properties/', include('properties.urls')),
    path('payments/', include('payments.urls')),
    path('notifications/', include('notifications.urls')),
    path('contracts/', include('contracts.urls')),
]

# Note: Additional legacy paths removed for clarity. 
# During Phase 2, endpoints will be gradually migrated to REST API.
# For full legacy URL list, see git history or IMPLEMENTATION_SUMMARY.md

