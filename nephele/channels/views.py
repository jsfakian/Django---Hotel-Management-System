"""
Views for Channel Integration API

Handles:
- Channel management (CRUD)
- Webhook for receiving bookings from OTA platforms
- Availability synchronization to channels
- Sync status monitoring
"""

import json
import hashlib
import hmac
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Channel, ChannelBooking, ChannelWebhookLog
from .serializers import (
    ChannelSerializer, ChannelDetailSerializer, ChannelBookingSerializer,
    ChannelBookingReceiptSerializer, ChannelAvailabilityStatusSerializer,
    ChannelAvailabilitySyncSerializer
)
from .tasks import channel_health_snapshot
from room.models import Room, Booking
from accounts.models import Guest
from inventory.models import AvailabilitySyncLog


def _decode_body(body):
    if isinstance(body, bytes):
        return body.decode('utf-8')
    return body


def _webhook_auth_error(channel, request, body_str):
    """Require a configured secret and a valid signature (no open webhooks)."""
    if not channel.api_secret:
        return Response(
            {"error": "Webhook secret not configured for this channel"},
            status=status.HTTP_403_FORBIDDEN,
        )
    signature = request.headers.get('X-Webhook-Signature', '').replace('sha256=', '')
    if not signature or not channel.verify_webhook_signature(body_str, signature):
        return Response(
            {"error": "Invalid webhook signature"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return None


def _parse_booking_payload(body_str):
    """Return (validated_data, None) or (None, error_response)."""
    try:
        data = json.loads(body_str)
    except json.JSONDecodeError:
        return None, Response(
            {"error": "Invalid JSON body"},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = ChannelBookingReceiptSerializer(data=data)
    if not serializer.is_valid():
        return None, Response(
            {"error": "Validation error", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    return serializer.validated_data, None


def _resolve_room_from_remote(channel, remote_room_type_id):
    """Map remote room type id → a physical Room on the channel property."""
    from channels.mapping_utils import reverse_room_type_map

    local_rt = reverse_room_type_map(channel.mapping_config).get(
        str(remote_room_type_id or "")
    )
    qs = Room.objects.filter(property=channel.property)
    if local_rt:
        room = qs.filter(room_type_fk_id=local_rt).first()
        if room:
            return room
    return qs.order_by("id").first()


def _receipt_from_normalized(channel, normalized):
    """Convert connector-normalized booking → ChannelBookingReceipt fields."""
    import time
    from decimal import Decimal

    room = _resolve_room_from_remote(
        channel, normalized.get("room_type_remote_id")
    )
    if room is None:
        return None, Response(
            {"error": "No room available for mapped room type"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    total = normalized.get("total_amount") or 0
    try:
        total = Decimal(str(total))
    except Exception:
        total = Decimal("0")
    check_in = normalized.get("check_in")
    check_out = normalized.get("check_out")
    data = {
        "channel_booking_id": str(normalized.get("external_id") or ""),
        "timestamp": int(time.time()),
        "event": "booking_created",
        "guest_first_name": normalized.get("guest_first_name") or "Guest",
        "guest_last_name": normalized.get("guest_last_name") or "",
        "guest_email": normalized.get("guest_email")
        or f"ota+{normalized.get('external_id')}@example.com",
        "room_id": room.id,
        "check_in": check_in,
        "check_out": check_out,
        "number_of_guests": 1,
        "total_price": total,
        "currency": normalized.get("currency") or "EUR",
    }
    serializer = ChannelBookingReceiptSerializer(data=data)
    if not serializer.is_valid():
        return None, Response(
            {"error": "Validation error", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return serializer.validated_data, None


def _try_connector_webhook(channel, payload):
    """Run connector.receive_webhook; return normalized booking dict or None."""
    from .connectors import get_connector

    connector = get_connector(channel.channel_name)
    if connector is None:
        return None
    try:
        result = connector.receive_webhook(channel, payload or {})
    except Exception:
        return None
    if result.get("status") == "ok" and result.get("booking"):
        return result["booking"]
    return None


def _get_channel_room(channel, validated_data):
    """Return (room, None) or (None, error_response) for the channel's property."""
    try:
        return Room.objects.get(id=validated_data['room_id'], property=channel.property), None
    except Room.DoesNotExist:
        return None, Response(
            {"error": "Room not found", "room_id": validated_data['room_id']},
            status=status.HTTP_400_BAD_REQUEST
        )


def _update_existing_channel_booking(existing, validated_data):
    """Update linked Booking from a repeated webhook (create/update path)."""
    booking = existing.nephele_booking
    booking.check_in_date = validated_data["check_in"]
    booking.check_out_date = validated_data["check_out"]
    booking.number_of_guests = validated_data["number_of_guests"]
    booking.adults = validated_data["number_of_guests"]
    booking.base_price = validated_data["total_price"]
    booking.actual_price = validated_data["total_price"]
    if validated_data.get("special_requests") is not None:
        booking.special_requests = validated_data.get("special_requests") or ""
    status_hint = str(validated_data.get("event") or "").lower()
    if "cancel" in status_hint:
        booking.status = "cancelled"
    elif booking.status == "cancelled":
        booking.status = "confirmed"
    booking.save()
    safe = _json_safe_payload(validated_data)
    existing.channel_data = safe
    existing.sync_status = "synced"
    existing.save(update_fields=["channel_data", "sync_status", "updated_at"])
    ChannelWebhookLog.objects.create(
        channel=existing.channel,
        event="booking_updated",
        payload=safe,
        status="processed",
    )
    return booking


def _duplicate_booking_response(channel, validated_data):
    try:
        existing = ChannelBooking.objects.get(
            channel=channel,
            channel_booking_id=validated_data['channel_booking_id']
        )
    except ChannelBooking.DoesNotExist:
        return None
    # Upsert: repeated OTA webhooks update the local booking instead of 409.
    booking = _update_existing_channel_booking(existing, validated_data)
    return Response(
        {
            "status": "updated",
            "message": f"Booking {validated_data['channel_booking_id']} updated",
            "booking_id": booking.id,
            "confirmation_number": booking.id,
        },
        status=status.HTTP_200_OK,
    )


def _room_unavailable_response(channel, room, validated_data):
    from inventory.services import is_room_available

    allow_overbook = bool(
        getattr(channel.property, 'allow_overbooking', False)
    )
    if not is_room_available(
        room,
        validated_data['check_in'],
        validated_data['check_out'],
        allow_overbook=allow_overbook,
    ):
        return Response(
            {
                "error": "Room not available",
                "message": "Room not available for selected dates",
                "available_rooms": list(
                    Room.objects.filter(property=channel.property).values_list('id', flat=True)[:5]
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    return None


def _send_channel_booking_alert(booking, channel):
    """Send staff notification asynchronously; never fail the booking."""
    try:
        from notifications.tasks import send_channel_booking_alert
        send_channel_booking_alert.delay(
            booking_id=booking.id,
            channel_name=channel.get_channel_name_display()
        )
    except Exception:
        pass  # Continue even if notification fails


_WEBHOOK_PII_KEYS = frozenset(
    {
        "guest_email",
        "email",
        "guest_first_name",
        "guest_last_name",
        "guest_phone",
        "phone",
        "phone_number",
        "first_name",
        "last_name",
        "name",
    }
)


def _is_pii_key(key: str) -> bool:
    key_l = (key or "").lower()
    if key_l in _WEBHOOK_PII_KEYS:
        return True
    return "email" in key_l or "phone" in key_l or key_l.endswith("_name")


def _redact_webhook_pii(data):
    """Strip guest email/name/phone from payloads stored in webhook logs."""
    if isinstance(data, list):
        return [_redact_webhook_pii(item) for item in data]
    if not isinstance(data, dict):
        return data
    out = {}
    for key, value in data.items():
        if _is_pii_key(key):
            out[key] = "[REDACTED]"
        elif isinstance(value, (dict, list)):
            out[key] = _redact_webhook_pii(value)
        else:
            out[key] = value
    return out


def _json_safe_payload(data):
    """Convert validated webhook data into JSON-serializable dict for logs."""
    from decimal import Decimal
    from datetime import date, datetime

    if isinstance(data, list):
        return [_json_safe_payload(item) for item in data]
    if not isinstance(data, dict):
        return data
    out = {}
    for key, value in data.items():
        if isinstance(value, Decimal):
            out[key] = str(value)
        elif isinstance(value, (date, datetime)):
            out[key] = value.isoformat()
        elif isinstance(value, (dict, list)):
            out[key] = _json_safe_payload(value)
        else:
            out[key] = value
    return _redact_webhook_pii(out)


def _reusable_channel_guest(email, external_id):
    """Reuse guest only when channel_external_id matches this booking."""
    if not external_id:
        return None
    existing = Guest.objects.filter(email__iexact=email).select_related("user").first()
    if not existing:
        return None
    prefs = existing.preferences or {}
    if prefs.get("channel_external_id") == external_id:
        return existing
    return None


def _unique_channel_guest_email(email):
    import secrets

    if not Guest.objects.filter(email__iexact=email).exists():
        return email
    local, _, domain = email.partition("@")
    return f"{local}+ch{secrets.token_hex(4)}@{domain or 'nephele.local'}"


def _create_channel_guest_user(validated_data, email):
    import secrets

    from django.contrib.auth.models import User

    user = User(username=f"ch_{secrets.token_hex(12)}", email=email)
    user.set_unusable_password()
    user.first_name = (validated_data.get("guest_first_name") or "Guest")[:150]
    user.last_name = (validated_data.get("guest_last_name") or "")[:150]
    user.save()
    return user


def _create_channel_guest(validated_data):
    """
    Create a Guest for an OTA webhook.

    Never attach to an existing profile by email alone — only reuse when
    preferences.channel_external_id matches this channel booking id.
    """
    email = validated_data["guest_email"]
    external_id = str(validated_data.get("channel_booking_id") or "")
    reusable = _reusable_channel_guest(email, external_id)
    if reusable:
        return reusable

    user = _create_channel_guest_user(validated_data, email)
    stored_email = _unique_channel_guest_email(email)

    return Guest.objects.create(
        user=user,
        email=stored_email,
        first_name=validated_data.get("guest_first_name") or "Guest",
        last_name=validated_data.get("guest_last_name") or "",
        phone_number=(validated_data.get("guest_phone") or "")[:20],
        preferences={
            "contact_email": email,
            "channel_external_id": external_id,
        },
    )


def _create_channel_booking(channel, room, validated_data):
    """Create guest, booking, channel link and availability atomically."""
    with transaction.atomic():
        guest = _create_channel_guest(validated_data)

        source_choices = {c[0] for c in Booking.BOOKING_SOURCE_CHOICES}
        booking_source = (
            channel.channel_name
            if channel.channel_name in source_choices
            else 'other'
        )

        # Create booking (inventory.signals apply/recount on post_save)
        booking = Booking.objects.create(
            room=room,
            guest=guest,
            check_in_date=validated_data['check_in'],
            check_out_date=validated_data['check_out'],
            number_of_guests=validated_data['number_of_guests'],
            adults=validated_data['number_of_guests'],
            base_price=validated_data['total_price'],
            actual_price=validated_data['total_price'],
            booking_source=booking_source,
            special_requests=validated_data.get('special_requests', ''),
            status='confirmed'
        )

        # Track channel booking
        ChannelBooking.objects.create(
            channel=channel,
            channel_booking_id=validated_data['channel_booking_id'],
            nephele_booking=booking,
            sync_status='synced',
            channel_data=_json_safe_payload(validated_data),
        )

        _send_channel_booking_alert(booking, channel)
    return booking


def _resolve_ingest_payload(channel, body_str):
    """Prefer connector.receive_webhook normalization; fall back to receipt schema."""
    try:
        raw_payload = json.loads(body_str) if body_str else {}
    except json.JSONDecodeError:
        raw_payload = None
    if isinstance(raw_payload, dict):
        normalized = _try_connector_webhook(channel, raw_payload)
        if normalized:
            return _receipt_from_normalized(channel, normalized)
    return _parse_booking_payload(body_str)


def _create_booking_with_log(channel, room, validated_data):
    """Create booking + webhook log; return (booking, None) or (None, error Response)."""
    safe = _json_safe_payload(validated_data)
    try:
        booking = _create_channel_booking(channel, room, validated_data)
        ChannelWebhookLog.objects.create(
            channel=channel,
            event='booking',
            payload=safe,
            status='processed',
        )
        return booking, None
    except Exception as e:
        ChannelWebhookLog.objects.create(
            channel=channel,
            event='booking',
            payload=safe,
            status='failed',
            error_message=str(e),
        )
        return None, Response(
            {"error": "Failed to create booking", "details": str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def _ingest_channel_booking(channel, request):
    """Validate webhook payload and create booking; return Response."""
    body_str = _decode_body(request.body)

    auth_error = _webhook_auth_error(channel, request, body_str)
    if auth_error is not None:
        return auth_error

    validated_data, error_response = _resolve_ingest_payload(channel, body_str)
    if error_response is not None:
        return error_response

    duplicate = _duplicate_booking_response(channel, validated_data)
    if duplicate is not None:
        return duplicate

    room, error_response = _get_channel_room(channel, validated_data)
    if error_response is not None:
        return error_response

    unavailable = _room_unavailable_response(channel, room, validated_data)
    if unavailable is not None:
        return unavailable

    booking, create_error = _create_booking_with_log(channel, room, validated_data)
    if create_error is not None:
        return create_error

    return Response(
        {
            "booking_id": booking.id,
            "status": "confirmed",
            "confirmation_number": f"BKNG-{booking.id}",
            "booking_created_at": booking.created_at.isoformat(),
        },
        status=status.HTTP_201_CREATED,
    )


def _mapping_errors(mapping, local_ids, entity_label):
    """Validate mapping keys against a set of local catalog ids."""
    errors = []
    for key, remote in mapping.items():
        try:
            rid = int(key)
        except (TypeError, ValueError):
            errors.append({'key': key, 'error': f'non-integer {entity_label} id'})
            continue
        if rid not in local_ids:
            errors.append(
                {'key': key, 'error': f'unknown {entity_label} for property'}
            )
        if not remote:
            errors.append({'key': key, 'error': 'empty remote id'})
    return errors


def _unmapped_local_ids(local_ids, mapping):
    return sorted(local_ids - {int(k) for k in mapping if str(k).isdigit()})


def _ical_feed_token_ok(request, expected):
    from accounts.api_permissions import is_hotel_staff

    if is_hotel_staff(request.user):
        return True
    provided = request.query_params.get("token") or ""
    return bool(provided) and provided == expected


def _ical_feed_get_response(request, channel, connector, expected):
    from django.http import HttpResponse

    if not _ical_feed_token_ok(request, expected):
        return Response(
            {
                "error": "Invalid or missing ical token",
                "hint": "Pass ?token=<ical_token> from channel.mapping_config",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    if request.query_params.get("url_only") in ("1", "true", "True"):
        return Response(
            {
                "channel_id": channel.id,
                "property_id": channel.property_id,
                "ical_url": connector.get_feed_url(channel),
                "ical_token": expected,
            }
        )
    feed = connector.export_feed(channel)
    return HttpResponse(feed, content_type="text/calendar; charset=utf-8")


def _ical_feed_put_response(request, channel, connector):
    url = request.data.get("ical_url") or request.data.get("url") or ""
    try:
        result = connector.set_feed_url(channel, url)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if request.data.get("import") in (True, "true", "1", 1):
        pull = connector.pull_bookings(channel)
        result["pull"] = pull
        ChannelWebhookLog.objects.create(
            channel=channel,
            event="ical_import",
            payload={"ical_url": url, "pull": pull},
            status="processed" if pull.get("status") == "ok" else "failed",
            error_message=pull.get("message", ""),
        )
    return Response(result)


class ChannelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing OTA channel integrations.
    
    Endpoints:
    - GET/POST /channels
    - GET/PUT/DELETE /channels/{id}
    - POST /channels/{id}/bookings (webhook)
    - POST /channels/{id}/availability/sync
    - GET /channels/{id}/availability/status
    """
    
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        from accounts.api_permissions import IsHotelStaff
        from rest_framework.permissions import AllowAny

        if self.action == 'receive_booking':
            return [AllowAny()]
        # Public iCal export (GET); configuring URL (PUT) stays staff-only
        if self.action == 'ical_feed' and self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsHotelStaff()]
    filterset_fields = ['property', 'channel_name', 'is_active']
    search_fields = ['channel_name', 'account_id']
    ordering_fields = ['created_at', 'last_sync_at']
    
    def get_queryset(self):
        """Filter channels by user's accessible properties"""
        # Public iCal export is token-gated; allow lookup by pk for GET.
        if self.action == "ical_feed" and self.request.method == "GET":
            return Channel.objects.filter(channel_name="ical", is_active=True)
        user = self.request.user
        if user.is_superuser or user.groups.filter(name__in=['admin', 'manager']).exists():
            return Channel.objects.all()
        # Employees see channels for their assigned properties
        if hasattr(user, 'employee_profile'):
            emp = user.employee_profile
            if emp.property_id:
                return Channel.objects.filter(property_id=emp.property_id)
        return Channel.objects.none()
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve endpoint"""
        if self.action == 'retrieve':
            return ChannelDetailSerializer
        return ChannelSerializer
    
    @action(detail=True, methods=['post'], url_path='bookings')
    @method_decorator(csrf_exempt)
    def receive_booking(self, request, pk=None):
        """
        Webhook endpoint for receiving bookings from OTA platforms.
        
        POST /channels/{channel_id}/bookings
        
        Handles bookings from Trivago, Booking.com, Airbnb, etc.
        Anonymous OTAs must resolve the channel by pk (get_queryset is empty for anon).
        """
        try:
            channel = Channel.objects.get(pk=pk)
        except Channel.DoesNotExist:
            return Response(
                {"error": "Channel not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not channel.accept_bookings:
            return Response(
                {"error": "Channel not accepting bookings"},
                status=status.HTTP_403_FORBIDDEN
            )

        return _ingest_channel_booking(channel, request)
    
    @action(detail=True, methods=['post'], url_path='availability/sync')
    def sync_availability(self, request, pk=None):
        """
        Trigger availability synchronization to OTA platform.
        """
        channel = self.get_object()
        
        if not channel.sync_enabled:
            return Response(
                {"error": "Sync disabled for this channel"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ChannelAvailabilitySyncSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Queue sync task
        try:
            from .tasks import sync_availability_to_channel
            task = sync_availability_to_channel.delay(
                channel_id=channel.id,
                sync_type=serializer.validated_data['sync_type']
            )
            return Response(
                {
                    "sync_id": task.id,
                    "status": "queued",
                    "message": "Availability sync queued for processing"
                },
                status=status.HTTP_202_ACCEPTED
            )
        except Exception as e:
            return Response(
                {"error": "Failed to queue sync", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='availability/status')
    def availability_status(self, request, pk=None):
        """
        Get synchronization status with channel.
        """
        channel = self.get_object()
        
        # Get latest sync log
        latest_sync = AvailabilitySyncLog.objects.filter(
            channel=channel
        ).order_by('-created_at').first()
        
        pending_syncs = AvailabilitySyncLog.objects.filter(
            channel=channel,
            sync_status__in=['pending', 'in_progress', 'retry']
        ).count()
        
        return Response({
            "channel_name": channel.get_channel_name_display(),
            "property_id": channel.property.id,
            "is_active": channel.is_active,
            "sync_enabled": channel.sync_enabled,
            "last_sync_at": latest_sync.completed_at if latest_sync else None,
            "sync_status": latest_sync.get_sync_status_display() if latest_sync else "Never synced",
            "rooms_synced": latest_sync.rooms_affected if latest_sync else 0,
            "pending_sync_count": pending_syncs,
            "last_error": channel.last_error if channel.error_count > 0 else None,
            "error_count": channel.error_count
        })

    @action(detail=True, methods=['get'], url_path='health')
    def health(self, request, pk=None):
        """GET /channels/{id}/health/ — sync health snapshot."""
        channel = self.get_object()
        return Response(channel_health_snapshot(channel))

    @action(detail=True, methods=['get', 'post'], url_path='validate-mappings')
    def validate_mappings(self, request, pk=None):
        """
        Validate room_type_mappings / rate_plan_mappings against local catalog.
        POST may include proposed mapping_config to dry-run without saving.
        """
        from channels.mapping_utils import normalize_mapping_config
        from inventory.models import RatePlan, RoomType

        channel = self.get_object()
        cfg = request.data.get('mapping_config') if request.method == 'POST' else None
        cfg = cfg or channel.mapping_config or {}
        normalized = normalize_mapping_config(cfg)
        rt_map = normalized['room_type_mappings']
        rp_map = normalized['rate_plan_mappings']

        local_rt = set(
            RoomType.objects.filter(property_id=channel.property_id).values_list(
                'id', flat=True
            )
        )
        local_rp = set(
            RatePlan.objects.filter(property_id=channel.property_id).values_list(
                'id', flat=True
            )
        )
        rt_errors = _mapping_errors(rt_map, local_rt, 'room type')
        rp_errors = _mapping_errors(rp_map, local_rp, 'rate plan')
        ok = not rt_errors and not rp_errors and bool(rt_map)
        return Response(
            {
                'valid': ok,
                'room_type_mappings_count': len(rt_map),
                'rate_plan_mappings_count': len(rp_map),
                'room_type_errors': rt_errors,
                'rate_plan_errors': rp_errors,
                'unmapped_room_types': _unmapped_local_ids(local_rt, rt_map),
                'unmapped_rate_plans': _unmapped_local_ids(local_rp, rp_map),
            }
        )

    @action(detail=True, methods=['get', 'put'], url_path='ical')
    def ical_feed(self, request, pk=None):
        """
        GET  /channels/{id}/ical/ — export VCALENDAR for the property
             or return configured remote feed URL (?url_only=1).
        PUT  /channels/{id}/ical/ — set mapping_config.ical_url
             body: {"ical_url": "https://..."}; optional import=true to pull.
        """
        from .connectors.ical import ICalConnector, ensure_ical_token

        channel = self.get_object()
        connector = ICalConnector()

        if request.method == 'GET':
            expected = ensure_ical_token(channel)
            return _ical_feed_get_response(request, channel, connector, expected)
        return _ical_feed_put_response(request, channel, connector)
