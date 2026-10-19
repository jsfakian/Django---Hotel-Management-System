"""Direct tests for calculate_guest_analytics / _store_guest_analytics."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from freezegun import freeze_time

from analytics.models import DashboardGuestAnalytics
from analytics.tasks import calculate_guest_analytics
from accounts.models import Guest
from properties.models import Property
from room.models import Booking, Room

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def _property(name="Acropolis Test"):
    return Property.objects.create(
        name=name,
        location="Athens",
        address="1 Main St",
        city="Athens",
        postal_code="10000",
        country="Greece",
    )


def _room(prop, number="101"):
    return Room.objects.create(
        property=prop,
        room_number=number,
        floor=1,
        room_type="double",
        capacity=2,
        number_of_beds=1,
        base_price=Decimal("100.00"),
        current_price=Decimal("100.00"),
        status="available",
    )


def _guest(email):
    return Guest.objects.create(
        email=email,
        first_name="Test",
        last_name="Guest",
        country="Greece",
    )


def _booking(room, guest, check_in, nights, status="checked_in"):
    return Booking.objects.create(
        room=room,
        guest=guest,
        check_in_date=check_in,
        check_out_date=check_in + timedelta(days=nights),
        status=status,
        base_price=Decimal("200.00"),
        actual_price=Decimal("226.00"),
        number_of_guests=2,
        adults=2,
        date_of_reservation=check_in - timedelta(days=10),
    )


@freeze_time("2026-10-19 12:00:00")
def test_calculate_guest_analytics_exact_counts():
    today = timezone.now().date()
    prop = _property()
    other = _property("Other Hotel")
    room = _room(prop)
    other_room = _room(other, "201")

    new_guest = _guest("new@example.com")
    returning = _guest("returning@example.com")
    # Prior stay for returning guest (checked out before today)
    _booking(room, returning, today - timedelta(days=40), 3, status="checked_out")
    # In-house today
    _booking(room, new_guest, today - timedelta(days=1), 3, status="checked_in")
    _booking(room, returning, today - timedelta(days=1), 4, status="checked_in")
    # Other property must not leak in
    _booking(other_room, _guest("other@example.com"), today - timedelta(days=1), 2)

    calculate_guest_analytics(property_id=prop.id, analytics_date=today)

    row = DashboardGuestAnalytics.objects.get(property=prop, analytics_date=today)
    assert row.total_unique_guests == 2
    assert row.new_guests == 1
    assert row.returning_guests == 1
    assert row.retention_rate == Decimal("50.00")
    # avg stay: new guest 3 nights, returning 4 nights → 3.5
    assert row.avg_length_of_stay == Decimal("3.50")
    assert not DashboardGuestAnalytics.objects.filter(property=other).exists()


@freeze_time("2026-10-19 12:00:00")
def test_calculate_guest_analytics_updates_existing_row():
    today = timezone.now().date()
    prop = _property()
    room = _room(prop)
    guest = _guest("solo@example.com")
    _booking(room, guest, today, 2, status="checked_in")

    calculate_guest_analytics(property_id=prop.id, analytics_date=today)
    first = DashboardGuestAnalytics.objects.get(property=prop, analytics_date=today)
    assert first.total_unique_guests == 1

    _booking(room, _guest("second@example.com"), today, 5, status="checked_in")
    calculate_guest_analytics(property_id=prop.id, analytics_date=today)
    first.refresh_from_db()
    assert first.total_unique_guests == 2
    assert DashboardGuestAnalytics.objects.filter(
        property=prop, analytics_date=today
    ).count() == 1


@freeze_time("2026-10-19 12:00:00")
def test_calculate_guest_analytics_unknown_property_is_noop():
    calculate_guest_analytics(property_id=999999)
    assert DashboardGuestAnalytics.objects.count() == 0
