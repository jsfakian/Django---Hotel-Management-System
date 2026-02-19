"""
Pricing Analysis Views for Phase 3 Template Integration

This provides the web interface for the intelligent pricing module,
linking the Vue.js frontend components to Django backend data.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from room.models import Room
from bookings.models import PricingHistory
from bookings.pricing_service import get_pricing_analyzer


@login_required
@require_http_methods(["GET"])
def pricing_analysis_view(request, room_id, date_str=None):
    """
    Display the intelligent pricing analysis dashboard.
    
    URL: /pricing/<room_id>/ or /pricing/<room_id>/<date>/
    Template: pricing/analysis.html
    
    Context:
        - room: Room object
        - selected_date: Selected date (defaults to today)
        - can_edit: Whether user can edit pricing
    """
    room = get_object_or_404(Room, id=room_id)
    
    # Parse date parameter
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()
    
    # Check permissions
    can_edit = request.user.is_staff or request.user.groups.filter(name='Manager').exists()
    
    context = {
        'room': room,
        'selected_date': selected_date.isoformat(),
        'can_edit': can_edit,
        'page_title': f'Pricing Analysis - {room.name}',
        'room_id': room_id,
    }
    
    return render(request, 'pricing/analysis.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pricing_summary_api(request):
    """
    Get summary statistics for all rooms' pricing.
    
    Used by admin dashboard to show pricing health.
    
    Response:
    {
        "total_rooms": 50,
        "rooms_using_ai": 45,
        "average_confidence": 0.87,
        "revenue_uplift": 12.5,
        "last_update": "2026-02-20T10:30:00Z"
    }
    """
    try:
        # Get all rooms
        rooms = Room.objects.all().count()
        
        # Get rooms with recent pricing predictions
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        rooms_with_ai = PricingHistory.objects.filter(
            date__gte=thirty_days_ago,
            model_version__isnull=False
        ).values('room').distinct().count()
        
        # Get average confidence
        avg_confidence = PricingHistory.objects.filter(
            date__gte=thirty_days_ago
        ).values_list('confidence_score', flat=True)
        
        if avg_confidence.exists():
            avg_conf = sum(avg_confidence) / len(avg_confidence)
        else:
            avg_conf = 0
        
        # Estimate revenue uplift from dynamic pricing
        pricing_history = PricingHistory.objects.filter(
            date__gte=thirty_days_ago
        ).values_list('base_price', 'dynamic_price')
        
        if pricing_history.exists():
            base_total = sum(base for base, _ in pricing_history)
            dynamic_total = sum(dynamic for _, dynamic in pricing_history)
            uplift = ((dynamic_total - base_total) / base_total * 100) if base_total > 0 else 0
        else:
            uplift = 0
        
        return Response({
            'total_rooms': rooms,
            'rooms_using_ai': rooms_with_ai,
            'average_confidence': float(avg_conf),
            'revenue_uplift_percent': round(uplift, 2),
            'last_update': datetime.now().isoformat(),
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
