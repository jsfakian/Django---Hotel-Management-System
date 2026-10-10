"""Build structured invoice line items (room, VAT, climate fee, extras)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List


def booking_invoice_lines(booking) -> List[Dict[str, Any]]:
    """Return line items suitable for invoices / MyData / guest receipts."""
    nights = max(1, (booking.check_out_date - booking.check_in_date).days)
    room_subtotal = Decimal(str(booking.base_price or 0))
    vat = Decimal(str(booking.vat_amount or 0))
    climate = Decimal(str(booking.climate_resilience_fee or 0))
    total = Decimal(str(booking.actual_price or room_subtotal + vat + climate))

    room_label = (
        booking.room_type.name
        if getattr(booking, "room_type_id", None)
        else (booking.room.room_number if booking.room_id else "Room")
    )
    lines = [
        {
            "code": "ROOM",
            "description": f"{room_label} × {nights} night(s)",
            "quantity": nights,
            "unit_amount": (room_subtotal / nights).quantize(Decimal("0.01")),
            "amount": room_subtotal,
            "tax_category": "vat_reduced",
        },
        {
            "code": "VAT",
            "description": "VAT / ΦΠΑ",
            "quantity": 1,
            "unit_amount": vat,
            "amount": vat,
            "tax_category": "vat",
        },
        {
            "code": "CLIMATE",
            "description": "Climate resilience fee / Τέλος κλιματικής ανθεκτικότητας",
            "quantity": nights,
            "unit_amount": (climate / nights).quantize(Decimal("0.01")) if nights else climate,
            "amount": climate,
            "tax_category": "fee",
        },
    ]
    extras_total = total - room_subtotal - vat - climate
    if extras_total > 0:
        lines.append(
            {
                "code": "EXTRAS",
                "description": "Extras / Επιπλέον χρεώσεις",
                "quantity": 1,
                "unit_amount": extras_total,
                "amount": extras_total,
                "tax_category": "other",
            }
        )
    return lines


def attach_lines_to_invoice_description(invoice, booking) -> str:
    lines = booking_invoice_lines(booking)
    parts = [f"{l['description']}: €{l['amount']}" for l in lines]
    return "; ".join(parts)
