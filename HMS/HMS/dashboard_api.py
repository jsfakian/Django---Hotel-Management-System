"""
Dashboard stats and 7-day trends API endpoints.

GET /api/v1/dashboard/stats/  — aggregated counts for the main dashboard
GET /api/v1/trends/           — 7-day daily series for bookings, payments, revenue
"""

from datetime import timedelta, date

from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _daily_counts(app_label, model_name, date_field, days=7):
    """Return a list of daily counts for the last *days* days (oldest first)."""
    from django.apps import apps
    Model = apps.get_model(app_label, model_name)
    today = date.today()
    series = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        kw = {f'{date_field}__date': day}
        series.append(Model.objects.filter(**kw).count())
    return series


def _daily_sums(app_label, model_name, date_field, value_field, days=7, **filters):
    """Return a list of daily sums for *value_field* for the last *days* days."""
    from django.apps import apps
    Model = apps.get_model(app_label, model_name)
    today = date.today()
    series = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        kw = {f'{date_field}__date': day, **filters}
        total = Model.objects.filter(**kw).aggregate(s=Sum(value_field))['s'] or 0
        series.append(float(total))
    return series


# ---------------------------------------------------------------------------
# /api/v1/dashboard/stats/
# ---------------------------------------------------------------------------

@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    description="Aggregated counts for the main HMS dashboard card tiles.",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Returns a single JSON object with total counts for all core entities:
    users, rooms, bookings, guests, properties, travel agencies, payments,
    invoices, contracts, active notifications, and completed-payment revenue.
    """
    from django.contrib.auth.models import User
    from django.apps import apps

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
        'unread_notifications': _count('notifications', 'Notification', user=request.user, status='unread'),
    }
    return Response(data)


# ---------------------------------------------------------------------------
# /api/v1/trends/
# ---------------------------------------------------------------------------

@extend_schema(
    parameters=[
        OpenApiParameter(
            'module',
            OpenApiTypes.STR,
            description='Filter to a single module: bookings | payments | forecast. Omit for all.',
            required=False,
        ),
        OpenApiParameter(
            'days',
            OpenApiTypes.INT,
            description='Number of days to include in each series (default: 7, max: 90).',
            required=False,
        ),
    ],
    responses={200: OpenApiTypes.OBJECT},
    description="7-day (or custom) daily trend series for bookings, payments, and revenue.",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trends(request):
    """
    Returns trend series (daily counts / sums) for the last N days.

    Response shape:
    {
      "days": 7,
      "bookings": { "count": [...] },
      "payments": { "volume": [...], "revenue": [...] },
      "forecast": { "occupancy": [...], "revenue": [...], "cancellation_risk": [...] }
    }
    """
    module = request.query_params.get('module', 'all')
    try:
        days = max(1, min(int(request.query_params.get('days', 7)), 90))
    except (ValueError, TypeError):
        days = 7

    result = {'days': days}

    if module in ('bookings', 'all'):
        result['bookings'] = {
            'count': _daily_counts('room', 'Booking', 'created_at', days),
        }

    if module in ('payments', 'all'):
        result['payments'] = {
            'volume': _daily_counts('payments', 'Payment', 'created_at', days),
            'revenue': _daily_sums('payments', 'Payment', 'created_at', 'amount', days, status='completed'),
        }

    if module in ('forecast', 'all'):
        # Best-effort occupancy forecast using the last N days of booking density
        bookings_series = _daily_counts('room', 'Booking', 'created_at', days)
        try:
            from django.apps import apps
            total_rooms = apps.get_model('room', 'Room').objects.count() or 1
            occupancy = [round((v / total_rooms) * 100, 1) for v in bookings_series]
        except Exception:
            occupancy = bookings_series

        revenue_series = _daily_sums('payments', 'Payment', 'created_at', 'amount', days, status='completed')
        cancellation_series = _daily_counts('room', 'Booking', 'updated_at', days)

        result['forecast'] = {
            'occupancy': occupancy,
            'revenue': revenue_series,
            'cancellation_risk': cancellation_series,
        }

    return Response(result)
