# nephele/inventory/tests/test_quote.py
"""Tests for room-type × rate-plan quote math."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from inventory.models import RatePlan, RatePlanPrice, RoomType, RoomTypeAvailability
from inventory.services import quote_availability
from properties.models import Property


@pytest.fixture
def property_obj(db):
    return Property.objects.create(
        name="Quote Hotel",
        location="Crete",
        address="2 Beach Rd",
        city="Chania",
        postal_code="73100",
        country="GR",
    )


@pytest.fixture
def catalog(db, property_obj):
    rt = RoomType.objects.create(
        property=property_obj,
        code="DBL",
        name="Double",
        capacity=2,
        base_occupancy=2,
        max_occupancy=3,
        base_price=Decimal("80.00"),
    )
    rp = RatePlan.objects.create(
        property=property_obj,
        code="BB",
        name="Bed & Breakfast",
        meal_plan="BB",
        is_refundable=True,
    )
    rp.room_types.add(rt)

    check_in = date.today() + timedelta(days=40)
    check_out = check_in + timedelta(days=2)
    for night in (check_in, check_in + timedelta(days=1)):
        RoomTypeAvailability.objects.create(
            room_type=rt,
            date=night,
            allotment=5,
            booked=1,
            min_stay=1,
            max_stay=0,
        )
        RatePlanPrice.objects.create(
            rate_plan=rp,
            room_type=rt,
            date=night,
            price_1=Decimal("90.00"),
            price_2=Decimal("100.00"),
            price_3=Decimal("120.00"),
        )
    return {
        "property": property_obj,
        "room_type": rt,
        "rate_plan": rp,
        "check_in": check_in,
        "check_out": check_out,
    }


@pytest.mark.integration
def test_quote_totals_occupancy_price(catalog):
    results = quote_availability(
        catalog["property"].id,
        catalog["check_in"],
        catalog["check_out"],
        adults=2,
        children=0,
    )
    assert len(results) == 1
    quote = results[0]
    assert quote["room_type_id"] == catalog["room_type"].id
    assert quote["rate_plan_id"] == catalog["rate_plan"].id
    assert quote["available_allotment"] == 4  # 5 - 1
    assert quote["restrictions_ok"] is True
    # 2 nights × price_2 (100)
    assert Decimal(quote["total"]) == Decimal("200.00")
    assert len(quote["nightly_prices"]) == 2


@pytest.mark.integration
def test_quote_respects_stop_sell(catalog):
    RoomTypeAvailability.objects.filter(
        room_type=catalog["room_type"], date=catalog["check_in"]
    ).update(stop_sell=True)

    results = quote_availability(
        catalog["property"].id,
        catalog["check_in"],
        catalog["check_out"],
        adults=2,
    )
    assert len(results) == 1
    assert results[0]["restrictions_ok"] is False


@pytest.mark.unit
def test_quote_empty_for_invalid_dates(catalog):
    results = quote_availability(
        catalog["property"].id,
        catalog["check_out"],
        catalog["check_in"],
        adults=1,
    )
    assert results == []


@pytest.mark.integration
def test_quote_skips_over_max_occupancy(catalog):
    results = quote_availability(
        catalog["property"].id,
        catalog["check_in"],
        catalog["check_out"],
        adults=4,  # max_occupancy=3
    )
    assert results == []
