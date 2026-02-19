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
    path('', include(router.urls)),
]
