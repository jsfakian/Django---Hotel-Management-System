# nephele/channels/tests/test_connectors.py
"""Unit tests for channel connectors (iCal + Booking.com stub)."""

import hashlib
import hmac
import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.test import APIClient

from accounts.models import Guest
from channels.connectors import get_connector
from channels.connectors.booking_com import (
    BookingComConnector,
    normalize_booking_payload,
)
from channels.connectors.expedia import ExpediaConnector
from channels.connectors.ical import ICalConnector, parse_vevents
from channels.models import Channel, ChannelBooking, ChannelWebhookLog
from channels.tasks import channel_health_snapshot
from properties.models import Property
from room.models import Booking, Room


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
    assert isinstance(get_connector("expedia"), ExpediaConnector)
    assert get_connector("unknown_ota") is None


@pytest.mark.unit
def test_expedia_stub_not_implemented():
    result = ExpediaConnector().push_rates(channel=None)
    assert result["status"] == "not_implemented"
    assert "next OTA by demand" in result["message"]


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
    assert "Ical Guest" not in feed
    assert "SUMMARY:Reserved" in feed or "SUMMARY:" in feed


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
def test_booking_com_push_rates_and_pull_not_implemented_when_stubbed(
    booking_com_channel,
):
    conn = BookingComConnector()
    rates = conn.push_rates(booking_com_channel)
    assert rates["status"] == "not_implemented"
    assert rates["prepared_rates"]
    assert conn.pull_bookings(booking_com_channel)["status"] == "not_implemented"
    wh = conn.receive_webhook(booking_com_channel, {"reservation_id": "x"})
    assert wh["status"] == "not_implemented"


@pytest.mark.unit
def test_normalize_booking_payload():
    normalized = normalize_booking_payload(
        {
            "reservation": {
                "id": "BCOM-99",
                "checkin": "2026-06-01",
                "checkout": "2026-06-03",
                "guest": {
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "email": "ada@example.com",
                },
                "rooms": [{"room_id": "rt-1", "rate_id": "rp-9"}],
            }
        }
    )
    assert normalized["external_id"] == "BCOM-99"
    assert normalized["guest_first_name"] == "Ada"
    assert normalized["room_type_remote_id"] == "rt-1"


@pytest.mark.unit
@pytest.mark.django_db
def test_booking_com_webhook_live_parses(booking_com_channel, settings):
    settings.BOOKING_COM_LIVE = True
    result = BookingComConnector().receive_webhook(
        booking_com_channel,
        {"reservation_id": "XYZ", "checkin": "2026-07-01", "checkout": "2026-07-02"},
    )
    assert result["status"] == "ok"
    assert result["booking"]["external_id"] == "XYZ"


@pytest.mark.unit
@pytest.mark.django_db
def test_booking_com_live_push_availability_posts_json(booking_com_channel, settings):
    settings.BOOKING_COM_LIVE = True
    settings.BOOKING_COM_API_BASE = "https://supply-xml.booking.com"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"ok":true}'
    mock_resp.text = '{"ok":true}'
    mock_resp.json.return_value = {"ok": True}
    night = date.today() + timedelta(days=10)
    # requests is imported inside _http_post_json — patch the stdlib module.
    with patch("requests.post", return_value=mock_resp) as post_req:
        result = BookingComConnector().push_availability(
            booking_com_channel, date_from=night, date_to=night + timedelta(days=1)
        )
    assert result["status"] == "ok"
    assert result["operation"] == "push_availability"
    assert "request_payload" in result
    assert result["request_payload"]["hotel_id"] == "hotel-123"
    assert "rooms" in result["request_payload"]
    post_req.assert_called_once()
    args, kwargs = post_req.call_args
    assert args[0].endswith("/hotels/hotel-123/availability")
    assert kwargs["json"]["rooms"]


@pytest.mark.unit
@pytest.mark.django_db
def test_booking_com_live_push_rates_puts_json(booking_com_channel, settings):
    settings.BOOKING_COM_LIVE = True
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"ok":true}'
    mock_resp.text = '{"ok":true}'
    mock_resp.json.return_value = {"ok": True}
    night = date.today() + timedelta(days=10)
    with patch("requests.put", return_value=mock_resp) as put_req:
        result = BookingComConnector().push_rates(
            booking_com_channel, date_from=night, date_to=night + timedelta(days=1)
        )
    assert result["status"] == "ok"
    assert result["operation"] == "push_rates"
    assert result["request_payload"]["hotel_id"] == "hotel-123"
    assert "rates" in result["request_payload"]
    put_req.assert_called_once()
    args, kwargs = put_req.call_args
    assert args[0].endswith("/hotels/hotel-123/rates")
    assert kwargs["json"]["rates"]


