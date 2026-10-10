"""Legacy module kept for imports/tests that reference bookings.urls.

Canonical registration of these paths is in config.api_urls (explicit prefixes)
so BookingViewSet is not shadowed by include('bookings/').
"""

from django.urls import path

from bookings.pricing_views import pricing_analysis_view, pricing_summary_api
from bookings.views import (
    analyze_scenario,
    get_available_models,
    get_dynamic_price,
    get_room_recommendations,
    predict_pricing,
    pricing_history,
)

urlpatterns = [
    path('dynamic-price/<int:room_id>/', get_dynamic_price, name='dynamic-price'),
    path(
        'recommendations/<int:guest_id>/',
        get_room_recommendations,
        name='room-recommendations',
    ),
    path('pricing/predict/', predict_pricing, name='pricing-predict'),
    path('pricing/history/', pricing_history, name='pricing-history'),
    path('pricing/scenario/', analyze_scenario, name='pricing-scenario'),
    path('pricing/models/', get_available_models, name='pricing-models'),
    path('pricing/summary/', pricing_summary_api, name='pricing-summary-api'),
    path(
        'pricing/<int:room_id>/<str:date_str>/',
        pricing_analysis_view,
        name='pricing-analysis-dated',
    ),
    path('pricing/<int:room_id>/', pricing_analysis_view, name='pricing-analysis'),
]
