from django.urls import path

from bookings.views import (
    get_dynamic_price,
    get_room_recommendations,
    predict_pricing,
    pricing_history,
    analyze_scenario,
    get_available_models,
)

from bookings.pricing_views import (
    pricing_analysis_view,
    pricing_summary_api,
)


urlpatterns = [
    # Existing endpoints
    path('dynamic-price/<int:room_id>/', get_dynamic_price, name='dynamic-price'),
    path('recommendations/<int:guest_id>/', get_room_recommendations, name='room-recommendations'),
    
    # New Pricing API endpoints (Phase 1 Implementation)
    path('pricing/predict/', predict_pricing, name='pricing-predict'),
    path('pricing/history/', pricing_history, name='pricing-history'),
    path('pricing/scenario/', analyze_scenario, name='pricing-scenario'),
    path('pricing/models/', get_available_models, name='pricing-models'),
    
    # Phase 3: Pricing Analysis Dashboard
    path('pricing/<int:room_id>/<str:date_str>/', pricing_analysis_view, name='pricing-analysis-dated'),
    path('pricing/<int:room_id>/', pricing_analysis_view, name='pricing-analysis'),
    path('api/pricing/summary/', pricing_summary_api, name='pricing-summary-api'),
]
