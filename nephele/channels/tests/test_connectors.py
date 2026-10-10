# nephele/channels/tests/test_connectors.py
"""Unit tests for channel connectors (iCal + Booking.com stub)."""

from datetime import date, timedelta

import pytest

from channels.connectors import get_connector
from channels.connectors.booking_com import BookingComConnector
from channels.connectors.ical import ICalConnector, parse_vevents
from channels.models import Channel
from channels.tasks import channel_health_snapshot
from properties.models import Property
from room.models import Booking, Room
from accounts.models import Guest


@pytest.fixture
def property_obj(db):
    return Property.objects.create(
        name="Channel Hotel",
        location="Rhodes",
        address="3 Harbor",
        city="Rhodes",
        postal_code="85100",
        country="GR",
    )


@pytest.fixture
def ical_channel(db, property_obj):
    return Channel.objects.create(
        property=property_obj,
        channel_name="ical",
        channel_type="direct",
        account_id="https://example.com/feed.ics",
        api_key="n/a",
        mapping_config={"ical_url": "https://example.com/feed.ics"},
        is_active=True,
        sync_enabled=True,
        accept_bookings=True,
    )


@pytest.fixture
def booking_com_channel(db, property_obj):
    return Channel.objects.create(
        property=property_obj,
        channel_name="booking_com",
        channel_type="ota",
        account_id="hotel-123",
        api_key="key",
        api_secret="secret",
        mapping_config={
            "room_type_mappings": {"1": "bcom-rt-1"},
            "rate_plan_mappings": {"9": "bcom-rp-9"},
        },
        is_active=True,
        sync_enabled=True,
    )


@pytest.mark.unit
def test_registry_returns_connectors():
    assert isinstance(get_connector("ical"), ICalConnector)
    assert isinstance(get_connector("booking_com"), BookingComConnector)
    assert get_connector("unknown_ota") is None


@pytest.mark.unit
def test_parse_vevents_stdlib():
    ical = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:abc-123
DTSTART;VALUE=DATE:20260315
DTEND;VALUE=DATE:20260317
SUMMARY:Test Stay
END:VEVENT
END:VCALENDAR
"""
    events = parse_vevents(ical)
    assert len(events) == 1
    assert events[0]["uid"] == "abc-123"
    assert events[0]["check_in"] == date(2026, 3, 15)
    assert events[0]["check_out"] == date(2026, 3, 17)


@pytest.mark.unit
@pytest.mark.django_db
def test_ical_export_feed_contains_booking(ical_channel, property_obj):
    room = Room.objects.create(
        room_number="101",
        floor=1,
        room_type="single",
        capacity=1,
        number_of_beds=1,
        base_price=50,
        current_price=50,
        property=property_obj,
    )
    guest = Guest.objects.create(
        email="icalguest@example.com",
        first_name="Ical",
        last_name="Guest",
    )
    check_in = date.today() + timedelta(days=5)
    Booking.objects.create(
        room=room,
        guest=guest,
        check_in_date=check_in,
        check_out_date=check_in + timedelta(days=2),
        number_of_guests=1,
        adults=1,
        base_price=100,
        actual_price=100,
        status="confirmed",
        booking_source="ical",
    )
    feed = ICalConnector().export_feed(ical_channel)
    assert "BEGIN:VEVENT" in feed
    assert "Ical Guest" in feed or "Booking" in feed


@pytest.mark.unit
@pytest.mark.django_db
def test_booking_com_push_availability_not_implemented(booking_com_channel):
    result = BookingComConnector().push_availability(booking_com_channel)
    assert result["status"] == "not_implemented"
    assert result["prepared_rooms"]
    assert BookingComConnector().map_room_type(booking_com_channel, 1) == "bcom-rt-1"
    assert BookingComConnector().map_rate_plan(booking_com_channel, 9) == "bcom-rp-9"


@pytest.mark.unit
@pytest.mark.django_db
def test_channel_health_snapshot(ical_channel):
    snap = channel_health_snapshot(ical_channel)
    assert snap["channel_id"] == ical_channel.id
    assert snap["connector"] == "ical"
    assert "healthy" in snap
