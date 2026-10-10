"""Police sheet / ΣΑΕ export smoke test."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from accounts.models import Guest
from properties.models import Property
from room.models import Booking, Room


def _staff_client(username="staff_compliance"):
    user = User.objects.create_user(username, password="x")
    Group.objects.get_or_create(name="admin")
    user.groups.add(Group.objects.get(name="admin"))
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.integration
@pytest.mark.django_db
def test_police_sheet_csv_export():
    prop = Property.objects.create(
        name="Compliance Hotel",
        location="Athens",
        address="1",
        city="Athens",
        postal_code="10000",
        country="GR",
        mhte_number="MHTE-123",
    )
    room = Room.objects.create(
        room_number="501",
        floor=5,
        room_type="double",
        capacity=2,
        number_of_beds=1,
        base_price=Decimal("90"),
        current_price=Decimal("90"),
        property=prop,
    )
    guest = Guest.objects.create(
        email="police@example.com", first_name="Nikos", last_name="Test"
    )
    check_in = date.today()
    Booking.objects.create(
        room=room,
        guest=guest,
        check_in_date=check_in,
        check_out_date=check_in + timedelta(days=1),
        number_of_guests=1,
        adults=1,
        base_price=Decimal("90"),
        actual_price=Decimal("100"),
        status="confirmed",
        guest_nationality="GR",
        guest_document_type="passport",
        guest_document_number="AB123",
        shima_stay_purpose="tourism",
        mhte_registry_number="MHTE-123",
    )
    client = _staff_client("staff_csv")
    resp = client.get(
        "/api/v1/compliance/police-sheet/",
        {"property_id": prop.id, "date_from": check_in.isoformat()},
    )
    assert resp.status_code == 200
    assert "text/csv" in resp["Content-Type"]
    assert b"Nikos" in resp.content


@pytest.mark.integration
@pytest.mark.django_db
def test_police_sheet_xml_and_guest_fallback():
    prop = Property.objects.create(
        name="XML Hotel",
        location="Crete",
        address="2",
        city="Chania",
        postal_code="73100",
        country="GR",
        mhte_number="MHTE-999",
    )
    room = Room.objects.create(
        room_number="202",
        floor=2,
        room_type="double",
        capacity=2,
        number_of_beds=1,
        base_price=Decimal("80"),
        current_price=Decimal("80"),
        property=prop,
    )
    guest = Guest.objects.create(
        email="xmlguest@example.com",
        first_name="Maria",
        last_name="Papadopoulos",
        nationality="GR",
        document_type="id_card",
        document_number="ΑΕ123456",
        birth_date=date(1990, 5, 1),
    )
    check_in = date.today()
    Booking.objects.create(
        room=room,
        guest=guest,
        check_in_date=check_in,
        check_out_date=check_in + timedelta(days=2),
        number_of_guests=1,
        adults=1,
        base_price=Decimal("160"),
        actual_price=Decimal("180"),
        status="confirmed",
        # booking identity left empty → sync from Guest
    )
    client = _staff_client("staff_xml")
    resp = client.get(
        "/api/v1/compliance/police-sheet/",
        {
            "property_id": prop.id,
            "date_from": check_in.isoformat(),
            "format": "xml",
        },
    )
    assert resp.status_code == 200
    assert "xml" in resp["Content-Type"]
    body = resp.content.decode("utf-8")
    assert "<PoliceSheet" in body
    assert "Maria" in body
    assert "ΑΕ123456" in body
    assert "id_card" in body

