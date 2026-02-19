from datetime import date

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view

from room.models import Room
from bookings.models import PricingHistory
from accounts.models import Guest


def _parse_iso_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _normalize_amenities(raw_amenities):
    if isinstance(raw_amenities, list):
        return [str(item).strip().lower() for item in raw_amenities if str(item).strip()]
    if isinstance(raw_amenities, str):
        return [item.strip().lower() for item in raw_amenities.split('|') if item.strip()]
    return []


@extend_schema(
    responses=inline_serializer(
        name='DynamicPriceResponse',
        fields={
            'room_id': serializers.IntegerField(required=False),
            'room_number': serializers.CharField(),
            'date': serializers.DateField(required=False),
            'base_price': serializers.DecimalField(max_digits=10, decimal_places=2),
            'dynamic_price': serializers.DecimalField(max_digits=10, decimal_places=2),
            'competitor_price': serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True),
            'occupancy_rate': serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True),
            'demand_score': serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True),
            'model_version': serializers.CharField(required=False, allow_blank=True),
            'confidence_score': serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True),
            'message': serializers.CharField(required=False),
        },
    )
)
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


@extend_schema(
    responses=inline_serializer(
        name='RoomRecommendationsResponse',
        fields={
            'guest_id': serializers.IntegerField(),
            'guest_email': serializers.EmailField(),
            'filters': serializers.DictField(child=serializers.CharField(allow_blank=True), allow_empty=True),
            'recommendation_count': serializers.IntegerField(),
            'recommendations': serializers.ListField(child=serializers.DictField()),
        },
    )
)
@api_view(["GET"])
def get_room_recommendations(request, guest_id):
    """Return personalized room recommendations for a guest profile."""
    try:
        guest = Guest.objects.get(id=guest_id)
    except Guest.DoesNotExist:
        return Response({"error": "Guest not found"}, status=404)

    preferences = guest.preferences or {}
    preferred_room_type = str(preferences.get('room_type', '')).strip().lower()
    preferred_floor = preferences.get('floor')
    budget_max = preferences.get('max_price')
    preferred_amenities = _normalize_amenities(preferences.get('amenities', []))

    check_in = _parse_iso_date(request.query_params.get('check_in_date'))
    check_out = _parse_iso_date(request.query_params.get('check_out_date'))
    if (check_in and not check_out) or (check_out and not check_in):
        return Response(
            {"error": "Both check_in_date and check_out_date are required when filtering by date."},
            status=400,
        )
    if check_in and check_out and check_out <= check_in:
        return Response({"error": "check_out_date must be after check_in_date."}, status=400)

    top_n = request.query_params.get('limit', 5)
    try:
        top_n = max(1, min(int(top_n), 20))
    except (TypeError, ValueError):
        top_n = 5

    candidate_rooms = Room.objects.select_related('property').filter(status='available')

    if check_in and check_out:
        overlapping_booking_rooms = (
            Room.objects.filter(
                bookings__status__in=['pending', 'confirmed', 'checked_in'],
                bookings__check_in_date__lt=check_out,
                bookings__check_out_date__gt=check_in,
            )
            .values_list('id', flat=True)
            .distinct()
        )
        candidate_rooms = candidate_rooms.exclude(id__in=overlapping_booking_rooms)

    scored = []
    for room in candidate_rooms:
        score = 0
        reasons = []

        if preferred_room_type and room.room_type.lower() == preferred_room_type:
            score += 5
            reasons.append('room_type_match')

        room_amenities = _normalize_amenities(room.amenities)
        matched_amenities = sorted(set(preferred_amenities).intersection(set(room_amenities)))
        if matched_amenities:
            score += len(matched_amenities) * 2
            reasons.append(f"amenities:{','.join(matched_amenities)}")

        if preferred_floor is not None and str(room.floor) == str(preferred_floor):
            score += 1
            reasons.append('preferred_floor')

        if budget_max is not None:
            try:
                budget_value = float(budget_max)
                room_price = float(room.current_price)
                if room_price <= budget_value:
                    score += 3
                    reasons.append('within_budget')
                else:
                    score -= 2
            except (TypeError, ValueError):
                pass

        scored.append(
            {
                'room_id': room.id,
                'room_number': room.room_number,
                'property_id': room.property_id,
                'property_name': room.property.name,
                'room_type': room.room_type,
                'floor': room.floor,
                'capacity': room.capacity,
                'current_price': room.current_price,
                'amenities': room.amenities,
                'score': score,
                'reasons': reasons,
            }
        )

    scored.sort(key=lambda row: (-row['score'], float(row['current_price'])))
    recommendations = scored[:top_n]

    return Response(
        {
            'guest_id': guest.id,
            'guest_email': guest.email,
            'filters': {
                'check_in_date': check_in,
                'check_out_date': check_out,
                'limit': top_n,
            },
            'recommendation_count': len(recommendations),
            'recommendations': recommendations,
        }
    )
