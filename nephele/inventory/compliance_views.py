"""Greek compliance exports — ΣΑΕ / police guest registration sheet."""

from __future__ import annotations

import csv
import io
from datetime import datetime

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.api_permissions import IsHotelStaff
from room.models import Booking

_POLICE_CSV_FIELDS = [
    "booking_id",
    "confirmation",
    "property",
    "mhte_number",
    "guest_first_name",
    "guest_last_name",
    "guest_email",
    "nationality",
    "document_type",
    "document_number",
    "birth_date",
    "check_in",
    "check_out",
    "room_number",
    "registration_id",
]


def _police_sheet_queryset(property_id, date_from, date_to):
    qs = Booking.objects.filter(
        status__in=["confirmed", "checked_in", "checked_out"],
    ).select_related(
        "guest", "room", "room_type", "room__property", "room_type__property"
    )
    qs = qs.filter(room__property_id=property_id) | qs.filter(
        room_type__property_id=property_id, room__isnull=True
    )
    if date_from:
        qs = qs.filter(check_in_date__gte=date_from)
    if date_to:
        qs = qs.filter(check_in_date__lte=date_to)
    return qs.order_by("check_in_date")


def _property_for_booking(booking):
    if booking.room_id:
        return booking.room.property
    if booking.room_type_id:
        return booking.room_type.property
    return None


def _booking_to_police_row(booking):
    guest = booking.guest
    prop = _property_for_booking(booking)
    return {
        "booking_id": booking.id,
        "confirmation": f"NEPH-{booking.id}",
        "property": prop.name if prop else "",
        "mhte_number": getattr(prop, "mhte_number", "") if prop else "",
        "guest_first_name": getattr(guest, "first_name", "") if guest else "",
        "guest_last_name": getattr(guest, "last_name", "") if guest else "",
        "guest_email": getattr(guest, "email", "") if guest else "",
        "nationality": booking.guest_nationality,
        "document_type": booking.guest_document_type,
        "document_number": booking.guest_document_number,
        "birth_date": (
            booking.guest_birth_date.isoformat() if booking.guest_birth_date else ""
        ),
        "check_in": booking.check_in_date.isoformat(),
        "check_out": booking.check_out_date.isoformat(),
        "room_number": booking.room.room_number if booking.room_id else "",
        "registration_id": booking.guest_registration_id,
    }


def _police_csv_response(rows, property_id):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_POLICE_CSV_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    filename = f"police_sheet_{property_id}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsHotelStaff])
def police_sheet_export(request):
    """
    Export guest registration rows for a property/date window (ΣΑΕ-oriented CSV).

    Query: property_id, date_from, date_to (ISO). Defaults to arrivals today.
    """
    property_id = request.query_params.get("property_id")
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    if not property_id:
        return Response(
            {"error": "property_id required"}, status=status.HTTP_400_BAD_REQUEST
        )

    qs = _police_sheet_queryset(property_id, date_from, date_to)
    rows = [_booking_to_police_row(b) for b in qs]

    Booking.objects.filter(id__in=[r["booking_id"] for r in rows]).update(
        police_sheet_exported_at=timezone.now()
    )

    if request.query_params.get("format", "csv") == "json":
        return Response({"count": len(rows), "results": rows})
    return _police_csv_response(rows, property_id)