@pytest.mark.unit
@pytest.mark.django_db
def test_booking_com_live_pull_bookings_gets_json(booking_com_channel, settings):
    settings.BOOKING_COM_LIVE = True
    settings.BOOKING_COM_API_BASE = "https://supply-xml.booking.com"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"reservations":[{"id":"BCOM-PULL-1","checkin":"2026-08-01","checkout":"2026-08-03"}]}'
    mock_resp.text = mock_resp.content.decode()
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.json.return_value = {
        "reservations": [
            {
                "id": "BCOM-PULL-1",
                "checkin": "2026-08-01",
                "checkout": "2026-08-03",
            }
        ]
    }
    with patch("requests.get", return_value=mock_resp) as get_req:
        result = BookingComConnector().pull_bookings(booking_com_channel)
    assert result["status"] == "ok"
    assert result["operation"] == "pull_bookings"
    assert result["count"] == 1
    assert result["bookings"][0]["external_id"] == "BCOM-PULL-1"
    get_req.assert_called_once()
    args, _kwargs = get_req.call_args
    assert args[0].endswith("/hotels/hotel-123/reservations")


def _sign(body: str, secret: str) -> str:
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


@pytest.mark.unit
@pytest.mark.django_db
def test_booking_com_webhook_receive_creates_and_updates_booking(
    booking_com_channel, property_obj, settings
):
    """LIVE webhook path creates a booking, then updates on redelivery."""
    settings.BOOKING_COM_LIVE = True
    booking_com_channel.accept_bookings = True
    booking_com_channel.save(update_fields=["accept_bookings"])
    room = Room.objects.create(
        room_number="501",
        floor=5,
        room_type="deluxe",
        capacity=2,
        number_of_beds=1,
        base_price=Decimal("100"),
        current_price=Decimal("100"),
        property=property_obj,
    )
    check_in = (date.today() + timedelta(days=30)).isoformat()
    check_out = (date.today() + timedelta(days=32)).isoformat()
    payload = {
        "reservation": {
            "id": "BCOM-LIVE-1",
            "checkin": check_in,
            "checkout": check_out,
            "total": "220.00",
            "currency": "EUR",
            "guest": {
                "first_name": "Nikos",
                "last_name": "Papas",
                "email": "nikos.bcom@example.com",
            },
            "rooms": [{"room_id": "bcom-rt-1", "rate_id": "bcom-rp-9"}],
        }
    }
    body = json.dumps(payload)
    client = APIClient()
    url = f"/api/v1/channels/{booking_com_channel.id}/bookings/"
    sig = _sign(body, booking_com_channel.api_secret)
    resp = client.post(
        url,
        data=body,
        content_type="application/json",
        HTTP_X_WEBHOOK_SIGNATURE=sig,
    )
    assert resp.status_code == 201, resp.content
    assert ChannelBooking.objects.filter(
        channel=booking_com_channel, channel_booking_id="BCOM-LIVE-1"
    ).exists()
    booking = ChannelBooking.objects.get(
        channel=booking_com_channel, channel_booking_id="BCOM-LIVE-1"
    ).nephele_booking
    assert (
        booking.guest.email == "nikos.bcom@example.com"
        or (booking.guest.preferences or {}).get("contact_email")
        == "nikos.bcom@example.com"
    )
    assert booking.guest.user_id
    assert not booking.guest.user.has_usable_password()

    # Update path: change checkout and total
    payload["reservation"]["checkout"] = (date.today() + timedelta(days=33)).isoformat()
    payload["reservation"]["total"] = "330.00"
    body2 = json.dumps(payload)
    sig2 = _sign(body2, booking_com_channel.api_secret)
    resp2 = client.post(
        url,
        data=body2,
        content_type="application/json",
        HTTP_X_WEBHOOK_SIGNATURE=sig2,
    )
    assert resp2.status_code == 200, resp2.content
    assert resp2.data["status"] == "updated"
    booking.refresh_from_db()
    assert booking.actual_price == Decimal("330.00")
    # silence unused room for mapping fallback
    assert room.id


@pytest.mark.unit
@pytest.mark.django_db
def test_channel_health_snapshot(ical_channel):
    snap = channel_health_snapshot(ical_channel)
    assert snap["channel_id"] == ical_channel.id
    assert snap["connector"] == "ical"
    assert "healthy" in snap


