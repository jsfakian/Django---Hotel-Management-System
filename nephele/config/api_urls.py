"""
API URL Configuration for Nephele

Per Task 4: API Design Specifications
API versioning: /api/v1/
"""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import IsAdminUser
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    check_export_status,
    get_data_export,
    request_data_deletion,
    request_data_export,
)
from bookings.pricing_views import pricing_analysis_view, pricing_summary_api
from bookings.views import (
    analyze_scenario,
    get_available_models,
    get_dynamic_price,
    get_room_recommendations,
    predict_pricing,
    pricing_history,
)
from channels.views import ChannelViewSet
from inventory.catalog_views import (
    AvailabilityQuoteView,
    BookingEngineCancelView,
    BookingEngineConfirmationView,
    BookingEngineConfirmView,
    BookingEngineHoldView,
    RatePlanViewSet,
    RoomTypeViewSet,
    housekeeping_board,
    tape_chart,
)
from inventory.compliance_views import police_sheet_export
from config.api_viewsets import (
    BookingViewSet,
    ContractViewSet,
    EmployeeViewSet,
    GuestViewSet,
    InvoiceViewSet,
    NotificationViewSet,
    PaymentViewSet,
    PropertyViewSet,
    RefundRequestViewSet,
    RoomViewSet,
    TravelAgencyViewSet,
    UserViewSet,
)
from config.auth_api import (
    ForgotPasswordAPIView,
    NepheleTokenObtainPairView,
    LogoutAPIView,
    RegisterAPIView,
)
from config.dashboard_api import dashboard_stats

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
router.register(r'room-types', RoomTypeViewSet, basename='room-types')
router.register(r'rate-plans', RatePlanViewSet, basename='rate-plans')

app_name = 'api'

urlpatterns = [
    # Authentication endpoints (JWT)
    path('auth/login/', NepheleTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/logout/', LogoutAPIView.as_view(), name='auth_logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterAPIView.as_view(), name='auth_register'),
    path('auth/forgot-password/', ForgotPasswordAPIView.as_view(), name='auth_forgot_password'),

    # GDPR Data Subject Access & Privacy Endpoints (Articles 15, 17, 20)
    path('gdpr/request-export/', request_data_export, name='gdpr_request_export'),
    path('gdpr/download-export/', get_data_export, name='gdpr_download_export'),
    path('gdpr/export-status/<str:task_id>/', check_export_status, name='gdpr_export_status'),
    path('gdpr/request-deletion/', request_data_deletion, name='gdpr_request_deletion'),

    # API Documentation (admin-only in all environments)
    path(
        'schema/',
        SpectacularAPIView.as_view(permission_classes=[IsAdminUser]),
        name='schema',
    ),
    path(
        'docs/swagger/',
        SpectacularSwaggerView.as_view(
            url_name='api:schema',
            permission_classes=[IsAdminUser],
        ),
        name='swagger_ui',
    ),

    # Bookings supplemental — explicit paths (not include('bookings/')) so the
    # DefaultRouter BookingViewSet list/detail routes remain reachable.
    path(
        'bookings/dynamic-price/<int:room_id>/',
        get_dynamic_price,
        name='dynamic-price',
    ),
    path(
        'bookings/recommendations/<int:guest_id>/',
        get_room_recommendations,
        name='room-recommendations',
    ),
    path('bookings/pricing/predict/', predict_pricing, name='pricing-predict'),
    path('bookings/pricing/history/', pricing_history, name='pricing-history'),
    path('bookings/pricing/scenario/', analyze_scenario, name='pricing-scenario'),
    path('bookings/pricing/models/', get_available_models, name='pricing-models'),
    path('bookings/pricing/summary/', pricing_summary_api, name='pricing-summary-api'),
    path(
        'bookings/pricing/<int:room_id>/<str:date_str>/',
        pricing_analysis_view,
        name='pricing-analysis-dated',
    ),
    path(
        'bookings/pricing/<int:room_id>/',
        pricing_analysis_view,
        name='pricing-analysis',
    ),

    # Inventory management (centralized availability)
    path('inventory/', include('inventory.urls')),

    # Availability quote + public booking engine
    path('availability/quote/', AvailabilityQuoteView.as_view(), name='availability-quote'),
    path('booking-engine/quote/', AvailabilityQuoteView.as_view(), name='booking-engine-quote'),
    path('booking-engine/hold/', BookingEngineHoldView.as_view(), name='booking-engine-hold'),
    path('booking-engine/confirm/', BookingEngineConfirmView.as_view(), name='booking-engine-confirm'),
    path('booking-engine/cancel/', BookingEngineCancelView.as_view(), name='booking-engine-cancel'),
    path(
        'booking-engine/confirmation/<int:booking_id>/',
        BookingEngineConfirmationView.as_view(),
        name='booking-engine-confirmation',
    ),

    # Front desk ops
    path('front-desk/tape-chart/', tape_chart, name='front-desk-tape-chart'),
    path('front-desk/housekeeping/', housekeeping_board, name='front-desk-housekeeping'),

    # Greek compliance exports
    path('compliance/police-sheet/', police_sheet_export, name='compliance-police-sheet'),

    # Routers (includes /bookings/ CRUD via BookingViewSet)
    path('', include(router.urls)),

    # Dashboard aggregates
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),

    # App-specific API endpoints
    path('analytics/', include('analytics.urls')),
]
