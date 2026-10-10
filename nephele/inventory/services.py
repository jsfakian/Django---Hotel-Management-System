# nephele/inventory/services.py
"""
Single availability engine for Nephele HMS.

Centralizes room-level inventory math and room-type / rate-plan quoting.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple

ACTIVE_BOOKING_STATUSES = ("pending", "confirmed", "checked_in", "held")


def ensure_room_availability(room, on_date: date):
    """Get or create a RoomAvailability row for ``room`` on ``on_date``."""
    from inventory.models import RoomAvailability

    defaults = {
        "total_units": 1,
        "available_units": 1,
        "booked_units": 0,
        "base_price": getattr(room, "base_price", None),
    }
    avail, _ = RoomAvailability.objects.get_or_create(
        room=room,
        date=on_date,
        defaults=defaults,
    )
    return avail


def _daterange(check_in: date, check_out: date):
    current = check_in
    while current < check_out:
        yield current
        current += timedelta(days=1)


# Public alias used by booking engine / catalog views
daterange = _daterange


def physical_room_count(room_type) -> int:
    """Count sellable physical rooms linked to a room type."""
    return room_type.rooms.exclude(status="maintenance").count()


def ensure_room_type_availability(room_type, on_date: date, *, allotment: Optional[int] = None):
    """
    Get or create a RoomTypeAvailability row.
    When allotment is omitted, default to the physical-room count for the type.
    """
    from inventory.models import RoomTypeAvailability

    if allotment is None:
        allotment = physical_room_count(room_type)

    defaults = {
        "allotment": allotment,
        "booked": 0,
        "stop_sell": False,
        "closed": False,
        "min_stay": 1,
        "max_stay": 0,
        "cta": False,
        "ctd": False,
    }
    avail, created = RoomTypeAvailability.objects.get_or_create(
        room_type=room_type, date=on_date, defaults=defaults
    )
    # Backfill empty calendars that were created with allotment=0
    if (
        not created
        and avail.allotment == 0
        and not avail.stop_sell
        and not avail.closed
        and not getattr(avail, "staff_override", False)
    ):
        count = physical_room_count(room_type)
        if count > 0:
            avail.allotment = count
            avail.save(update_fields=["allotment", "updated_at"])
    return avail


def _effective_available(avail, booked_units: int, allow_overbook: bool = False) -> int:
    """Compute sellable units for a night."""
    base = avail.total_units - booked_units - avail.blocked_units
    if allow_overbook:
        return base + avail.overbooked_units
    return base


def recalculate_room_availability(room, check_in: date, check_out: date) -> None:
    """
    Recount booked units from overlapping active Bookings for each night
    in [check_in, check_out).
    """
    from room.models import Booking

    if not room or check_out <= check_in:
        return

    for on_date in _daterange(check_in, check_out):
        avail = ensure_room_availability(room, on_date)
        booked = Booking.objects.filter(
            room=room,
            status__in=ACTIVE_BOOKING_STATUSES,
            check_in_date__lte=on_date,
            check_out_date__gt=on_date,
        ).count()
        avail.booked_units = booked
        avail.available_units = max(
            0,
            avail.total_units
            - avail.booked_units
            - avail.blocked_units
            - avail.overbooked_units,
        )
        avail.save(
            update_fields=[
                "booked_units",
                "available_units",
                "updated_at",
            ]
        )


def apply_booking_to_inventory(booking) -> None:
    """Apply (or refresh) inventory impact for an active booking."""
    if not booking or not getattr(booking, "room_id", None):
        return
    if booking.status not in ACTIVE_BOOKING_STATUSES:
        release_booking_from_inventory(booking)
        return
    recalculate_room_availability(
        booking.room, booking.check_in_date, booking.check_out_date
    )


def release_booking_from_inventory(booking) -> None:
    """Refresh inventory after a booking is cancelled/deleted/inactive."""
    if not booking or not getattr(booking, "room_id", None):
        return
    recalculate_room_availability(
        booking.room, booking.check_in_date, booking.check_out_date
    )


def is_room_available(
    room,
    check_in: date,
    check_out: date,
    allow_overbook: bool = False,
) -> bool:
    """
    Return True if ``room`` can be sold for [check_in, check_out).

    Combines RoomAvailability (allotment / blocks) with live Booking counts.
    """
    from room.models import Booking

    if not room or check_out <= check_in:
        return False

    prop = getattr(room, "property", None)
    if prop is not None and getattr(prop, "allow_overbooking", False):
        allow_overbook = True

    for on_date in _daterange(check_in, check_out):
        avail = ensure_room_availability(room, on_date)
        booked = Booking.objects.filter(
            room=room,
            status__in=ACTIVE_BOOKING_STATUSES,
            check_in_date__lte=on_date,
            check_out_date__gt=on_date,
        ).count()
        if _effective_available(avail, booked, allow_overbook=allow_overbook) <= 0:
            return False
    return True


def _occupancy_price(rate_price, occupancy: int) -> Optional[Decimal]:
    """Resolve nightly price for an occupancy from RatePlanPrice."""
    occ = max(1, min(int(occupancy), 4))
    if rate_price.price_by_occupancy:
        raw = rate_price.price_by_occupancy.get(str(occ))
        if raw is None:
            raw = rate_price.price_by_occupancy.get(occ)
        if raw is not None:
            return Decimal(str(raw))
    price = getattr(rate_price, f"price_{occ}", None)
    if price is not None:
        return price
    return rate_price.price_1


def _night_restriction_reasons(row, on_date: date, check_in: date, nights: int) -> List[str]:
    reasons: List[str] = []
    if row.stop_sell or row.closed:
        reasons.append(f"closed:{on_date}")
    if on_date == check_in and row.cta:
        reasons.append(f"cta:{on_date}")
    if row.min_stay and nights < row.min_stay:
        reasons.append(f"min_stay:{on_date}")
    if row.max_stay and nights > row.max_stay:
        reasons.append(f"max_stay:{on_date}")
    return reasons


def _ctd_reasons(by_date: Dict, check_out: date) -> List[str]:
    # CTD is evaluated on the departure date row if present
    ctd_row = by_date.get(check_out) or by_date.get(check_out - timedelta(days=1))
    if ctd_row is None or not getattr(ctd_row, "ctd", False):
        return []
    # Closed to departure on the last night of stay
    last_night = by_date.get(check_out - timedelta(days=1))
    if last_night is not None and last_night.ctd:
        return [f"ctd:{last_night.date}"]
    return []


def _restrictions_ok(
    night_rows: Sequence,
    check_in: date,
    check_out: date,
) -> Tuple[bool, List[str]]:
    """Evaluate stay restrictions across nights."""
    nights = (check_out - check_in).days
    reasons: List[str] = []
    by_date = {row.date: row for row in night_rows}

    for on_date in _daterange(check_in, check_out):
        row = by_date.get(on_date)
        if row is None:
            reasons.append(f"missing_availability:{on_date}")
            continue
        reasons.extend(_night_restriction_reasons(row, on_date, check_in, nights))

    reasons.extend(_ctd_reasons(by_date, check_out))
    return (len(reasons) == 0, reasons)


def _allotment_for_stay(room_type, night_rows, check_in, check_out, ok: bool):
    expected_nights = (check_out - check_in).days
    if night_rows and len(night_rows) >= expected_nights:
        open_rows = [r for r in night_rows if not r.stop_sell and not r.closed]
        available_allotment = (
            min(max(0, row.allotment - row.booked) for row in open_rows)
            if open_rows
            else 0
        )
        return available_allotment, ok
    available_allotment = physical_room_count(room_type)
    return available_allotment, available_allotment > 0 and ok


def _nightly_prices_for_plan(rate_plan, room_type, check_in, check_out, occupancy):
    from inventory.models import RatePlanPrice

    nightly_prices: List[Dict[str, Any]] = []
    total = Decimal("0.00")
    missing_price = False

    for on_date in _daterange(check_in, check_out):
        price_row = RatePlanPrice.objects.filter(
            rate_plan=rate_plan,
            room_type=room_type,
            date=on_date,
        ).first()
        if price_row is None:
            missing_price = True
            nightly_prices.append({"date": on_date.isoformat(), "price": None})
            continue
        price = _occupancy_price(price_row, occupancy)
        if price is None:
            missing_price = True
            nightly_prices.append({"date": on_date.isoformat(), "price": None})
            continue
        nightly_prices.append({"date": on_date.isoformat(), "price": str(price)})
        total += price

    if missing_price:
        nights = (check_out - check_in).days
        total = room_type.base_price * nights
        nightly_prices = [
            {"date": d.isoformat(), "price": str(room_type.base_price)}
            for d in _daterange(check_in, check_out)
        ]
    return nightly_prices, total


def _quote_product_dict(
    room_type, rate_plan, nightly_prices, total, available_allotment, ok
):
    return {
        "room_type_id": room_type.id,
        "rate_plan_id": rate_plan.id,
        "room_type": {
            "id": room_type.id,
            "code": room_type.code,
            "name": room_type.name,
            "capacity": room_type.capacity,
            "max_occupancy": room_type.max_occupancy,
        },
        "rate_plan": {
            "id": rate_plan.id,
            "code": rate_plan.code,
            "name": rate_plan.name,
            "meal_plan": rate_plan.meal_plan,
            "is_refundable": rate_plan.is_refundable,
        },
        "nightly_prices": nightly_prices,
        "total": str(total),
        "available_allotment": available_allotment,
        "restrictions_ok": bool(ok and available_allotment > 0),
    }


def _quotes_for_room_type(
    room_type, property_id, check_in, check_out, occupancy
) -> List[Dict[str, Any]]:
    from inventory.models import RatePlan, RoomTypeAvailability

    for on_date in _daterange(check_in, check_out):
        ensure_room_type_availability(room_type, on_date)

    night_rows = list(
        RoomTypeAvailability.objects.filter(
            room_type=room_type,
            date__gte=check_in,
            date__lt=check_out,
        )
    )
    ok, _reasons = _restrictions_ok(night_rows, check_in, check_out)
    available_allotment, ok = _allotment_for_stay(
        room_type, night_rows, check_in, check_out, ok
    )

    rate_plans = RatePlan.objects.filter(
        property_id=property_id,
        is_active=True,
        room_types=room_type,
    ).distinct()

    results: List[Dict[str, Any]] = []
    for rate_plan in rate_plans:
        nightly_prices, total = _nightly_prices_for_plan(
            rate_plan, room_type, check_in, check_out, occupancy
        )
        results.append(
            _quote_product_dict(
                room_type, rate_plan, nightly_prices, total, available_allotment, ok
            )
        )
    return results


def quote_availability(
    property_id: int,
    check_in: date,
    check_out: date,
    adults: int,
    children: int = 0,
    children_ages: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """
    Build sellable room-type × rate-plan quotes for a stay.

    Returns list of dicts:
      room_type, rate_plan, nightly_prices, total, available_allotment, restrictions_ok
    """
    from inventory.models import RoomType

    del children_ages  # reserved for future child-rate rules

    if check_out <= check_in or adults < 1:
        return []

    occupancy = adults + max(0, children)
    results: List[Dict[str, Any]] = []

    room_types = RoomType.objects.filter(
        property_id=property_id, is_active=True
    ).prefetch_related("rate_plans")

    for room_type in room_types:
        if occupancy > room_type.max_occupancy:
            continue
        results.extend(
            _quotes_for_room_type(
                room_type, property_id, check_in, check_out, occupancy
            )
        )

    return results


def bulk_upsert_room_type_availability(
    room_type,
    rows: Sequence[Dict[str, Any]],
) -> List:
    """
    Upsert RoomTypeAvailability rows for a room type.

    Each row dict may include: date, allotment, booked, stop_sell, min_stay,
    max_stay, cta, ctd, closed, restrictions.
    """
    from inventory.models import RoomTypeAvailability

    updated = []
    for row in rows:
        on_date = row["date"]
        defaults = {
            key: row[key]
            for key in (
                "allotment",
                "booked",
                "stop_sell",
                "min_stay",
                "max_stay",
                "cta",
                "ctd",
                "closed",
                "restrictions",
            )
            if key in row
        }
        obj, _ = RoomTypeAvailability.objects.update_or_create(
            room_type=room_type,
            date=on_date,
            defaults=defaults,
        )
        updated.append(obj)
    return updated
