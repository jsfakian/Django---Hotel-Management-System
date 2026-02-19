from django.urls import path

from bookings.views import get_dynamic_price, get_room_recommendations


urlpatterns = [
    path('dynamic-price/<int:room_id>/', get_dynamic_price, name='dynamic-price'),
    path('recommendations/<int:guest_id>/', get_room_recommendations, name='room-recommendations'),
]
