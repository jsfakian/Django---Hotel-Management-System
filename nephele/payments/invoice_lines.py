# nephele/payments/invoice_lines.py
"""Build structured invoice line items (room, VAT, climate fee, extras)."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any, Dict, List

from django.utils.translation import gettext as _


def _room_label(booking) -> str:
    if getattr(booking, "room_type_id", None):
        return booking.room_type.name
    if getattr(booking, "room_id", None):
        return booking.room.room_number
    return str(_("Room"))


def _serialize_line(line: Dict[str, Any]) -> Dict[str, Any]:
    """JSON-safe copy (Decimal → str)."""
    out = dict(line)
    for key in ("unit_amount", "amount"):
        if key in out and isinstance(out[key], Decimal):
            out[key] = str(out[key])
    return out


def booking_invoice_lines(booking) -> List[Dict[str, Any]]:
    """Return line items suitable for invoices / MyData / guest receipts."""
    nights = max(1, (booking.check_out_date - booking.check_in_date).days)
    room_subtotal = Decimal(str(booking.base_price or 0))
    vat = Decimal(str(booking.vat_amount or 0))
    climate = Decimal(str(booking.climate_resilience_fee or 0))
    total = Decimal(str(booking.actual_price or room_subtotal + vat + climate))

    room_label = _room_label(booking)
    unit_room = (room_subtotal / nights).quantize(Decimal("0.01"))
    climate_unit = (
        (climate / nights).quantize(Decimal("0.01")) if nights else climate
    )
    lines = [
        {
            "code": "ROOM",
            "description": _("%(room)s × %(nights)s night(s)")
            % {"room": room_label, "nights": nights},
            "quantity": nights,
            "unit_amount": unit_room,
            "amount": room_subtotal,
            "tax_category": "vat_reduced",
        },
        {
            "code": "VAT",
            "description": str(_("VAT")),
            "quantity": 1,
            "unit_amount": vat,
            "amount": vat,
            "tax_category": "vat",
        },
        {
            "code": "CLIMATE",
            "description": str(_("Climate resilience fee")),
            "quantity": nights,
            "unit_amount": climate_unit,
            "amount": climate,
            "tax_category": "fee",
        },
    ]
    extras_total = total - room_subtotal - vat - climate
    if extras_total > 0:
        lines.append(
            {
                "code": "EXTRAS",
                "description": str(_("Extras")),
                "quantity": 1,
                "unit_amount": extras_total,
                "amount": extras_total,
                "tax_category": "other",
            }
        )
    return lines


def lines_as_jsonable(lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [_serialize_line(l) for l in lines]


def attach_lines_to_invoice_description(invoice, booking) -> str:
    lines = booking_invoice_lines(booking)
    parts = [f"{l['description']}: €{l['amount']}" for l in lines]
    return "; ".join(parts)


def apply_invoice_lines(invoice, booking) -> List[Dict[str, Any]]:
    """Set description + line_items (and notes JSON fallback) on invoice."""
    lines = booking_invoice_lines(booking)
    invoice.description = attach_lines_to_invoice_description(invoice, booking)
    jsonable = lines_as_jsonable(lines)
    if hasattr(invoice, "line_items"):
        invoice.line_items = jsonable
    note_blob = json.dumps({"line_items": jsonable}, ensure_ascii=False)
    existing = (invoice.notes or "").strip()
    # Avoid duplicating the JSON blob on repeated saves
    if "line_items" in existing:
        invoice.notes = existing
    else:
        invoice.notes = f"{existing}\n{note_blob}".strip() if existing else note_blob
    return lines


def ensure_invoice_lines(invoice, booking=None, *, force: bool = False) -> List[Dict[str, Any]]:
    """
    Apply structured lines when invoice has a booking.

    Shared by checkout signals, InvoiceForm.save, and Invoice post_save.
    Skips when line_items already populated unless force=True.
    """
    booking = booking or getattr(invoice, "booking", None)
    if booking is None:
        return list(getattr(invoice, "line_items", None) or [])
    existing = getattr(invoice, "line_items", None) or []
    if existing and not force:
        return list(existing)
    return apply_invoice_lines(invoice, booking)
