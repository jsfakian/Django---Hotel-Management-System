"""
API URL Configuration for NEPHELE HMS

Per Task 4: API Design Specifications
API versioning: /api/v1/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from HMS.api_viewsets import (
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

# Import API views when they're created
# from accounts.api.views import *
# from bookings.api.views import *
# from properties.api.views import *
# from payments.api.views import *

# Create router for ViewSets
router = DefaultRouter()

router.register(r'properties', PropertyViewSet, basename='properties')
router.register(r'travel-agencies', TravelAgencyViewSet, basename='travel-agencies')
router.register(r'rooms', RoomViewSet, basename='rooms')
router.register(r'bookings', BookingViewSet, basename='bookings')
router.register(r'contracts', ContractViewSet, basename='contracts')
router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'invoices', InvoiceViewSet, basename='invoices')
router.register(r'refund-requests', RefundRequestViewSet, basename='refund-requests')
router.register(r'notifications', NotificationViewSet, basename='notifications')

app_name = 'api'

urlpatterns = [
    # Authentication endpoints (JWT)
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/swagger/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger_ui'),
    
    # Routers
    path('', include(router.urls)),
    
    # App-specific API endpoints
    path('analytics/', include('analytics.urls')),
    
    # Domain-specific API endpoints already mounted through router above
]
