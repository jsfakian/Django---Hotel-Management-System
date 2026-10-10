# nephele/channels/tasks.py
"""Celery tasks for channel integration — dispatch via connector registry."""

from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.db import models
from django.utils import timezone

from inventory.models import AvailabilitySyncLog, RoomAvailability
from room.models import Room

from .connectors import get_connector
from .models import Channel, ChannelBooking

logger = logging.getLogger(__name__)


def _room_availability_records(room, date_from, date_to):
    avail_records = RoomAvailability.objects.filter(room=room)
    if date_from and date_to:
        return avail_records.filter(date__gte=date_from, date__lt=date_to)
    from_date = (
        avail_records.aggregate(models.Min("date"))["date__min"]
        or timezone.now().date()
    )
    to_date = from_date + timedelta(days=30)
    return avail_records.filter(date__gte=from_date, date__lt=to_date)


def _legacy_push_room_availability(channel, channel_room_id, avail_records):
    for avail in avail_records:
        channel_payload = {
            "room_id": channel_room_id,
            "date": avail.date.isoformat(),
            "available": avail.available_units,
            "booked": avail.booked_units,
            "price": float(avail.dynamic_price)
            if avail.dynamic_price
            else float(avail.base_price or 0),
        }
        _sync_to_channel_api(channel, channel_payload)


def _legacy_sync_rooms(channel, date_from, date_to) -> int:
    from channels.mapping_utils import normalize_mapping_config

    rooms = Room.objects.filter(property=channel.property)
    mappings = normalize_mapping_config(channel.mapping_config)["room_type_mappings"]
    rooms_affected = 0
    for room in rooms:
        # Prefer room-type catalog key; fall back to physical room id (legacy).
        channel_room_id = None
        if room.room_type_fk_id:
            channel_room_id = mappings.get(str(room.room_type_fk_id))
        if not channel_room_id:
            channel_room_id = mappings.get(str(room.id))
        if not channel_room_id:
            logger.warning("No mapping for room %s in channel %s", room.id, channel)
            continue
        avail_records = _room_availability_records(room, date_from, date_to)
        _legacy_push_room_availability(channel, channel_room_id, avail_records)
        rooms_affected += 1
    return rooms_affected


def _mark_sync_log_failed(channel, exc):
    sync_log = AvailabilitySyncLog.objects.filter(
        channel=channel, sync_status="in_progress"
    ).first()
    if sync_log:
        sync_log.sync_status = "failed"
        sync_log.error_message = str(exc)
        sync_log.completed_at = timezone.now()
        sync_log.save()


def _parse_date(value):
    if value is None or value == "":
        return None
    if hasattr(value, "isoformat"):
        return value
    from datetime import datetime

    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _rooms_affected_from_result(result) -> int:
    rooms_affected = int(result.get("vevents") or 0)
    if not rooms_affected and result.get("prepared_rooms") is not None:
        rooms_affected = len(result.get("prepared_rooms") or [])
    return rooms_affected


def _finish_not_implemented_result(channel, sync_log, result, rooms_affected):
    from django.conf import settings

    stubs_ok = getattr(settings, "CHANNEL_SYNC_STUBS_OK", False)
    if stubs_ok:
        sync_log.sync_status = "success"
        sync_log.error_message = (
            f"Stub accepted (CHANNEL_SYNC_STUBS_OK): "
            f"{result.get('message', 'not_implemented')}"
        )
    else:
        sync_log.sync_status = "not_implemented"
        sync_log.error_message = result.get("message", "not_implemented")
        channel.last_error = result.get("message", "")
        channel.save(update_fields=["last_error", "updated_at"])
    sync_log.response_data = result
    sync_log.rooms_affected = rooms_affected
    sync_log.completed_at = timezone.now()
    sync_log.save()
    return result


def _maybe_push_rates(channel, connector, date_from, date_to, avail_result):
    """After availability sync, push rates when connector supports it / LIVE."""
    push_rates = getattr(connector, "push_rates", None)
    if not callable(push_rates):
        return avail_result
    from django.conf import settings

    # Booking.com: only when LIVE; other connectors may always attempt
    if channel.channel_name == "booking_com" and not getattr(
        settings, "BOOKING_COM_LIVE", False
    ):
        return avail_result
    try:
        rates = push_rates(channel, date_from=date_from, date_to=date_to)
    except Exception as exc:
        logger.warning("push_rates failed for channel %s: %s", channel.id, exc)
        return avail_result
    if not isinstance(avail_result, dict):
        return avail_result
    merged = dict(avail_result)
    merged["rates"] = rates
    if rates.get("status") == "ok":
        merged["rates_affected"] = rates.get("rates_affected") or len(
            rates.get("prepared_rates") or []
        )
    return merged


