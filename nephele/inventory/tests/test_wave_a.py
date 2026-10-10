"""Wave A hardening tests: allotment defaults, cancel hold, deposit modes."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from inventory.booking_engine import cancel_hold, create_hold, quote
from inventory.models import RatePlan, RatePlanPrice, RoomType, RoomTypeAvailability
from inventory.services import ensure_room_type_availability, physical_room_count
from properties.models import Property
from room.models import Room


@pytest.fixture
def catalog(db):
    prop = Property.objects.create(
        name="Wave A Hotel",
        location="Athens",
        address="1 Wave",
        city="Athens",
        postal_code="10000",
        country="Greece",
    )
    rt = RoomType.objects.create(
        property=prop,
        code="DLX",
        name="Deluxe",
        capacity=2,
        base_occupancy=2,
        max_occupancy=3,
        base_price=Decimal("100.00"),
    )
    for i in range(3):
        Room.objects.create(
            room_number=f"2{i}1",
            floor=2,
            room_type="deluxe",
            capacity=2,
            number_of_beds=1,
            base_price=Decimal("100"),
            current_price=Decimal("100"),
            property=prop,
            room_type_fk=rt,
        )
    rp = RatePlan.objects.create(
        property=prop, code="FLEX", name="Flexible", meal_plan="BB"
    )
    rp.room_types.add(rt)
    check_in = date.today() + timedelta(days=21)
    check_out = check_in + timedelta(days=2)
    for d in (check_in, check_in + timedelta(days=1)):
        RatePlanPrice.objects.create(
            rate_plan=rp, room_type=rt, date=d, price_2=Decimal("100.00")
        )
    return {
        "property": prop,
        "room_type": rt,
        "rate_plan": rp,
        "check_in": check_in,
        "check_out": check_out,
    }


@pytest.mark.unit
@pytest.mark.django_db
def test_ensure_allotment_defaults_to_physical_count(catalog):
    rt = catalog["room_type"]
    night = catalog["check_in"]
    avail = ensure_room_type_availability(rt, night)
    assert physical_room_count(rt) == 3
    assert avail.allotment == 3


@pytest.mark.unit
@pytest.mark.django_db
def test_quote_seeds_missing_calendar(catalog):
    products = quote(
        catalog["property"].id,
        catalog["check_in"],
        catalog["check_out"],
        adults=2,
    )
    assert products
    assert products[0]["available_allotment"] >= 1


@pytest.mark.unit
@pytest.mark.django_db
def test_deposit_and_cancel_hold(catalog):
    booking = create_hold(
        property_id=catalog["property"].id,
        room_type_id=catalog["room_type"].id,
        rate_plan_id=catalog["rate_plan"].id,
        check_in=catalog["check_in"],
        check_out=catalog["check_out"],
        adults=2,
        guest_email="wavea@example.com",
        guest_name="Wave Tester",
        payment_mode="deposit",
        deposit_percent="30.00",
    )
    assert booking.status == "held"
    assert "payment_mode=deposit" in booking.notes
    assert booking.deposit_due > 0
    booked = RoomTypeAvailability.objects.get(
        room_type=catalog["room_type"], date=catalog["check_in"]
    ).booked
    assert booked == 1

    cancelled = cancel_hold(booking.id)
    assert cancelled.status == "cancelled"
    booked_after = RoomTypeAvailability.objects.get(
        room_type=catalog["room_type"], date=catalog["check_in"]
    ).booked
    assert booked_after == 0


@pytest.mark.unit
@pytest.mark.django_db
def test_pay_at_hotel_zero_deposit(catalog):
    booking = create_hold(
        property_id=catalog["property"].id,
        room_type_id=catalog["room_type"].id,
        rate_plan_id=catalog["rate_plan"].id,
        check_in=catalog["check_in"],
        check_out=catalog["check_out"],
        adults=2,
        guest_email="hotelpay@example.com",
        guest_first_name="Hotel",
        guest_last_name="Pay",
        payment_mode="pay_at_hotel",
    )
    assert booking.deposit_due == Decimal("0.00")
