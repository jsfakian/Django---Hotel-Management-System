from rest_framework.decorators import api_view
from rest_framework.response import Response

from room.models import Room
from bookings.models import PricingHistory


@api_view(["GET"])
def get_dynamic_price(request, room_id):
    """Return latest dynamic pricing insight for a room."""
    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        return Response({"error": "Room not found"}, status=404)

    latest_price = (
        PricingHistory.objects
        .filter(room=room)
        .order_by('-date')
        .first()
    )

    if not latest_price:
        return Response({
            "room_number": room.room_number,
            "base_price": room.base_price,
            "dynamic_price": room.current_price,
            "message": "No historical pricing record found; returning current room price."
        })

    return Response({
        "room_id": room.id,
        "room_number": room.room_number,
        "date": latest_price.date,
        "base_price": latest_price.base_price,
        "dynamic_price": latest_price.dynamic_price,
        "competitor_price": latest_price.competitor_price,
        "occupancy_rate": latest_price.occupancy_rate,
        "demand_score": latest_price.demand_score,
        "model_version": latest_price.model_version,
        "confidence_score": latest_price.confidence_score,
    })
