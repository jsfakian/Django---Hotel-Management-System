"""Public booking engine: quote → hold → confirm."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

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


def _hint_payload(price, source: str) -> dict:
    return {
        "smart_rate": str(price),
        "smart_rate_label": str(_("Smart rate")),
        "source": source,
    }


def _predict_smart_rate(room_type_id: int, check_in):
    """Try dynamic pricing model; return price or None (never raises)."""
    try:
        from bookings.models import PricingHistory
        from bookings.price_predictor import predict_price
        from room.models import Room

        room = Room.objects.filter(room_type_fk_id=room_type_id).first()
        row = None
        if room:
            row = (
                PricingHistory.objects.filter(room=room, date__lte=check_in)
                .order_by("-date")
                .first()
            )
        features = {
            "occupancy_rate": float(getattr(row, "occupancy_rate", None) or 0.5),
            "competitor_price": float(
                getattr(row, "competitor_price", None)
                or getattr(row, "dynamic_price", None)
                or 100
            ),
            "demand_index": float(getattr(row, "demand_index", None) or 1.0),
            "day_of_week": check_in.weekday() if hasattr(check_in, "weekday") else 0,
            "season": (check_in.month % 12) // 3 if hasattr(check_in, "month") else 0,
        }
        return predict_price(features)
    except Exception:
        return None


def _pricing_history_hint(room_type_id: int, check_in) -> dict | None:
    """Fallback smart rate from latest PricingHistory row."""
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
        return _hint_payload(price, "ml_pricing")
    except Exception:
        return None


def _smart_rate_hint(room_type_id: int, check_in) -> dict | None:
    """ML predictor when model available; else PricingHistory (non-blocking)."""
    predicted = _predict_smart_rate(room_type_id, check_in)
    if predicted is not None:
        return _hint_payload(predicted, "price_predictor")
    return _pricing_history_hint(room_type_id, check_in)


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


def _split_guest_name(guest_name, guest_first_name, guest_last_name):
    if guest_name and not guest_first_name:
        parts = guest_name.strip().split(None, 1)
        guest_first_name = parts[0]
        guest_last_name = parts[1] if len(parts) > 1 else guest_last_name
    return guest_first_name, guest_last_name


def _match_quote_product(products, room_type_id, rate_plan_id):
    match = next(
        (
            q
            for q in products
            if q["room_type_id"] == room_type_id and q["rate_plan_id"] == rate_plan_id
        ),
        None,
    )
    if not match:
        raise NoAllotmentError(
            str(_("Selected room type / rate plan not available for dates"))
        )
    return match


def _reserve_room_type_nights(room_type, check_in, check_out):
    from inventory.models import RoomTypeAvailability

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
            raise NoAllotmentError(
                str(_("No allotment for %(date)s")) % {"date": night}
            )
        avail.booked += 1
        avail.save(update_fields=["booked", "updated_at"])


def _deposit_due_amount(total, payment_mode, deposit_percent):
    pct = Decimal(str(deposit_percent if deposit_percent is not None else "30.00"))
    if payment_mode == "pay_at_hotel":
        return Decimal("0.00")
    if payment_mode == "full":
        return total
    return (total * pct / Decimal("100")).quantize(Decimal("0.01"))


def _get_or_create_hold_guest(
    guest_email, guest_first_name, guest_last_name, guest_phone
):
    from accounts.models import Guest

    guest, _ = Guest.objects.get_or_create(
        email=guest_email,
        defaults={
            "first_name": guest_first_name or "Guest",
            "last_name": guest_last_name,
            "phone_number": guest_phone,
        },
    )
    return guest


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
    from inventory.models import RatePlan, RoomType
    from room.models import Booking

    if not guest_email:
        raise BookingEngineError(str(_("guest_email is required")))
    if check_out <= check_in:
        raise BookingEngineError(str(_("check_out must be after check_in")))

    guest_first_name, guest_last_name = _split_guest_name(
        guest_name, guest_first_name, guest_last_name
    )

    products = quote(
        property_id, check_in, check_out, adults=adults, children=children
    )
    match = _match_quote_product(products, room_type_id, rate_plan_id)

    room_type = RoomType.objects.select_for_update().get(
        pk=room_type_id, property_id=property_id
    )
    rate_plan = RatePlan.objects.get(pk=rate_plan_id, property_id=property_id)

    nights = (check_out - check_in).days
    _reserve_room_type_nights(room_type, check_in, check_out)

    guest = _get_or_create_hold_guest(
        guest_email, guest_first_name, guest_last_name, guest_phone
    )

    subtotal = Decimal(str(match["total"]))
    taxes = compute_taxes(subtotal, nights)
    hold_expires = timezone.now() + timedelta(minutes=ttl_minutes)
    total = taxes["total_with_taxes"]
    deposit_due = _deposit_due_amount(total, payment_mode, deposit_percent)

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


def _append_confirm_notes(booking, payment_ref, payment_mode):
    extras = []
    if payment_mode:
        extras.append(f"confirmed_payment_mode={payment_mode}")
    if payment_ref:
        extras.append(f"Payment: {payment_ref}")
    if extras:
        booking.notes = ((booking.notes or "") + "\n" + "; ".join(extras)).strip()


def _notify_hold_confirmed(booking):
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


def _expire_stale_hold(booking):
    if not booking.hold_expires_at or booking.hold_expires_at >= timezone.now():
        return
    _release_room_type_allotment(booking)
    booking.status = "cancelled"
    booking.save(update_fields=["status", "updated_at"])
    raise HoldExpiredError(str(_("Hold expired")))


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
        raise HoldNotFoundError(str(_("Hold not found"))) from exc

    if booking.status != "held":
        raise HoldNotFoundError(
            str(_("Booking %(id)s is not held")) % {"id": booking_id}
        )
    _expire_stale_hold(booking)

    booking.status = "confirmed"
    booking.hold_expires_at = None
    _append_confirm_notes(booking, payment_ref, payment_mode)
    booking.save()
    _notify_hold_confirmed(booking)
    return booking


@transaction.atomic
def cancel_hold(booking_id: int):
    """Cancel a held booking and restore room-type allotment."""
    from room.models import Booking

    try:
        booking = Booking.objects.select_for_update().get(pk=booking_id)
    except Booking.DoesNotExist as exc:
        raise HoldNotFoundError(str(_("Hold not found"))) from exc

    if booking.status != "held":
        raise BookingEngineError(
            str(_("Only held bookings can be cancelled via BE (status=%(status)s)"))
            % {"status": booking.status}
        )

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


def _parse_payment_mode(notes: str | None) -> str:
    if not notes:
        return "deposit"
    for part in notes.replace("\n", ";").split(";"):
        part = part.strip()
        if part.startswith("payment_mode="):
            return part.split("=", 1)[1].strip() or "deposit"
    return "deposit"


def _parse_deposit_due(notes: str | None):
    if not notes:
        return None
    for part in notes.replace("\n", ";").split(";"):
        part = part.strip()
        if part.startswith("deposit_due="):
            try:
                return Decimal(part.split("=", 1)[1].strip())
            except Exception:
                return None
    return None


def _needs_online_payment(payment_mode: str | None) -> bool:
    return (payment_mode or "") in ("deposit", "full")


def gateway_checkout_for_booking(booking, payment_mode=None) -> dict:
    """
    Start gateway checkout for deposit/full modes.

    pay_at_hotel returns {}. Never raises — quote/confirm must stay resilient.
    """
    mode = payment_mode or getattr(booking, "payment_mode", None) or _parse_payment_mode(
        booking.notes
    )
    if not _needs_online_payment(mode):
        return {}
    amount = getattr(booking, "deposit_due", None)
    if amount is None:
        amount = _parse_deposit_due(booking.notes)
    if amount is None:
        amount = booking.actual_price
    if amount is None or Decimal(str(amount)) <= 0:
        return {}
    try:
        from payments.gateway import start_booking_checkout

        guest = getattr(booking, "guest", None)
        email = getattr(guest, "email", "") or ""
        return start_booking_checkout(
            amount=Decimal(str(amount)),
            booking_id=booking.id,
            customer_email=email,
            description=f"Booking {booking.id} ({mode})",
        )
    except Exception:
        return {}


def hold_booking_dict(booking) -> dict:
    """Canonical hold payload for create/modify API responses."""
    payment_mode = getattr(booking, "payment_mode", None) or _parse_payment_mode(
        booking.notes
    )
    deposit_due = getattr(booking, "deposit_due", None)
    if deposit_due is None:
        deposit_due = _parse_deposit_due(booking.notes)
    if deposit_due is None:
        deposit_due = booking.actual_price
    payload = {
        "booking_id": booking.id,
        "status": booking.status,
        "hold_expires_at": booking.hold_expires_at,
        "check_in": booking.check_in_date,
        "check_out": booking.check_out_date,
        "adults": booking.adults,
        "children": booking.children,
        "room_type_id": booking.room_type_id,
        "rate_plan_id": booking.rate_plan_id,
        "total": str(booking.actual_price),
        "vat_amount": str(booking.vat_amount or 0),
        "climate_resilience_fee": str(booking.climate_resilience_fee or 0),
        "payment_mode": payment_mode,
        "deposit_due": str(deposit_due),
        "notes": booking.notes,
    }
    checkout = gateway_checkout_for_booking(booking, payment_mode)
    if checkout:
        payload.update(checkout)
    return payload


def _modifiable_hold_or_raise(booking):
    if booking.status not in ("held", "pending"):
        raise BookingEngineError(
            str(_("Only held/pending bookings can be modified (status=%(status)s)"))
            % {"status": booking.status}
        )
    if booking.status == "held":
        _expire_stale_hold(booking)


def _kw_or_booking(kwargs, key, booking_value):
    value = kwargs.get(key)
    return booking_value if value is None else value


def _resolve_modify_params(booking, **kwargs):
    check_in = kwargs.get("check_in") or booking.check_in_date
    check_out = kwargs.get("check_out") or booking.check_out_date
    adults = _kw_or_booking(kwargs, "adults", booking.adults)
    children = _kw_or_booking(kwargs, "children", booking.children)
    room_type_id = kwargs.get("room_type_id") or booking.room_type_id
    rate_plan_id = kwargs.get("rate_plan_id") or booking.rate_plan_id
    payment_mode = kwargs.get("payment_mode") or _parse_payment_mode(booking.notes)
    if check_out <= check_in:
        raise BookingEngineError(str(_("check_out must be after check_in")))
    if not room_type_id or not rate_plan_id:
        raise BookingEngineError(
            str(_("room_type_id and rate_plan_id are required"))
        )
    return check_in, check_out, adults, children, room_type_id, rate_plan_id, payment_mode


def _apply_hold_repricing(
    booking, room_type, rate_plan, check_in, check_out, adults, children, payment_mode
):
    nights = (check_out - check_in).days
    products = quote(
        room_type.property_id, check_in, check_out, adults=adults, children=children
    )
    match = _match_quote_product(products, room_type.id, rate_plan.id)
    _reserve_room_type_nights(room_type, check_in, check_out)

    subtotal = Decimal(str(match["total"]))
    taxes = compute_taxes(subtotal, nights)
    total = taxes["total_with_taxes"]
    deposit_due = _deposit_due_amount(total, payment_mode, None)
    payment_note = (
        f"payment_mode={payment_mode}; deposit_due={deposit_due}; "
        f"balance_due={total - deposit_due}"
    )

    booking.room_type = room_type
    booking.rate_plan = rate_plan
    booking.check_in_date = check_in
    booking.check_out_date = check_out
    booking.adults = adults
    booking.children = children
    booking.number_of_guests = adults + children
    booking.base_price = subtotal
    booking.actual_price = total
    booking.vat_amount = taxes["vat_amount"]
    booking.climate_resilience_fee = taxes["climate_resilience_fee"]
    booking.notes = payment_note
    booking.save()
    booking.deposit_due = deposit_due
    booking.payment_mode = payment_mode
    return booking


@transaction.atomic
def modify_hold(
    booking_id: int,
    *,
    check_in=None,
    check_out=None,
    adults=None,
    children=None,
    room_type_id=None,
    rate_plan_id=None,
    payment_mode=None,
):
    """Re-quote and re-hold an existing held/pending booking with new params."""
    from inventory.models import RatePlan, RoomType
    from room.models import Booking

    try:
        booking = Booking.objects.select_for_update().get(pk=booking_id)
    except Booking.DoesNotExist as exc:
        raise HoldNotFoundError(str(_("Hold not found"))) from exc

    _modifiable_hold_or_raise(booking)
    (
        check_in,
        check_out,
        adults,
        children,
        room_type_id,
        rate_plan_id,
        payment_mode,
    ) = _resolve_modify_params(
        booking,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        children=children,
        room_type_id=room_type_id,
        rate_plan_id=rate_plan_id,
        payment_mode=payment_mode,
    )

    _release_room_type_allotment(booking)

    room_type = RoomType.objects.select_for_update().get(pk=room_type_id)
    rate_plan = RatePlan.objects.get(pk=rate_plan_id, property_id=room_type.property_id)

    booking = _apply_hold_repricing(
        booking,
        room_type,
        rate_plan,
        check_in,
        check_out,
        adults,
        children,
        payment_mode,
    )
    return hold_booking_dict(booking)
