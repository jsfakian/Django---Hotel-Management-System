# nephele/inventory/tests/test_wave_security.py
"""Waves A–D security: hold tokens, guest isolation, payment gate, scopes."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from accounts.models import Employee, Guest
from inventory.booking_engine import (
    HoldTokenError,
    PaymentRequiredError,
    cancel_hold,
    confirm_hold,
    create_hold,
    modify_hold,
)
from inventory.models import RatePlan, RatePlanPrice, RoomType, RoomTypeAvailability
from properties.models import Property
from room.models import Room


@pytest.fixture
def catalog(db):
    prop = Property.objects.create(
        name="Sec Hotel",
        location="Athens",
        address="1 Sec",
        city="Athens",
        postal_code="10000",
        country="GR",
    )
    rt = RoomType.objects.create(
        property=prop,
        code="STD",
        name="Standard",
        capacity=2,
        base_occupancy=2,
        max_occupancy=2,
        base_price=Decimal("80.00"),
    )
    Room.objects.create(
        room_number="101",
        floor=1,
        room_type="double",
        capacity=2,
        number_of_beds=1,
        base_price=Decimal("80"),
        current_price=Decimal("80"),
        property=prop,
        room_type_fk=rt,
    )
    rp = RatePlan.objects.create(
        property=prop, code="BAR", name="BAR", meal_plan="RO"
    )
    rp.room_types.add(rt)
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=2)
    for d in (check_in, check_in + timedelta(days=1)):
        RoomTypeAvailability.objects.create(
            room_type=rt, date=d, allotment=3, booked=0
        )
        RatePlanPrice.objects.create(
            rate_plan=rp, room_type=rt, date=d, price_2=Decimal("80.00")
        )
    return {
        "property": prop,
        "room_type": rt,
        "rate_plan": rp,
        "check_in": check_in,
        "check_out": check_out,
    }


def _hold(catalog, email="sec@example.com", **kwargs):
    defaults = dict(
        property_id=catalog["property"].id,
        room_type_id=catalog["room_type"].id,
        rate_plan_id=catalog["rate_plan"].id,
        check_in=catalog["check_in"],
        check_out=catalog["check_out"],
        adults=1,
        guest_email=email,
        guest_first_name="Sec",
        guest_last_name="Guest",
        payment_mode="pay_at_hotel",
    )
    defaults.update(kwargs)
    return create_hold(**defaults)


@pytest.mark.unit
@pytest.mark.django_db
def test_create_hold_returns_hold_token(catalog):
    booking = _hold(catalog)
    assert booking.hold_token
    assert len(booking.hold_token) >= 32


@pytest.mark.unit
@pytest.mark.django_db
def test_cancel_hold_requires_token(catalog):
    booking = _hold(catalog, email="tok@example.com")
    with pytest.raises(HoldTokenError):
        cancel_hold(booking.id)
    with pytest.raises(HoldTokenError):
        cancel_hold(booking.id, hold_token="wrong-token")
    cancelled = cancel_hold(booking.id, hold_token=booking.hold_token)
    assert cancelled.status == "cancelled"


@pytest.mark.unit
@pytest.mark.django_db
def test_public_hold_does_not_reuse_existing_guest(catalog):
    existing = Guest.objects.create(
        email="reuse@example.com",
        first_name="Existing",
        last_name="Profile",
    )
    booking = _hold(catalog, email="reuse@example.com")
    assert booking.guest_id != existing.id
    assert booking.guest.user_id
    assert not booking.guest.user.has_usable_password()
    assert booking.guest.preferences.get("contact_email") == "reuse@example.com"


@pytest.mark.unit
@pytest.mark.django_db
def test_confirm_deposit_requires_paid_payment(catalog, settings):
    settings.DEBUG = False
    settings.PAYMENT_DEMO = False
    settings.VIVA_MERCHANT_ID = ""
    settings.VIVA_API_KEY = ""
    booking = _hold(
        catalog, email="pay@example.com", payment_mode="deposit"
    )
    with pytest.raises(PaymentRequiredError):
        confirm_hold(
            booking.id,
            payment_ref="viva-demo-abc123",
            payment_mode="deposit",
            hold_token=booking.hold_token,
        )
    booking.refresh_from_db()
    assert booking.status == "held"


@pytest.mark.unit
@pytest.mark.django_db
def test_confirm_deposit_demo_paid_when_debug(catalog, settings):
    settings.DEBUG = True
    settings.VIVA_MERCHANT_ID = ""
    settings.VIVA_API_KEY = ""
    booking = _hold(
        catalog, email="demod@example.com", payment_mode="deposit"
    )
    confirmed = confirm_hold(
        booking.id,
        payment_ref="viva-demo-paidok12",
        payment_mode="deposit",
        hold_token=booking.hold_token,
    )
    assert confirmed.status == "confirmed"


@pytest.mark.unit
@pytest.mark.django_db
def test_modify_hold_rejects_other_property_room_type(catalog):
    other = Property.objects.create(
        name="Other",
        location="X",
        address="2",
        city="X",
        postal_code="1",
        country="GR",
    )
    other_rt = RoomType.objects.create(
        property=other,
        code="OTH",
        name="Other RT",
        capacity=2,
        base_price=Decimal("50"),
    )
    booking = _hold(catalog, email="scope@example.com")
    from inventory.booking_engine import BookingEngineError

    with pytest.raises(BookingEngineError):
        modify_hold(
            booking.id,
            room_type_id=other_rt.id,
            hold_token=booking.hold_token,
        )


@pytest.mark.unit
@pytest.mark.django_db
def test_confirmation_hides_email_without_token(catalog):
    booking = _hold(catalog, email="pii@example.com")
    client = APIClient()
    url = f"/api/v1/booking-engine/confirmation/{booking.id}/"
    bare = client.get(url)
    assert bare.status_code == 200
    assert "guest_email" not in bare.data
    assert set(bare.data.keys()) <= {"booking_id", "status"}

    ok = client.get(url, {"hold_token": booking.hold_token})
    assert ok.status_code == 200
    assert ok.data.get("guest_email") == "pii@example.com"


@pytest.mark.unit
@pytest.mark.django_db
def test_confirm_rejects_pay_at_hotel_downgrade(catalog, settings):
    settings.DEBUG = False
    settings.PAYMENT_DEMO = False
    booking = _hold(catalog, email="down@example.com", payment_mode="deposit")
    with pytest.raises(PaymentRequiredError):
        confirm_hold(
            booking.id,
            payment_mode="pay_at_hotel",
            hold_token=booking.hold_token,
        )
    booking.refresh_from_db()
    assert booking.status == "held"


@pytest.mark.unit
@pytest.mark.django_db
def test_modify_rejects_pay_at_hotel_downgrade(catalog):
    from inventory.booking_engine import BookingEngineError

    booking = _hold(catalog, email="modedown@example.com", payment_mode="deposit")
    with pytest.raises(BookingEngineError):
        modify_hold(
            booking.id,
            payment_mode="pay_at_hotel",
            hold_token=booking.hold_token,
        )
    booking.refresh_from_db()
    assert "payment_mode=deposit" in (booking.notes or "")


@pytest.mark.unit
@pytest.mark.django_db
def test_confirm_api_rejects_missing_token(catalog):
    booking = _hold(catalog, email="api@example.com")
    client = APIClient()
    resp = client.post(
        "/api/v1/booking-engine/confirm/",
        {
            "booking_id": booking.id,
            "payment_mode": "pay_at_hotel",
        },
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.unit
@pytest.mark.django_db
def test_police_export_scoped_to_staff_property(catalog):
    prop = catalog["property"]
    other = Property.objects.create(
        name="Other Prop",
        location="Y",
        address="3",
        city="Y",
        postal_code="2",
        country="GR",
    )
    user = User.objects.create_user("recv1", password="x")
    Group.objects.get_or_create(name="receptionist")
    user.groups.add(Group.objects.get(name="receptionist"))
    Employee.objects.create(user=user, property=prop, position="Front desk")
    client = APIClient()
    client.force_authenticate(user=user)

    allowed = client.get(
        "/api/v1/compliance/police-sheet/",
        {"property_id": prop.id, "format": "json"},
    )
    assert allowed.status_code == 200

    denied = client.get(
        "/api/v1/compliance/police-sheet/",
        {"property_id": other.id, "format": "json"},
    )
    assert denied.status_code == 403
