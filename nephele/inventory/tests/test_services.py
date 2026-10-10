# nephele/inventory/tests/test_services.py
"""Unit/integration tests for the inventory availability engine."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from inventory.models import RoomAvailability
from inventory.services import (
    ACTIVE_BOOKING_STATUSES,
    apply_booking_to_inventory,
    ensure_room_availability,
    is_room_available,
    recalculate_room_availability,
    release_booking_from_inventory,
)
from properties.models import Property
from room.models import Booking, Room


@pytest.fixture
def property_obj(db):
    return Property.objects.create(
        name="Test Hotel Inv",
        location="Athens",
        address="1 Test St",
        city="Athens",
        postal_code="10431",
        country="GR",
    )


@pytest.fixture
def room(db, property_obj):
    return Room.objects.create(
        room_number="101",
        floor=1,
        room_type="double",
        capacity=2,
        number_of_beds=1,
        base_price=Decimal("100.00"),
        current_price=Decimal("100.00"),
        property=property_obj,
    )


@pytest.mark.unit
def test_ensure_room_availability_creates_row(room):
    on_date = date.today()
    avail = ensure_room_availability(room, on_date)
    assert avail.pk is not None
    assert avail.room_id == room.id
    assert avail.date == on_date
    assert avail.total_units == 1
    assert ensure_room_availability(room, on_date).pk == avail.pk


@pytest.mark.integration
def test_recalculate_counts_active_bookings(room):
    check_in = date.today() + timedelta(days=10)
    check_out = check_in + timedelta(days=3)

    Booking.objects.create(
        room=room,
        check_in_date=check_in,
        check_out_date=check_out,
        base_price=Decimal("300.00"),
        status="confirmed",
    )
    Booking.objects.create(
        room=room,
        check_in_date=check_in,
        check_out_date=check_out,
        base_price=Decimal("300.00"),
        status="cancelled",
    )

    recalculate_room_availability(room, check_in, check_out)

    for night in (check_in, check_in + timedelta(days=1), check_in + timedelta(days=2)):
        avail = RoomAvailability.objects.get(room=room, date=night)
        assert avail.booked_units == 1
        assert avail.available_units == 0


@pytest.mark.integration
def test_is_room_available_false_when_booked(room):
    check_in = date.today() + timedelta(days=20)
    check_out = check_in + timedelta(days=2)
    Booking.objects.create(
        room=room,
        check_in_date=check_in,
        check_out_date=check_out,
        base_price=Decimal("200.00"),
        status="held",
    )
    assert "held" in ACTIVE_BOOKING_STATUSES
    assert is_room_available(room, check_in, check_out) is False
    assert is_room_available(room, check_out, check_out + timedelta(days=1))


@pytest.mark.integration
def test_apply_and_release_booking(room):
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=1)
    booking = Booking.objects.create(
        room=room,
        check_in_date=check_in,
        check_out_date=check_out,
        base_price=Decimal("100.00"),
        status="pending",
    )
    apply_booking_to_inventory(booking)
    avail = RoomAvailability.objects.get(room=room, date=check_in)
    assert avail.booked_units == 1

    booking.status = "cancelled"
    booking.save(update_fields=["status"])
    release_booking_from_inventory(booking)
    avail.refresh_from_db()
    assert avail.booked_units == 0
    assert avail.available_units == 1
