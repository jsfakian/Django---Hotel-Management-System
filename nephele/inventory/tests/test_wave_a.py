"""Wave A hardening tests: allotment defaults, cancel hold, deposit modes."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from inventory.booking_engine import cancel_hold, create_hold, modify_hold, quote
from inventory.models import (
    RatePlan,
    RatePlanPrice,
    RoomType,
    RoomTypeAvailability,
    RoomTypeAvailabilityAudit,
)
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


@pytest.mark.unit
@pytest.mark.django_db
def test_modify_hold_changes_dates_and_allotment(catalog):
    booking = create_hold(
        property_id=catalog["property"].id,
        room_type_id=catalog["room_type"].id,
        rate_plan_id=catalog["rate_plan"].id,
        check_in=catalog["check_in"],
        check_out=catalog["check_out"],
        adults=2,
        guest_email="modify@example.com",
        guest_first_name="Mod",
        guest_last_name="Ify",
    )
    old_in = catalog["check_in"]
    new_in = old_in + timedelta(days=3)
    new_out = new_in + timedelta(days=2)
    for d in (new_in, new_in + timedelta(days=1)):
        RatePlanPrice.objects.get_or_create(
            rate_plan=catalog["rate_plan"],
            room_type=catalog["room_type"],
            date=d,
            defaults={"price_2": Decimal("100.00")},
        )

    payload = modify_hold(booking.id, check_in=new_in, check_out=new_out, adults=1)
    assert payload["booking_id"] == booking.id
    assert payload["status"] == "held"
    assert payload["check_in"] == new_in
    assert payload["check_out"] == new_out
    assert payload["adults"] == 1

    assert (
        RoomTypeAvailability.objects.get(
            room_type=catalog["room_type"], date=old_in
        ).booked
        == 0
    )
    assert (
        RoomTypeAvailability.objects.get(
            room_type=catalog["room_type"], date=new_in
        ).booked
        == 1
    )


@pytest.mark.unit
@pytest.mark.django_db
def test_modify_hold_api_endpoint(catalog):
    booking = create_hold(
        property_id=catalog["property"].id,
        room_type_id=catalog["room_type"].id,
        rate_plan_id=catalog["rate_plan"].id,
        check_in=catalog["check_in"],
        check_out=catalog["check_out"],
        adults=2,
        guest_email="api-modify@example.com",
        guest_first_name="Api",
        guest_last_name="Modify",
    )
    client = APIClient()
    url = f"/api/v1/booking-engine/holds/{booking.id}/modify/"
    resp = client.post(url, {"adults": 1, "payment_mode": "full"}, format="json")
    assert resp.status_code == 200
    assert resp.data["adults"] == 1
    assert resp.data["payment_mode"] == "full"


@pytest.mark.unit
@pytest.mark.django_db
def test_availability_patch_writes_audit(catalog):
    rt = catalog["room_type"]
    night = catalog["check_in"]
    ensure_room_type_availability(rt, night)
    staff = User.objects.create_superuser(
        username="front_desk", email="fd@example.com", password="x"
    )
    client = APIClient()
    client.force_authenticate(user=staff)
    url = f"/api/v1/room-types/{rt.id}/availability/"
    resp = client.patch(
        url,
        {
            "date_from": night.isoformat(),
            "date_to": (night + timedelta(days=1)).isoformat(),
            "allotment": 1,
            "staff_override": True,
        },
        format="json",
    )
    assert resp.status_code == 200
    audit = RoomTypeAvailabilityAudit.objects.get(room_type=rt, date=night)
    assert audit.new_allotment == 1
    assert audit.new_staff_override is True
    assert audit.changed_by_id == staff.id


@pytest.mark.unit
@pytest.mark.django_db
def test_availability_get_calendar_range(catalog):
    """GET /room-types/{id}/availability/ returns existing rows for the UI."""
    rt = catalog["room_type"]
    night = catalog["check_in"]
    next_night = night + timedelta(days=1)
    a0 = ensure_room_type_availability(rt, night)
    a0.allotment = 2
    a0.stop_sell = False
    a0.save(update_fields=["allotment", "stop_sell"])
    ensure_room_type_availability(rt, next_night)

    staff = User.objects.create_superuser(
        username="cal_get", email="cal@example.com", password="x"
    )
    client = APIClient()
    client.force_authenticate(user=staff)
    url = f"/api/v1/room-types/{rt.id}/availability/"
    resp = client.get(
        url,
        {
            "date_from": night.isoformat(),
            "date_to": (next_night + timedelta(days=1)).isoformat(),
        },
    )
    assert resp.status_code == 200
    assert isinstance(resp.data, list)
    assert len(resp.data) == 2
    row = next(r for r in resp.data if r["date"] == night.isoformat())
    assert row["allotment"] == 2
    assert row["room_type"] == rt.id
    assert "available_units" in row
    assert "booked" in row


@pytest.mark.unit
@pytest.mark.django_db
def test_availability_patch_days_list(catalog):
    """PATCH accepts per-day days[] payload from the calendar UI."""
    rt = catalog["room_type"]
    night = catalog["check_in"]
    next_night = night + timedelta(days=1)
    ensure_room_type_availability(rt, night)
    ensure_room_type_availability(rt, next_night)

    staff = User.objects.create_superuser(
        username="cal_patch", email="calp@example.com", password="x"
    )
    client = APIClient()
    client.force_authenticate(user=staff)
    url = f"/api/v1/room-types/{rt.id}/availability/"
    resp = client.patch(
        url,
        {
            "date_from": night.isoformat(),
            "date_to": (next_night + timedelta(days=1)).isoformat(),
            "days": [
                {
                    "date": night.isoformat(),
                    "allotment": 5,
                    "min_stay": 2,
                    "stop_sell": True,
                },
                {
                    "date": next_night.isoformat(),
                    "allotment": 3,
                    "min_stay": 1,
                    "stop_sell": False,
                },
            ],
        },
        format="json",
    )
    assert resp.status_code == 200
    assert len(resp.data) == 2
    a0 = RoomTypeAvailability.objects.get(room_type=rt, date=night)
    a1 = RoomTypeAvailability.objects.get(room_type=rt, date=next_night)
    assert a0.allotment == 5
    assert a0.min_stay == 2
    assert a0.stop_sell is True
    assert a1.allotment == 3
    assert a1.stop_sell is False


@pytest.mark.unit
@pytest.mark.django_db
def test_availability_audit_is_immutable(catalog):
    """Audit rows may be created once; update/delete must raise."""
    rt = catalog["room_type"]
    night = catalog["check_in"]
    audit = RoomTypeAvailabilityAudit.objects.create(
        room_type=rt,
        date=night,
        old_allotment=3,
        new_allotment=1,
        old_staff_override=False,
        new_staff_override=True,
        note="seed",
    )
    audit.note = "mutated"
    with pytest.raises(PermissionError):
        audit.save()
    with pytest.raises(PermissionError):
        audit.delete()
    assert RoomTypeAvailabilityAudit.objects.filter(pk=audit.pk).exists()


@pytest.mark.unit
@pytest.mark.django_db
def test_quote_includes_smart_rate_when_predictor_available(catalog, monkeypatch):
    """Thin regression: quote surfaces smart_rate/ml hint when predictor works."""
    monkeypatch.setattr(
        "inventory.booking_engine._predict_smart_rate",
        lambda room_type_id, check_in: Decimal("142.50"),
    )
    products = quote(
        catalog["property"].id,
        catalog["check_in"],
        catalog["check_out"],
        adults=2,
    )
    assert products
    assert products[0].get("smart_rate") == "142.50"
    assert products[0].get("source") == "price_predictor"
