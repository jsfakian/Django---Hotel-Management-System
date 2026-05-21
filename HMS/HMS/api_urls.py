"""
API URL Configuration for NEPHELE HMS

Per Task 4: API Design Specifications
API versioning: /api/v1/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from HMS.auth_api import RegisterAPIView, LogoutAPIView, ForgotPasswordAPIView, HMSTokenObtainPairView
from HMS.dashboard_api import dashboard_stats, trends
from HMS.api_viewsets import (
    UserViewSet,
    GuestViewSet,
    EmployeeViewSet,
    PropertyViewSet,
    TravelAgencyViewSet,
    RoomViewSet,
    BookingViewSet,
    ContractViewSet,
    PaymentViewSet,
    InvoiceViewSet,
    RefundRequestViewSet,
    NotificationViewSet,
)
from channels.views import ChannelViewSet
from inventory.views import RoomAvailabilityViewSet
from accounts.views import (
    request_data_export,
    get_data_export,
    check_export_status,
    request_data_deletion,
)

# Create router for ViewSets
router = DefaultRouter()

router.register(r'users', UserViewSet, basename='users')
router.register(r'guests', GuestViewSet, basename='guests')
router.register(r'employees', EmployeeViewSet, basename='employees')
router.register(r'properties', PropertyViewSet, basename='properties')
router.register(r'travel-agencies', TravelAgencyViewSet, basename='travel-agencies')
router.register(r'rooms', RoomViewSet, basename='rooms')
router.register(r'bookings', BookingViewSet, basename='bookings')
router.register(r'contracts', ContractViewSet, basename='contracts')
router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'invoices', InvoiceViewSet, basename='invoices')
router.register(r'refund-requests', RefundRequestViewSet, basename='refund-requests')
router.register(r'notifications', NotificationViewSet, basename='notifications')
# Channel integration (OTA platforms)
router.register(r'channels', ChannelViewSet, basename='channels')

app_name = 'api'

urlpatterns = [
    # Authentication endpoints (JWT)
    path('auth/login/', HMSTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/logout/', LogoutAPIView.as_view(), name='auth_logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterAPIView.as_view(), name='auth_register'),
    path('auth/forgot-password/', ForgotPasswordAPIView.as_view(), name='auth_forgot_password'),
    
    # GDPR Data Subject Access & Privacy Endpoints (Articles 15, 17, 20)
    path('gdpr/request-export/', request_data_export, name='gdpr_request_export'),
    path('gdpr/download-export/', get_data_export, name='gdpr_download_export'),
    path('gdpr/export-status/<str:task_id>/', check_export_status, name='gdpr_export_status'),
    path('gdpr/request-deletion/', request_data_deletion, name='gdpr_request_deletion'),
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/swagger/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger_ui'),

    # Bookings supplemental endpoints (dynamic pricing & recommendations)
    path('bookings/', include('bookings.urls')),
    
    # Channel integration (OTA platforms)
    path('channels/', include('channels.urls')),
    
    # Inventory management (centralized availability)
    path('inventory/', include('inventory.urls')),
    
    # Routers
    path('', include(router.urls)),
    
    # Dashboard aggregates and trend series
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('trends/', trends, name='trends'),

    # App-specific API endpoints
    path('analytics/', include('analytics.urls')),
    
    # Domain-specific API endpoints already mounted through router above
]
