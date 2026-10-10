"""Police sheet / ΣΑΕ export smoke test."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from accounts.models import Guest
from properties.models import Property
from room.models import Booking, Room


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
    )
    user = User.objects.create_user("staff1", password="x")
    Group.objects.get_or_create(name="admin")
    user.groups.add(Group.objects.get(name="admin"))
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get(
        "/api/v1/compliance/police-sheet/",
        {"property_id": prop.id, "date_from": check_in.isoformat()},
    )
    assert resp.status_code == 200
    assert "text/csv" in resp["Content-Type"]
    assert b"Nikos" in resp.content
