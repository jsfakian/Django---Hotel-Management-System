"""
Dashboard stats API endpoint.

GET /api/v1/dashboard/stats/  — aggregated counts for ops dashboards
"""

from datetime import timedelta

from django.apps import apps
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.api_permissions import IsHotelStaff


def _count(app, model, **kw):
    try:
        return apps.get_model(app, model).objects.filter(**kw).count()
    except Exception:
        return 0


def _sum(app, model, field, **kw):
    try:
        result = (
            apps.get_model(app, model).objects.filter(**kw).aggregate(s=Sum(field))["s"]
        )
        return float(result) if result is not None else 0.0
    except Exception:
        return 0.0


def _occupancy_rate(total_rooms, occupied_rooms):
    if not total_rooms:
        return 0.0
    return round((occupied_rooms / total_rooms) * 100, 1)


def _month_bounds(today):
    start = today.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
    return start, end


def _today_booking_stats(today):
    """Cloudbeds-style front-desk day counts from Booking dates/status."""
    Booking = apps.get_model("room", "Booking")
    base = Booking.objects.exclude(status__in=["cancelled", "no_show", "held"])
    arrivals = base.filter(check_in_date=today).count()
    departures = base.filter(check_out_date=today).count()
    in_house = Booking.objects.filter(status="checked_in").count()
    return {
        "arrivals_today": arrivals,
        "departures_today": departures,
        "checkins_today": arrivals,
        "checkouts_today": departures,
        "pending_arrivals": base.filter(
            check_in_date=today, status__in=["pending", "confirmed"]
        ).count(),
        "pending_departures": base.filter(
            check_out_date=today, status="checked_in"
        ).count(),
        "in_house": in_house,
        "active_guests": in_house,
        "stayovers": base.filter(
            check_in_date__lt=today,
            check_out_date__gt=today,
            status="checked_in",
        ).count(),
    }


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    description="Aggregated counts for Nephele ops dashboard tiles (today + portfolio).",
)
@api_view(["GET"])
@permission_classes([IsHotelStaff])
def dashboard_stats(request):
    today = timezone.localdate()
    month_start, month_end = _month_bounds(today)

    total_rooms = _count("room", "Room")
    occupied_rooms = _count("room", "Room", status="occupied")
    available_rooms = _count("room", "Room", status="available")

    revenue_mtd = _sum(
        "payments",
        "Payment",
        "amount",
        status="completed",
        created_at__date__gte=month_start,
        created_at__date__lte=month_end,
    )
    if revenue_mtd == 0.0:
        revenue_mtd = _sum("payments", "Payment", "amount", status="completed")

    day = _today_booking_stats(today)

    data = {
        "as_of": today.isoformat(),
        "total_users": User.objects.count(),
        "total_staff": User.objects.filter(is_staff=True).count(),
        "total_active_users": User.objects.filter(is_active=True).count(),
        "total_rooms": total_rooms,
        "available_rooms": available_rooms,
        "occupied_rooms": occupied_rooms,
        "occupancy_rate": _occupancy_rate(total_rooms, occupied_rooms),
        "total_bookings": _count("room", "Booking"),
        "pending_bookings": _count("room", "Booking", status="pending"),
        "confirmed_bookings": _count("room", "Booking", status="confirmed"),
        "total_guests": _count("accounts", "Guest"),
        "total_properties": _count("properties", "Property"),
        "active_properties": _count("properties", "Property", is_active=True),
        "total_travel_agencies": _count("properties", "TravelAgency"),
        "active_travel_agencies": _count("properties", "TravelAgency", status="active"),
        "total_payments": _count("payments", "Payment"),
        "completed_payments": _count("payments", "Payment", status="completed"),
        "total_revenue": _sum("payments", "Payment", "amount", status="completed"),
        "revenue_mtd": revenue_mtd,
        "total_invoices": _count("payments", "Invoice"),
        "paid_invoices": _count("payments", "Invoice", status="paid"),
        "total_contracts": _count("contracts", "Contract"),
        "active_contracts": _count("contracts", "Contract", status="active"),
        "pending_contracts": _count("contracts", "Contract", status="pending"),
        "unread_notifications": _count(
            "notifications", "Notification", user=request.user, status="unread"
        ),
        **day,
    }
    return Response(data)