@pytest.mark.unit
def test_normalize_mapping_config_accepts_aliases():
    from channels.mapping_utils import normalize_mapping_config

    cfg = normalize_mapping_config(
        {"room_mappings": {"5": "remote-rt"}, "rate_mappings": {"9": "remote-rp"}}
    )
    assert cfg["room_type_mappings"]["5"] == "remote-rt"
    assert cfg["rate_plan_mappings"]["9"] == "remote-rp"


@pytest.mark.unit
@pytest.mark.django_db
def test_booking_com_prepared_payloads_include_ari(booking_com_channel):
    from decimal import Decimal

    from inventory.models import RatePlan, RatePlanPrice, RoomType, RoomTypeAvailability

    prop = booking_com_channel.property
    rt = RoomType.objects.create(
        property=prop, name="Std", code="STD", capacity=2, max_occupancy=2
    )
    rp = RatePlan.objects.create(
        property=prop, name="BAR", code="BAR", meal_plan="RO"
    )
    rp.room_types.add(rt)
    night = date.today() + timedelta(days=14)
    RoomTypeAvailability.objects.create(
        room_type=rt, date=night, allotment=4, booked=1
    )
    RatePlanPrice.objects.create(
        rate_plan=rp, room_type=rt, date=night, price_2=Decimal("120.00")
    )
    booking_com_channel.mapping_config = {
        "room_mappings": {str(rt.id): "bcom-rt-x"},
        "rate_mappings": {str(rp.id): "bcom-rp-x"},
    }
    booking_com_channel.save(update_fields=["mapping_config"])

    conn = BookingComConnector()
    rooms = conn._prepared_room_types(
        booking_com_channel, night, night + timedelta(days=1)
    )
    rates = conn._prepared_rate_plans(
        booking_com_channel, night, night + timedelta(days=1)
    )
    assert rooms[0]["nights"]
    assert rooms[0]["nights"][0]["allotment"] == 4
    assert rates[0]["prices"]
    assert rates[0]["prices"][0]["price"] == "120.00"
    assert conn.map_room_type(booking_com_channel, rt.id) == "bcom-rt-x"


@pytest.mark.unit
@pytest.mark.django_db
def test_webhook_does_not_hijack_existing_guest_by_email(
    booking_com_channel, property_obj, settings
):
    settings.BOOKING_COM_LIVE = True
    booking_com_channel.accept_bookings = True
    booking_com_channel.save(update_fields=["accept_bookings"])
    Room.objects.create(
        room_number="601",
        floor=6,
        room_type="deluxe",
        capacity=2,
        number_of_beds=1,
        base_price=Decimal("100"),
        current_price=Decimal("100"),
        property=property_obj,
    )
    existing = Guest.objects.create(
        email="shared@example.com",
        first_name="Existing",
        last_name="Guest",
    )
    check_in = (date.today() + timedelta(days=40)).isoformat()
    check_out = (date.today() + timedelta(days=42)).isoformat()
    payload = {
        "reservation": {
            "id": "BCOM-NOHIJACK",
            "checkin": check_in,
            "checkout": check_out,
            "total": "100.00",
            "guest": {
                "first_name": "New",
                "last_name": "Arrival",
                "email": "shared@example.com",
            },
            "rooms": [{"room_id": "bcom-rt-1"}],
        }
    }
    body = json.dumps(payload)
    client = APIClient()
    resp = client.post(
        f"/api/v1/channels/{booking_com_channel.id}/bookings/",
        data=body,
        content_type="application/json",
        HTTP_X_WEBHOOK_SIGNATURE=_sign(body, booking_com_channel.api_secret),
    )
    assert resp.status_code == 201, resp.content
    cb = ChannelBooking.objects.get(
        channel=booking_com_channel, channel_booking_id="BCOM-NOHIJACK"
    )
    assert cb.nephele_booking.guest_id != existing.id
    log = ChannelWebhookLog.objects.filter(
        channel=booking_com_channel, event="booking"
    ).latest("id")
    assert log.payload.get("guest_email") == "[REDACTED]"
    assert log.payload.get("guest_first_name") == "[REDACTED]"


@pytest.mark.unit
def test_redact_webhook_pii_helper():
    from channels.views import _redact_webhook_pii

    redacted = _redact_webhook_pii(
        {
            "guest_email": "a@b.com",
            "guest_first_name": "Ada",
            "channel_booking_id": "X1",
            "nested": {"email": "x@y.com", "room_id": 1},
        }
    )
    assert redacted["guest_email"] == "[REDACTED]"
    assert redacted["guest_first_name"] == "[REDACTED]"
    assert redacted["channel_booking_id"] == "X1"
    assert redacted["nested"]["email"] == "[REDACTED]"
    assert redacted["nested"]["room_id"] == 1
