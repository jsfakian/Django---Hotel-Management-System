# nephele/inventory/compliance_views.py
"""Greek compliance exports — ΣΑΕ / police guest registration sheet."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework.response import Response
from rest_framework import status

from accounts.api_permissions import IsHotelStaff
from room.models import Booking


class _CSVRenderer(BaseRenderer):
    """Allow ?format=csv without DRF Http404 during content negotiation."""

    media_type = "text/csv"
    format = "csv"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""
        if isinstance(data, bytes):
            return data
        return str(data).encode(self.charset)


class _XMLRenderer(BaseRenderer):
    """Allow ?format=xml without DRF Http404 during content negotiation."""

    media_type = "application/xml"
    format = "xml"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""
        if isinstance(data, bytes):
            return data
        return str(data).encode(self.charset)

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
    "shima_stay_purpose",
    "mhte_registry_number",
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


def _guest_attr(guest, name, default=""):
    if not guest:
        return default
    return getattr(guest, name, None) or default


def _coalesce_identity(booking_value, guest_value):
    """Prefer booking police fields; fall back to Guest profile."""
    if booking_value not in (None, ""):
        return booking_value
    return guest_value if guest_value not in (None, "") else ""


def _booking_to_police_row(booking):
    guest = booking.guest
    prop = _property_for_booking(booking)
    nationality = _coalesce_identity(
        booking.guest_nationality, _guest_attr(guest, "nationality")
    )
    document_type = _coalesce_identity(
        booking.guest_document_type, _guest_attr(guest, "document_type")
    )
    document_number = _coalesce_identity(
        booking.guest_document_number, _guest_attr(guest, "document_number")
    )
    birth = booking.guest_birth_date or _guest_attr(guest, "birth_date", None)
    mhte = getattr(booking, "mhte_registry_number", "") or (
        getattr(prop, "mhte_number", "") if prop else ""
    )
    return {
        "booking_id": booking.id,
        "confirmation": f"NEPH-{booking.id}",
        "property": prop.name if prop else "",
        "mhte_number": getattr(prop, "mhte_number", "") if prop else "",
        "guest_first_name": _guest_attr(guest, "first_name"),
        "guest_last_name": _guest_attr(guest, "last_name"),
        "guest_email": _guest_attr(guest, "email"),
        "nationality": nationality,
        "document_type": document_type,
        "document_number": document_number,
        "birth_date": birth.isoformat() if birth else "",
        "check_in": booking.check_in_date.isoformat(),
        "check_out": booking.check_out_date.isoformat(),
        "room_number": booking.room.room_number if booking.room_id else "",
        "registration_id": booking.guest_registration_id,
        "shima_stay_purpose": getattr(booking, "shima_stay_purpose", "") or "",
        "mhte_registry_number": mhte,
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


def _police_xml_response(rows, property_id):
    """Ministry-friendly simple XML: <PoliceSheet><Guest>...</Guest></PoliceSheet>."""
    root = Element("PoliceSheet")
    root.set("property_id", str(property_id))
    root.set("exported_at", timezone.now().isoformat())
    for row in rows:
        guest_el = SubElement(root, "Guest")
        for key in _POLICE_CSV_FIELDS:
            child = SubElement(guest_el, key)
            child.text = str(row.get(key, "") or "")
    xml_bytes = tostring(root, encoding="utf-8", xml_declaration=True)
    filename = f"police_sheet_{property_id}_{datetime.utcnow().strftime('%Y%m%d')}.xml"
    resp = HttpResponse(xml_bytes, content_type="application/xml; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@api_view(["GET"])
@renderer_classes([JSONRenderer, _CSVRenderer, _XMLRenderer])
@permission_classes([IsAuthenticated, IsHotelStaff])
def police_sheet_export(request):
    """
    Export guest registration rows for a property/date window (ΣΑΕ-oriented).

    Query: property_id, date_from, date_to (ISO), format=csv|json|xml.
    Defaults to arrivals today; format defaults to csv.
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

    fmt = (request.query_params.get("format") or "csv").lower()
    if fmt == "json":
        return Response({"count": len(rows), "results": rows})
    if fmt == "xml":
        return _police_xml_response(rows, property_id)
    return _police_csv_response(rows, property_id)
