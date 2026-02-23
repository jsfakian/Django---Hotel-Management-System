"""
Analytics Web URLs Configuration

Web views (HTML pages) for analytics dashboards.
These are separate from the REST API endpoints.
"""

from django.urls import path

from .views import (
    analytics_dashboard_view,
    executive_dashboard_view,
    operational_dashboard_view,
    revenue_analytics_view,
    guest_analytics_view,
)

app_name = 'analytics'

urlpatterns = [
    # Web views (HTML pages at /analytics/)
    path('', analytics_dashboard_view, name='index'),
    path('executive/', executive_dashboard_view, name='executive-dashboard'),
    path('operational/', operational_dashboard_view, name='operational-dashboard'),
    path('revenue/', revenue_analytics_view, name='revenue-analytics'),
    path('guests/', guest_analytics_view, name='guest-analytics'),
]
