"""Public booking engine: quote → hold → confirm."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from inventory.services import (
    daterange,
    ensure_room_type_availability,
    quote_availability,
)


class BookingEngineError(Exception):
    """Base booking-engine error."""


class NoAllotmentError(BookingEngineError):
    """Requested product has no remaining allotment."""


class HoldExpiredError(BookingEngineError):
    """Hold TTL elapsed."""


class HoldNotFoundError(BookingEngineError):
    """Hold booking missing or not in held state."""


def compute_taxes(subtotal: Decimal, nights: int) -> dict:
    vat_rate = Decimal(str(getattr(settings, "DEFAULT_VAT_RATE", "0.13")))
    climate_per_night = Decimal(str(getattr(settings, "CLIMATE_FEE_PER_NIGHT", "1.50")))
    vat_amount = (subtotal * vat_rate).quantize(Decimal("0.01"))
    climate = (climate_per_night * Decimal(nights)).quantize(Decimal("0.01"))
    return {
        "vat_rate": vat_rate,
        "vat_amount": vat_amount,
        "climate_resilience_fee": climate,
        "total_with_taxes": subtotal + vat_amount + climate,
    }


def _smart_rate_hint(room_type_id: int, check_in) -> dict | None:
    """Optional ML recommended nightly from pricing history (non-blocking)."""
    try:
        from bookings.models import PricingHistory
        from room.models import Room

        room = Room.objects.filter(room_type_fk_id=room_type_id).first()
        if not room:
            return None
        row = (
            PricingHistory.objects.filter(room=room, date__lte=check_in)
            .order_by("-date")
            .first()
        )
        if not row:
            return None
        price = getattr(row, "ai_recommended_price", None) or getattr(
            row, "dynamic_price", None
        )
        if price is None:
            return None
        return {
            "smart_rate": str(price),
            "smart_rate_label": "Smart rate",
            "source": "ml_pricing",
        }
    except Exception:
        return None


def quote(property_id, check_in, check_out, adults=1, children=0, children_ages=None):
    """Public quote with tax line items attached."""
    products = quote_availability(
        property_id,
        check_in,
        check_out,
        adults=adults,
        children=children,
        children_ages=children_ages,
    )
    nights = (check_out - check_in).days
    enriched = []
    for p in products:
        if not p.get("restrictions_ok", True):
            continue
        subtotal = Decimal(str(p["total"]))
        taxes = compute_taxes(subtotal, nights)
        item = {
            **p,
            "room_type_id": p["room_type"]["id"],
            "rate_plan_id": p["rate_plan"]["id"],
            "vat_amount": str(taxes["vat_amount"]),
            "climate_resilience_fee": str(taxes["climate_resilience_fee"]),
            "total_with_taxes": str(taxes["total_with_taxes"]),
            "currency": "EUR",
        }
        hint = _smart_rate_hint(item["room_type_id"], check_in)
        if hint:
            item.update(hint)
        enriched.append(item)
    return enriched


@transaction.atomic
def create_hold(
    *,
    property_id: int,
    room_type_id: int,
    rate_plan_id: int,
    check_in,
    check_out,
    adults: int = 1,
    children: int = 0,
    children_ages=None,
    guest_email: str = "",
    guest_name: str = "",
    guest_first_name: str = "",
    guest_last_name: str = "",
    guest_phone: str = "",
    ttl_minutes: int = 15,
    special_requests: str = "",
    payment_mode: str = "deposit",
    deposit_percent=None,
):
    from accounts.models import Guest
    from inventory.models import RatePlan, RoomType, RoomTypeAvailability
    from room.models import Booking

    if not guest_email:
        raise BookingEngineError("guest_email is required")
    if check_out <= check_in:
        raise BookingEngineError("check_out must be after check_in")

    if guest_name and not guest_first_name:
        parts = guest_name.strip().split(None, 1)
        guest_first_name = parts[0]
        guest_last_name = parts[1] if len(parts) > 1 else guest_last_name

    products = quote(
        property_id, check_in, check_out, adults=adults, children=children
    )
    match = next(
        (
            q
            for q in products
            if q["room_type_id"] == room_type_id and q["rate_plan_id"] == rate_plan_id
        ),
        None,
    )
    if not match:
        raise NoAllotmentError("Selected room type / rate plan not available for dates")

    room_type = RoomType.objects.select_for_update().get(
        pk=room_type_id, property_id=property_id
    )
    rate_plan = RatePlan.objects.get(pk=rate_plan_id, property_id=property_id)

    nights = (check_out - check_in).days
    for night in daterange(check_in, check_out):
        avail = (
            RoomTypeAvailability.objects.select_for_update()
            .filter(room_type=room_type, date=night)
            .first()
        )
        if avail is None:
            avail = ensure_room_type_availability(
                room_type, night, allotment=max(1, room_type.rooms.count())
            )
            avail = RoomTypeAvailability.objects.select_for_update().get(pk=avail.pk)
        if avail.stop_sell or avail.closed or avail.available_units <= 0:
            raise NoAllotmentError(f"No allotment for {night}")
        avail.booked += 1
        avail.save(update_fields=["booked", "updated_at"])

    guest, _ = Guest.objects.get_or_create(
        email=guest_email,
        defaults={
            "first_name": guest_first_name or "Guest",
            "last_name": guest_last_name,
            "phone_number": guest_phone,
        },
    )

    subtotal = Decimal(str(match["total"]))
    taxes = compute_taxes(subtotal, nights)
    hold_expires = timezone.now() + timedelta(minutes=ttl_minutes)
    total = taxes["total_with_taxes"]
    pct = Decimal(str(deposit_percent if deposit_percent is not None else "30.00"))
    if payment_mode == "pay_at_hotel":
        deposit_due = Decimal("0.00")
    elif payment_mode == "full":
        deposit_due = total
    else:
        deposit_due = (total * pct / Decimal("100")).quantize(Decimal("0.01"))

    payment_note = (
        f"payment_mode={payment_mode}; deposit_due={deposit_due}; "
        f"balance_due={total - deposit_due}"
    )

    booking = Booking.objects.create(
        room=None,
        room_type=room_type,
        rate_plan=rate_plan,
        guest=guest,
        check_in_date=check_in,
        check_out_date=check_out,
        number_of_guests=adults + children,
        adults=adults,
        children=children,
        children_ages=children_ages or [],
        status="held",
        hold_expires_at=hold_expires,
        base_price=subtotal,
        actual_price=total,
        vat_amount=taxes["vat_amount"],
        climate_resilience_fee=taxes["climate_resilience_fee"],
        booking_source="booking_engine",
        special_requests=special_requests,
        notes=payment_note,
    )
    booking.deposit_due = deposit_due  # ephemeral attr for API response
    booking.payment_mode = payment_mode
    return booking


@transaction.atomic
def confirm_hold(
    booking_id: int,
    payment_ref: str | None = None,
    payment_mode: str | None = None,
):
    from room.models import Booking

    try:
        booking = Booking.objects.select_for_update().get(pk=booking_id)
    except Booking.DoesNotExist as exc:
        raise HoldNotFoundError("Hold not found") from exc

    if booking.status != "held":
        raise HoldNotFoundError(f"Booking {booking_id} is not held")
    if booking.hold_expires_at and booking.hold_expires_at < timezone.now():
        _release_room_type_allotment(booking)
        booking.status = "cancelled"
        booking.save(update_fields=["status", "updated_at"])
        raise HoldExpiredError("Hold expired")

    booking.status = "confirmed"
    booking.hold_expires_at = None
    extras = []
    if payment_mode:
        extras.append(f"confirmed_payment_mode={payment_mode}")
    if payment_ref:
        extras.append(f"Payment: {payment_ref}")
    if extras:
        booking.notes = ((booking.notes or "") + "\n" + "; ".join(extras)).strip()
    booking.save()

    try:
        from notifications.tasks import send_booking_confirmation

        send_booking_confirmation.delay(booking.id)
    except Exception:
        try:
            from notifications.tasks import send_channel_booking_alert

            send_channel_booking_alert.delay(
                booking_id=booking.id, channel_name="Booking Engine"
            )
        except Exception:
            pass
    return booking


@transaction.atomic
def cancel_hold(booking_id: int):
    """Cancel a held booking and restore room-type allotment."""
    from room.models import Booking

    try:
        booking = Booking.objects.select_for_update().get(pk=booking_id)
    except Booking.DoesNotExist as exc:
        raise HoldNotFoundError("Hold not found") from exc

    if booking.status != "held":
        raise BookingEngineError(f"Only held bookings can be cancelled via BE (status={booking.status})")

    _release_room_type_allotment(booking)
    booking.status = "cancelled"
    booking.hold_expires_at = None
    booking.save(update_fields=["status", "hold_expires_at", "updated_at"])
    return booking


@transaction.atomic
def expire_holds():
    from room.models import Booking

    now = timezone.now()
    expired = list(
        Booking.objects.select_for_update().filter(
            status="held", hold_expires_at__lt=now
        )
    )
    for booking in expired:
        _release_room_type_allotment(booking)
        booking.status = "cancelled"
        booking.save(update_fields=["status", "updated_at"])
    return len(expired)


def _release_room_type_allotment(booking):
    if not booking.room_type_id:
        return
    from inventory.models import RoomTypeAvailability

    for night in daterange(booking.check_in_date, booking.check_out_date):
        avail = RoomTypeAvailability.objects.filter(
            room_type_id=booking.room_type_id, date=night
        ).first()
        if avail and avail.booked > 0:
            avail.booked -= 1
            avail.save(update_fields=["booked", "updated_at"])
