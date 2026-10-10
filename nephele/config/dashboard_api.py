"""
Dashboard stats API endpoint.

GET /api/v1/dashboard/stats/  — aggregated counts for the main dashboard
"""

from django.db.models import Sum
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.api_permissions import IsHotelStaff


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    description="Aggregated counts for the main Nephele dashboard card tiles.",
)
@api_view(['GET'])
@permission_classes([IsHotelStaff])
def dashboard_stats(request):
    """
    Returns a single JSON object with total counts for all core entities:
    users, rooms, bookings, guests, properties, travel agencies, payments,
    invoices, contracts, active notifications, and completed-payment revenue.
    """
    from django.apps import apps
    from django.contrib.auth.models import User

    def _count(app, model, **kw):
        try:
            return apps.get_model(app, model).objects.filter(**kw).count()
        except Exception:
            return 0

    def _sum(app, model, field, **kw):
        try:
            result = apps.get_model(app, model).objects.filter(**kw).aggregate(s=Sum(field))['s']
            return float(result) if result is not None else 0.0
        except Exception:
            return 0.0

    data = {
        'total_users': User.objects.count(),
        'total_staff': User.objects.filter(is_staff=True).count(),
        'total_active_users': User.objects.filter(is_active=True).count(),
        'total_rooms': _count('room', 'Room'),
        'available_rooms': _count('room', 'Room', status='available'),
        'occupied_rooms': _count('room', 'Room', status='occupied'),
        'total_bookings': _count('room', 'Booking'),
        'pending_bookings': _count('room', 'Booking', status='pending'),
        'confirmed_bookings': _count('room', 'Booking', status='confirmed'),
        'total_guests': _count('accounts', 'Guest'),
        'total_properties': _count('properties', 'Property'),
        'active_properties': _count('properties', 'Property', is_active=True),
        'total_travel_agencies': _count('properties', 'TravelAgency'),
        'active_travel_agencies': _count('properties', 'TravelAgency', status='active'),
        'total_payments': _count('payments', 'Payment'),
        'completed_payments': _count('payments', 'Payment', status='completed'),
        'total_revenue': _sum('payments', 'Payment', 'amount', status='completed'),
        'total_invoices': _count('payments', 'Invoice'),
        'paid_invoices': _count('payments', 'Invoice', status='paid'),
        'total_contracts': _count('contracts', 'Contract'),
        'active_contracts': _count('contracts', 'Contract', status='active'),
        'pending_contracts': _count('contracts', 'Contract', status='pending'),
        'unread_notifications': _count(
            'notifications', 'Notification', user=request.user, status='unread'
        ),
    }
    return Response(data)
