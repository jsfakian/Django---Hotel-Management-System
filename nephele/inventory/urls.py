"""
URL configuration for Inventory app
"""

from django.urls import path
from .views import RoomAvailabilityViewSet

app_name = 'inventory'
urlpatterns = [
    path('availability/<int:property_id>/', RoomAvailabilityViewSet.as_view({'get': 'get_property_availability'}), name='property-availability'),
    path('rooms/<int:room_id>/availability/', RoomAvailabilityViewSet.as_view({'put': 'update_room_availability'}), name='room-availability-update'),
    path('overbook/', RoomAvailabilityViewSet.as_view({'post': 'overbook'}), name='overbook'),
    path('sync-log/<int:property_id>/', RoomAvailabilityViewSet.as_view({'get': 'sync_log'}), name='sync-log'),
]