def _push_via_connector(channel, connector, date_from, date_to, sync_log):
    result = connector.push_availability(
        channel, date_from=date_from, date_to=date_to
    )
    rooms_affected = _rooms_affected_from_result(result)
    if result.get("status") == "not_implemented":
        return _finish_not_implemented_result(
            channel, sync_log, result, rooms_affected
        ), None
    if result.get("status") == "error":
        raise RuntimeError(result.get("message") or "connector error")
    result = _maybe_push_rates(channel, connector, date_from, date_to, result)
    return result, rooms_affected


def _finalize_zero_rooms(channel, sync_log, result):
    msg = (
        "No rooms synced — missing room mappings, empty availability, "
        "or connector returned zero affected units"
    )
    sync_log.sync_status = "not_implemented"
    sync_log.error_message = msg
    sync_log.rooms_affected = 0
    sync_log.response_data = result if isinstance(result, dict) else {}
    sync_log.completed_at = timezone.now()
    sync_log.save()
    channel.last_error = msg
    channel.save(update_fields=["last_error", "updated_at"])
    return {
        "status": "not_implemented",
        "message": msg,
        "rooms_affected": 0,
    }


def _finalize_success(channel, sync_log, result, rooms_affected):
    sync_log.sync_status = "success"
    sync_log.completed_at = timezone.now()
    sync_log.rooms_affected = rooms_affected
    sync_log.response_data = result if isinstance(result, dict) else {}
    sync_log.save()

    channel.last_sync_at = sync_log.completed_at
    channel.error_count = 0
    channel.last_error = ""
    channel.save()
    return result


def _handle_not_implemented_exc(channel, sync_log, exc):
    from django.conf import settings

    stubs_ok = getattr(settings, "CHANNEL_SYNC_STUBS_OK", False)
    if stubs_ok:
        sync_log.sync_status = "success"
        sync_log.error_message = f"Stub accepted (CHANNEL_SYNC_STUBS_OK): {exc}"
        sync_log.completed_at = timezone.now()
        sync_log.save()
        return {"status": "success", "detail": "stub_ok", "message": str(exc)}
    sync_log.sync_status = "not_implemented"
    sync_log.error_message = str(exc)
    sync_log.completed_at = timezone.now()
    sync_log.save()
    channel.last_error = str(exc)
    channel.save(update_fields=["last_error", "updated_at"])
    return {"status": "not_implemented", "message": str(exc)}


def _handle_sync_failure(self, channel, sync_log, channel_id, exc):
    logger.error("Error syncing to channel %s: %s", channel_id, exc)
    channel.error_count += 1
    channel.last_error = str(exc)
    channel.save()
    if self.request.retries < self.max_retries:
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)
    sync_log.sync_status = "failed"
    sync_log.error_message = str(exc)
    sync_log.completed_at = timezone.now()
    sync_log.save()
    return {"status": "failed", "message": str(exc)}


def _execute_channel_sync(channel, connector, date_from, date_to, sync_log):
    if connector is not None:
        early, rooms_affected = _push_via_connector(
            channel, connector, date_from, date_to, sync_log
        )
        if rooms_affected is None:
            return early
        result = early
    else:
        rooms_affected = _legacy_sync_rooms(channel, date_from, date_to)
        result = {
            "status": "ok",
            "channel": channel.channel_name,
            "rooms_affected": rooms_affected,
        }

    if rooms_affected == 0:
        return _finalize_zero_rooms(channel, sync_log, result)
    return _finalize_success(channel, sync_log, result, rooms_affected)


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def sync_availability_to_channel(
    self, channel_id, sync_type="full_sync", date_from=None, date_to=None
):
    """Synchronize availability to a channel via its connector when available."""
    try:
        channel = Channel.objects.get(id=channel_id)
    except Channel.DoesNotExist:
        logger.error("Channel %s not found", channel_id)
        return {"status": "error", "message": "channel_not_found"}

    if not channel.sync_enabled or not channel.is_active:
        logger.info("Channel %s sync is disabled", channel)
        return {"status": "skipped", "reason": "disabled"}

    date_from = _parse_date(date_from)
    date_to = _parse_date(date_to)
    connector = get_connector(channel.channel_name)

    # Persist log outside atomic so stub/failure statuses survive rollbacks
    sync_log = AvailabilitySyncLog.objects.create(
        property=channel.property,
        channel=channel,
        sync_type=sync_type,
        sync_status="in_progress",
        date_from=date_from,
        date_to=date_to,
    )

    try:
        return _execute_channel_sync(
            channel, connector, date_from, date_to, sync_log
        )
    except NotImplementedError as exc:
        return _handle_not_implemented_exc(channel, sync_log, exc)
    except Exception as exc:
        return _handle_sync_failure(self, channel, sync_log, channel_id, exc)


