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
# from accounts.views import home

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API v1 (REST)
    path('api/v1/', include('HMS.api_urls')),
    
    # Legacy views (for backward compatibility during transition)
    # path('', home, name="home"),
    path('properties/', include('properties.urls')),
    path('payments/', include('payments.urls')),
    path('notifications/', include('notifications.urls')),
    path('contracts/', include('contracts.urls')),
    
    # Legacy authentication views (being replaced by JWT API)
    # path('login/', login_page, name="login"),
    # path('logout/', logout_user, name="logout"),
    # path('register/', register_page, name="register"),
]

# Note: Additional legacy paths removed for clarity. 
# During Phase 2, endpoints will be gradually migrated to REST API.
# For full legacy URL list, see git history or IMPLEMENTATION_SUMMARY.md

