"""API tests for BookingViewSet check_in / check_out actions."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, User
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Guest
from properties.models import Property
from room.models import Booking, Room


@pytest.fixture
def front_desk(db):
    prop = Property.objects.create(
        name="Desk Hotel",
        location="Athens",
        address="1 Desk",
        city="Athens",
        postal_code="10000",
        country="Greece",
    )
    room = Room.objects.create(
        room_number="501",
        floor=5,
        room_type="double",
        capacity=2,
        number_of_beds=1,
        base_price=Decimal("120.00"),
        current_price=Decimal("120.00"),
        property=prop,
        status="available",
    )
    guest_user = User.objects.create_user(username="g_cio", email="g_cio@ex.com")
    guest = Guest.objects.create(
        user=guest_user,
        email="g_cio@ex.com",
        first_name="Check",
        last_name="Guest",
    )
    staff = User.objects.create_user(
        username="recv", email="recv@ex.com", password="pass"
    )
    group, _ = Group.objects.get_or_create(name="receptionist")
    staff.groups.add(group)
    return {"property": prop, "room": room, "guest": guest, "staff": staff}


def _booking(front_desk, status="confirmed"):
    today = timezone.localdate()
    return Booking.objects.create(
        room=front_desk["room"],
        guest=front_desk["guest"],
        check_in_date=today,
        check_out_date=today + timedelta(days=2),
        number_of_guests=2,
        status=status,
        base_price=Decimal("240.00"),
        actual_price=Decimal("240.00"),
    )


@pytest.mark.unit
@pytest.mark.django_db
def test_check_in_sets_status_and_room_occupied(front_desk):
    booking = _booking(front_desk, status="confirmed")
    client = APIClient()
    client.force_authenticate(user=front_desk["staff"])
    resp = client.post(f"/api/v1/bookings/{booking.id}/check_in/")
    assert resp.status_code == 200
    assert resp.data["status"] == "checked_in"
    booking.refresh_from_db()
    front_desk["room"].refresh_from_db()
    assert booking.status == "checked_in"
    assert front_desk["room"].status == "occupied"


@pytest.mark.unit
@pytest.mark.django_db
def test_check_out_sets_status_and_housekeeping(front_desk):
    booking = _booking(front_desk, status="checked_in")
    front_desk["room"].status = "occupied"
    front_desk["room"].save(update_fields=["status"])

    client = APIClient()
    client.force_authenticate(user=front_desk["staff"])
    resp = client.post(f"/api/v1/bookings/{booking.id}/check_out/")
    assert resp.status_code == 200
    assert resp.data["status"] == "checked_out"
    booking.refresh_from_db()
    front_desk["room"].refresh_from_db()
    assert booking.status == "checked_out"
    # booking_checkout_sets_housekeeping signal
    assert front_desk["room"].status == "cleaning"


@pytest.mark.unit
@pytest.mark.django_db
def test_check_in_rejects_invalid_status(front_desk):
    booking = _booking(front_desk, status="checked_out")
    client = APIClient()
    client.force_authenticate(user=front_desk["staff"])
    resp = client.post(f"/api/v1/bookings/{booking.id}/check_in/")
    assert resp.status_code == 400


@pytest.mark.unit
@pytest.mark.django_db
def test_check_out_requires_staff(front_desk):
    booking = _booking(front_desk, status="checked_in")
    guest_user = front_desk["guest"].user
    client = APIClient()
    client.force_authenticate(user=guest_user)
    resp = client.post(f"/api/v1/bookings/{booking.id}/check_out/")
    assert resp.status_code == 403
