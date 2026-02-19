"""
Analytics URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ExecutiveDashboardViewSet,
    OperationalDashboardViewSet,
    RevenueAnalyticsViewSet,
    GuestAnalyticsViewSet,
    CustomReportViewSet,
    AnalyticsDashboardViewSet,
    ScheduledReportViewSet,
    ReportExecutionViewSet,
    # Forecasting viewsets
    OccupancyForecastViewSet,
    RevenueForecastViewSet,
    CancellationPredictionViewSet,
    NoShowPredictionViewSet,
    ForecastingModelMetricsViewSet,
)

app_name = 'analytics'

router = DefaultRouter()
router.register(r'executive-dashboard', ExecutiveDashboardViewSet, basename='executive-dashboard')
router.register(r'operational-dashboard', OperationalDashboardViewSet, basename='operational-dashboard')
router.register(r'revenue-analytics', RevenueAnalyticsViewSet, basename='revenue-analytics')
router.register(r'guest-analytics', GuestAnalyticsViewSet, basename='guest-analytics')
router.register(r'custom-reports', CustomReportViewSet, basename='custom-reports')
router.register(r'dashboard', AnalyticsDashboardViewSet, basename='dashboard')
router.register(r'scheduled-reports', ScheduledReportViewSet, basename='scheduled-reports')
router.register(r'report-executions', ReportExecutionViewSet, basename='report-executions')

# Forecasting routes
router.register(r'occupancy-forecasts', OccupancyForecastViewSet, basename='occupancy-forecasts')
router.register(r'revenue-forecasts', RevenueForecastViewSet, basename='revenue-forecasts')
router.register(r'cancellation-predictions', CancellationPredictionViewSet, basename='cancellation-predictions')
router.register(r'noshow-predictions', NoShowPredictionViewSet, basename='noshow-predictions')
router.register(r'forecast-metrics', ForecastingModelMetricsViewSet, basename='forecast-metrics')

urlpatterns = [
    path(
        'occupancy-forecasts/next-30-days/',
        OccupancyForecastViewSet.as_view({'get': 'next_30_days'}),
        name='occupancy-forecasts-next-30-days',
    ),
    path(
        'revenue-forecasts/next-30-days/',
        RevenueForecastViewSet.as_view({'get': 'next_30_days'}),
        name='revenue-forecasts-next-30-days',
    ),
    path(
        'cancellation-predictions/high-risk/',
        CancellationPredictionViewSet.as_view({'get': 'high_risk'}),
        name='cancellation-predictions-high-risk',
    ),
    path(
        'noshow-predictions/overbooking-recommendations/',
        NoShowPredictionViewSet.as_view({'get': 'overbooking_recommendations'}),
        name='noshow-overbooking-recommendations',
    ),
    path(
        'forecast-metrics/health-check/',
        ForecastingModelMetricsViewSet.as_view({'get': 'health_check'}),
        name='forecast-metrics-health-check',
    ),
    path(
        'reports/<int:pk>/resend/',
        ReportExecutionViewSet.as_view({'post': 'resend'}),
        name='report-execution-resend-alias',
    ),
    path(
        'delivery-tracking/<int:pk>/',
        ReportExecutionViewSet.as_view({'get': 'delivery_status'}),
        name='delivery-tracking-alias',
    ),
    path('', include(router.urls)),
]
