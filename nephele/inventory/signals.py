# nephele/inventory/signals.py
"""Keep RoomAvailability in sync when Bookings change; fan-out to channels."""

from __future__ import annotations

import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from inventory.services import (
    ACTIVE_BOOKING_STATUSES,
    apply_booking_to_inventory,
    recalculate_room_availability,
    release_booking_from_inventory,
)

logger = logging.getLogger(__name__)

_PREVIOUS_BOOKING_STATE = {}


def _property_id_for_booking(booking):
    if getattr(booking, "room_id", None) and booking.room_id:
        room = getattr(booking, "room", None)
        if room is not None and getattr(room, "property_id", None):
            return room.property_id
        try:
            from room.models import Room

            return Room.objects.filter(pk=booking.room_id).values_list(
                "property_id", flat=True
            ).first()
        except Exception:
            return None
    room_type = getattr(booking, "room_type", None)
    if room_type is not None:
        return getattr(room_type, "property_id", None)
    return None


def _trigger_channel_sync(property_id, date_from=None, date_to=None):
    if not property_id:
        return
    try:
        from channels.tasks import sync_availability_to_channels

        sync_availability_to_channels.delay(
            property_id=property_id,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
        )
    except Exception:
        logger.debug("Channel sync trigger skipped", exc_info=True)


@receiver(pre_save, sender="room.Booking")
def booking_pre_save_capture(sender, instance, **kwargs):
    """Capture prior dates/status/room so we can refresh old inventory slots."""
    if not instance.pk:
        _PREVIOUS_BOOKING_STATE.pop(id(instance), None)
        return
    try:
        previous = sender.objects.filter(pk=instance.pk).values(
            "status",
            "room_id",
            "check_in_date",
            "check_out_date",
        ).first()
    except Exception:
        previous = None
    if previous:
        _PREVIOUS_BOOKING_STATE[instance.pk] = previous


def _booking_slot_changed(previous, instance) -> bool:
    return (
        previous["room_id"] != instance.room_id
        or previous["check_in_date"] != instance.check_in_date
        or previous["check_out_date"] != instance.check_out_date
        or previous["status"] != instance.status
    )


def _refresh_previous_inventory(previous, instance):
    """Recalculate inventory for the prior room/dates when the booking moved."""
    if not previous or not previous.get("room_id"):
        return
    old_room_id = previous["room_id"]
    if not old_room_id or not _booking_slot_changed(previous, instance):
        return
    try:
        from room.models import Room

        old_room = Room.objects.filter(pk=old_room_id).first()
        if old_room:
            recalculate_room_availability(
                old_room,
                previous["check_in_date"],
                previous["check_out_date"],
            )
    except Exception:
        logger.exception("Failed to refresh previous booking inventory")


@receiver(post_save, sender="room.Booking")
def booking_post_save_inventory(sender, instance, created, **kwargs):
    previous = _PREVIOUS_BOOKING_STATE.pop(instance.pk, None) if instance.pk else None
    _refresh_previous_inventory(previous, instance)

    if instance.status in ACTIVE_BOOKING_STATUSES:
        apply_booking_to_inventory(instance)
    else:
        release_booking_from_inventory(instance)

    _trigger_channel_sync(
        _property_id_for_booking(instance),
        date_from=instance.check_in_date,
        date_to=instance.check_out_date,
    )


@receiver(post_delete, sender="room.Booking")
def booking_post_delete_inventory(sender, instance, **kwargs):
    release_booking_from_inventory(instance)
    _trigger_channel_sync(
        _property_id_for_booking(instance),
        date_from=getattr(instance, "check_in_date", None),
        date_to=getattr(instance, "check_out_date", None),
    )


@receiver(post_save, sender="room.Booking")
def booking_checkout_sets_housekeeping(sender, instance, **kwargs):
    """When a booking checks out, mark the physical room for cleaning."""
    previous = _PREVIOUS_BOOKING_STATE.get(instance.pk) if instance.pk else None
    # previous may already have been popped by inventory handler; use status transition
    if instance.status != "checked_out" or not instance.room_id:
        return
    try:
        from room.models import Room

        Room.objects.filter(pk=instance.room_id).exclude(status="cleaning").update(
            status="cleaning"
        )
    except Exception:
        logger.debug("Housekeeping status update skipped", exc_info=True)
