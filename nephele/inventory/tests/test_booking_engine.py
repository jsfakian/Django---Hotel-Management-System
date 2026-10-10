# nephele/inventory/tests/test_booking_engine.py
"""Unit tests for the public booking engine (hold / confirm / expire / taxes)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from inventory.booking_engine import (
    HoldExpiredError,
    NoAllotmentError,
    compute_taxes,
    confirm_hold,
    create_hold,
    expire_holds,
    quote,
)
from inventory.models import RatePlan, RatePlanPrice, RoomType, RoomTypeAvailability
from properties.models import Property
from room.models import Booking


@pytest.fixture
def property_obj(db):
    return Property.objects.create(
        name="Engine Hotel",
        location="Athens",
        address="1 Syntagma",
        city="Athens",
        postal_code="10563",
        country="GR",
    )


@pytest.fixture
def catalog(db, property_obj):
    rt = RoomType.objects.create(
        property=property_obj,
        code="SGL",
        name="Single",
        capacity=1,
        base_occupancy=1,
        max_occupancy=2,
        base_price=Decimal("70.00"),
    )
    rp = RatePlan.objects.create(
        property=property_obj,
        code="RO",
        name="Room Only",
        meal_plan="RO",
        is_refundable=True,
    )
    rp.room_types.add(rt)
    check_in = date.today() + timedelta(days=20)
    check_out = check_in + timedelta(days=2)
    for night in (check_in, check_in + timedelta(days=1)):
        RoomTypeAvailability.objects.create(
            room_type=rt,
            date=night,
            allotment=2,
            booked=0,
            min_stay=1,
            max_stay=0,
        )
        RatePlanPrice.objects.create(
            rate_plan=rp,
            room_type=rt,
            date=night,
            price_1=Decimal("70.00"),
            price_2=Decimal("90.00"),
        )
    return {
        "property": property_obj,
        "room_type": rt,
        "rate_plan": rp,
        "check_in": check_in,
        "check_out": check_out,
    }


@pytest.mark.unit
def test_compute_taxes_greek_vat_and_climate(settings):
    settings.DEFAULT_VAT_RATE = "0.13"
    settings.CLIMATE_FEE_PER_NIGHT = "2.00"
    taxes = compute_taxes(Decimal("100.00"), nights=3)
    assert taxes["vat_amount"] == Decimal("13.00")
    assert taxes["climate_resilience_fee"] == Decimal("6.00")
    assert taxes["total_with_taxes"] == Decimal("119.00")


@pytest.mark.unit
@pytest.mark.django_db
def test_quote_includes_tax_fields(catalog, settings):
    settings.DEFAULT_VAT_RATE = "0.13"
    settings.CLIMATE_FEE_PER_NIGHT = "1.50"
    products = quote(
        catalog["property"].id,
        catalog["check_in"],
        catalog["check_out"],
        adults=1,
    )
    assert products
    assert "vat_amount" in products[0]
    assert "climate_resilience_fee" in products[0]
    assert "total_with_taxes" in products[0]


@pytest.mark.unit
@pytest.mark.django_db
def test_create_hold_decrements_allotment(catalog):
    booking = create_hold(
        property_id=catalog["property"].id,
        room_type_id=catalog["room_type"].id,
        rate_plan_id=catalog["rate_plan"].id,
        check_in=catalog["check_in"],
        check_out=catalog["check_out"],
        adults=1,
        children=0,
        guest_email="hold@example.com",
        guest_name="Hold Guest",
        ttl_minutes=15,
    )
    assert booking.status == "held"
    assert booking.hold_expires_at is not None
    assert booking.vat_amount is not None
    assert booking.climate_resilience_fee is not None
    for night in (catalog["check_in"], catalog["check_in"] + timedelta(days=1)):
        avail = RoomTypeAvailability.objects.get(
            room_type=catalog["room_type"], date=night
        )
        assert avail.booked == 1


@pytest.mark.unit
@pytest.mark.django_db
def test_create_hold_raises_when_no_allotment(catalog):
    RoomTypeAvailability.objects.filter(room_type=catalog["room_type"]).update(
        allotment=1, booked=1
    )
    with pytest.raises(NoAllotmentError):
        create_hold(
            property_id=catalog["property"].id,
            room_type_id=catalog["room_type"].id,
            rate_plan_id=catalog["rate_plan"].id,
            check_in=catalog["check_in"],
            check_out=catalog["check_out"],
            adults=1,
            guest_email="full@example.com",
            guest_name="Full House",
        )


@pytest.mark.unit
@pytest.mark.django_db
def test_confirm_hold_sets_confirmed(catalog):
    booking = create_hold(
        property_id=catalog["property"].id,
        room_type_id=catalog["room_type"].id,
        rate_plan_id=catalog["rate_plan"].id,
        check_in=catalog["check_in"],
        check_out=catalog["check_out"],
        adults=1,
        guest_email="confirm@example.com",
        guest_name="Confirm Guest",
    )
    confirmed = confirm_hold(booking.id, payment_ref="pay_123")
    assert confirmed.status == "confirmed"
    assert confirmed.hold_expires_at is None
    assert "pay_123" in (confirmed.notes or "")


@pytest.mark.unit
@pytest.mark.django_db
def test_confirm_expired_hold_raises(catalog):
    booking = create_hold(
        property_id=catalog["property"].id,
        room_type_id=catalog["room_type"].id,
        rate_plan_id=catalog["rate_plan"].id,
        check_in=catalog["check_in"],
        check_out=catalog["check_out"],
        adults=1,
        guest_email="expired@example.com",
        guest_name="Expired Guest",
    )
    Booking.objects.filter(pk=booking.pk).update(
        hold_expires_at=timezone.now() - timedelta(minutes=1)
    )
    with pytest.raises(HoldExpiredError):
        confirm_hold(booking.id)


@pytest.mark.unit
@pytest.mark.django_db
def test_expire_holds_restores_allotment(catalog):
    booking = create_hold(
        property_id=catalog["property"].id,
        room_type_id=catalog["room_type"].id,
        rate_plan_id=catalog["rate_plan"].id,
        check_in=catalog["check_in"],
        check_out=catalog["check_out"],
        adults=1,
        guest_email="ttl@example.com",
        guest_name="TTL Guest",
    )
    Booking.objects.filter(pk=booking.pk).update(
        hold_expires_at=timezone.now() - timedelta(minutes=5)
    )
    count = expire_holds()
    assert count == 1
    booking.refresh_from_db()
    assert booking.status == "cancelled"
    for night in (catalog["check_in"], catalog["check_in"] + timedelta(days=1)):
        avail = RoomTypeAvailability.objects.get(
            room_type=catalog["room_type"], date=night
        )
        assert avail.booked == 0
