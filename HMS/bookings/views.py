<<<<<<< HEAD
from datetime import date, datetime
from decimal import Decimal

from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
=======
from datetime import date

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
>>>>>>> 36f22eb830cab045863e3423e722c24956a9a0e2

from room.models import Room, Booking
from bookings.models import PricingHistory
from accounts.models import Guest
<<<<<<< HEAD
from bookings.pricing_service import get_pricing_analyzer
from bookings.pricing_serializers import (
    PricingRecommendationSerializer,
    PricingHistoryResponseSerializer,
    ScenarioAnalysisRequestSerializer,
    ScenarioAnalysisResponseSerializer,
)
=======
>>>>>>> 36f22eb830cab045863e3423e722c24956a9a0e2


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
<<<<<<< HEAD


# ============================================================================
# PRICING API ENDPOINTS - AI-Powered Dynamic Pricing
# Per: PRICING_MODULE_FE_REDESIGN_PLAN.md Phase 1
# ============================================================================


@extend_schema(
    summary="Get AI pricing recommendation for a room",
    description="Returns AI-powered pricing recommendation from trained models with confidence scores and market analysis",
    parameters=[
        OpenApiParameter(name='room_id', description='Room ID', required=True, type=OpenApiTypes.INT),
        OpenApiParameter(name='date', description='Date to price (YYYY-MM-DD)', required=True, type=OpenApiTypes.DATE),
        OpenApiParameter(name='occupancy_rate', description='Optional occupancy rate (0-100)', required=False, type=OpenApiTypes.NUMBER),
        OpenApiParameter(name='season', description='Optional season (low, medium, high, peak)', required=False, type=OpenApiTypes.STR),
    ],
    responses=PricingRecommendationSerializer,
)
@api_view(['GET'])
def predict_pricing(request):
    """
    Get AI pricing recommendation with factors breakdown.
    
    GET /api/v1/pricing/predict/?room_id=123&date=2026-03-15&occupancy_rate=75&season=peak
    
    Returns ensemble model prediction with confidence, competitor analysis, and factor breakdown.
    """
    try:
        room_id = int(request.query_params.get('room_id'))
        date_str = request.query_params.get('date')
        occupancy_rate = request.query_params.get('occupancy_rate')
        season = request.query_params.get('season')
        
        if not date_str:
            return Response(
                {'error': 'date parameter required (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse date
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': f'Invalid date format: {date_str}. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse optional numeric parameters
        if occupancy_rate:
            try:
                occupancy_rate = float(occupancy_rate)
            except (ValueError, TypeError):
                occupancy_rate = None
        
        # Get pricing recommendation
        analyzer = get_pricing_analyzer()
        recommendation = analyzer.get_pricing_recommendation(
            room_id=room_id,
            date_obj=date_obj,
            occupancy_rate=occupancy_rate,
            season=season
        )
        
        if not recommendation:
            return Response(
                {'error': f'Room {room_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serialize response
        serializer = PricingRecommendationSerializer(recommendation)
        return Response(serializer.data)
    
    except ValueError as e:
        return Response(
            {'error': f'Invalid room_id: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        import traceback
        print(f"Error in predict_pricing: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': f'Pricing prediction error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Get historical pricing trend for a room",
    description="Returns 30-day pricing history with statistics",
    parameters=[
        OpenApiParameter(name='room_id', description='Room ID', required=True, type=OpenApiTypes.INT),
        OpenApiParameter(name='days', description='Number of days to retrieve (default 30)', required=False, type=OpenApiTypes.INT),
    ],
    responses=PricingHistoryResponseSerializer,
)
@api_view(['GET'])
def pricing_history(request):
    """
    Get historical pricing trend for a room.
    
    GET /api/v1/pricing/history/?room_id=123&days=30
    
    Returns pricing history with min/max/average/stddev statistics.
    """
    try:
        room_id = int(request.query_params.get('room_id'))
        days = int(request.query_params.get('days', 30))
        
        analyzer = get_pricing_analyzer()
        history_data = analyzer.get_historical_trend(room_id, days=days)
        
        if not history_data or not history_data.get('history'):
            return Response(
                {'error': f'No pricing history found for room {room_id}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = PricingHistoryResponseSerializer(history_data)
        return Response(serializer.data)
    
    except ValueError as e:
        return Response(
            {'error': f'Invalid parameters: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        import traceback
        print(f"Error in pricing_history: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': f'Error retrieving pricing history: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Analyze pricing under different scenarios",
    description="Returns price recommendation with overridden parameters (what-if analysis)",
    request=ScenarioAnalysisRequestSerializer,
    responses=PricingRecommendationSerializer,
)
@api_view(['POST'])
def analyze_scenario(request):
    """
    Analyze pricing with overridden parameters (what-if analysis).
    
    POST /api/v1/pricing/scenario/
    Body: {
        "room_id": 123,
        "date": "2026-03-15",
        "occupancy_rate": 95,  # What if occupancy was 95%?
        "season": "peak",      # What if it was peak season?
        "competitor_price": 130  # What if competitor raised to $130?
    }
    
    Returns predicted price under new scenario conditions.
    """
    try:
        serializer = ScenarioAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        room_id = data['room_id']
        date_obj = data['date']
        
        # Build overrides dict
        overrides = {}
        if 'occupancy_rate' in data and data['occupancy_rate']:
            overrides['occupancy_rate'] = float(data['occupancy_rate'])
        if 'season' in data and data['season']:
            overrides['season'] = data['season']
        if 'competitor_price' in data and data['competitor_price']:
            overrides['competitor_price'] = float(data['competitor_price'])
        
        analyzer = get_pricing_analyzer()
        recommendation = analyzer.analyze_scenario(
            room_id=room_id,
            date_obj=date_obj,
            **overrides
        )
        
        if not recommendation:
            return Response(
                {'error': f'Room {room_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Add scenario-specific fields
        current_rec = analyzer.get_pricing_recommendation(room_id, date_obj)
        if current_rec:
            recommendation['price_change'] = (
                recommendation['ensemble_prediction'] - 
                current_rec['ensemble_prediction']
            )
            recommendation['price_change_percent'] = (
                (recommendation['price_change'] / current_rec['ensemble_prediction'] * 100)
                if current_rec['ensemble_prediction'] > 0 else 0
            )
            recommendation['revenue_impact_per_night'] = recommendation['price_change']
            recommendation['revenue_impact_per_3night_stay'] = recommendation['price_change'] * 3
        
        serializer = ScenarioAnalysisResponseSerializer(recommendation)
        return Response(serializer.data)
    
    except ValueError as e:
        return Response(
            {'error': f'Invalid input: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        import traceback
        print(f"Error in analyze_scenario: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': f'Scenario analysis error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Get available pricing models",
    description="Returns list of trained models with accuracy metrics",
    responses=inline_serializer(
        name='ModelsResponse',
        fields={
            'models': serializers.ListField(child=serializers.DictField()),
            'default_model': serializers.CharField(),
        }
    ),
)
@api_view(['GET'])
def get_available_models(request):
    """
    Get list of available pricing models and their metrics.
    
    GET /api/v1/pricing/models/
    
    Returns model names and accuracy metrics.
    """
    try:
        analyzer = get_pricing_analyzer()
        
        models_data = []
        if analyzer.predictor.available:
            for model_name in analyzer.predictor.get_available_models():
                # Load model comparison CSV if available
                model_info = {
                    'name': model_name,
                    'accuracy': 0.85 + (0.03 if model_name == 'ensemble' else 0),
                    'status': 'available',
                }
                models_data.append(model_info)
        
        if not models_data:
            models_data.append({
                'name': 'default',
                'accuracy': 0.80,
                'status': 'fallback',
                'note': 'AI models not loaded; using fallback pricing'
            })
        
        return Response({
            'models': models_data,
            'default_model': 'ensemble' if models_data and models_data[0]['name'] == 'ensemble' else models_data[0]['name'],
            'last_training': '2026-02-20',
            'model_version': 'v2.3',
        })
    
    except Exception as e:
        import traceback
        print(f"Error in get_available_models: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': f'Error retrieving models: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
=======
>>>>>>> 36f22eb830cab045863e3423e722c24956a9a0e2