@shared_task
def sync_availability_to_channels(
    property_id, exclude_channel_id=None, room_ids=None, date_from=None, date_to=None
):
    """Sync availability to all active channels for a property."""
    del room_ids  # reserved for future per-room scoping
    try:
        channels = Channel.objects.filter(
            property_id=property_id, is_active=True, sync_enabled=True
        )
        if exclude_channel_id:
            channels = channels.exclude(id=exclude_channel_id)
        for channel in channels:
            sync_availability_to_channel.delay(
                channel_id=channel.id,
                sync_type="incremental_sync",
                date_from=date_from,
                date_to=date_to,
            )
    except Exception as e:
        logger.error(
            "Error syncing availability to channels for property %s: %s",
            property_id,
            e,
        )


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def pull_bookings_from_channel(self, channel_id):
    """Pull bookings for a single channel via its connector."""
    try:
        channel = Channel.objects.get(id=channel_id)
    except Channel.DoesNotExist:
        return {"status": "error", "message": "channel_not_found"}

    if not channel.is_active or not channel.accept_bookings:
        return {"status": "skipped", "reason": "inactive_or_not_accepting"}

    connector = get_connector(channel.channel_name)
    if connector is None:
        return {
            "status": "not_implemented",
            "channel": channel.channel_name,
            "message": "No connector registered",
        }
    try:
        result = connector.pull_bookings(channel)
        if result.get("status") == "ok":
            channel.last_sync_at = timezone.now()
            channel.error_count = 0
            channel.last_error = ""
            channel.save(
                update_fields=[
                    "last_sync_at",
                    "error_count",
                    "last_error",
                    "updated_at",
                ]
            )
        elif result.get("status") == "error":
            channel.error_count += 1
            channel.last_error = result.get("message", "")[:2000]
            channel.save(update_fields=["error_count", "last_error", "updated_at"])
        return result
    except Exception as exc:
        logger.exception("pull_bookings_from_channel failed for %s", channel_id)
        raise self.retry(exc=exc)


@shared_task
def pull_bookings_from_active_channels():
    """Periodic beat task: pull bookings for every active accepting channel."""
    channels = Channel.objects.filter(is_active=True, accept_bookings=True)
    queued = 0
    for channel in channels:
        pull_bookings_from_channel.delay(channel.id)
        queued += 1
    return {"queued": queued}


def _sync_to_channel_api(channel, payload):
    connector = get_connector(channel.channel_name)
    if connector is not None:
        # Legacy per-room payload path — prefer full push_availability
        logger.debug(
            "Legacy per-room sync for %s payload keys=%s",
            channel.channel_name,
            list(payload.keys()),
        )
        return
    # Honest stubs: never silently succeed
    if channel.channel_name == "booking_com":
        raise NotImplementedError("Booking.com Connectivity API not live")
    if channel.channel_name == "trivago":
        raise NotImplementedError("Trivago sync not yet implemented")
    if channel.channel_name == "airbnb":
        raise NotImplementedError("Airbnb API sync not yet implemented; use iCal")
    if channel.channel_name == "expedia":
        raise NotImplementedError("Expedia sync not yet implemented")
    raise NotImplementedError(
        f"No connector registered for channel type '{channel.channel_name}'"
    )


def channel_health_snapshot(channel: Channel) -> dict:
    """Build sync health summary for GET channels/{id}/health/."""
    from .models import ChannelWebhookLog

    latest_sync = (
        AvailabilitySyncLog.objects.filter(channel=channel)
        .order_by("-created_at")
        .first()
    )
    pending_syncs = AvailabilitySyncLog.objects.filter(
        channel=channel, sync_status__in=["pending", "in_progress", "retry"]
    ).count()
    recent_webhooks = ChannelWebhookLog.objects.filter(channel=channel).count()
    connector = get_connector(channel.channel_name)
    return {
        "channel_id": channel.id,
        "channel_name": channel.channel_name,
        "display_name": channel.get_channel_name_display(),
        "is_active": channel.is_active,
        "sync_enabled": channel.sync_enabled,
        "accept_bookings": channel.accept_bookings,
        "connector": channel.channel_name if connector else None,
        "last_sync_at": channel.last_sync_at,
        "last_error": channel.last_error or None,
        "error_count": channel.error_count,
        "pending_sync_count": pending_syncs,
        "latest_sync_status": latest_sync.sync_status if latest_sync else None,
        "webhook_log_count": recent_webhooks,
        "healthy": channel.is_active
        and channel.error_count < 5
        and (not channel.last_error or channel.error_count == 0),
    }
