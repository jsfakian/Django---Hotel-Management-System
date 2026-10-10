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


def _get_channel_room(channel, validated_data):
    """Return (room, None) or (None, error_response) for the channel's property."""
    try:
        return Room.objects.get(id=validated_data['room_id'], property=channel.property), None
    except Room.DoesNotExist:
        return None, Response(
            {"error": "Room not found", "room_id": validated_data['room_id']},
            status=status.HTTP_400_BAD_REQUEST
        )


def _duplicate_booking_response(channel, validated_data):
    try:
        existing = ChannelBooking.objects.get(
            channel=channel,
            channel_booking_id=validated_data['channel_booking_id']
        )
    except ChannelBooking.DoesNotExist:
        return None
    return Response(
        {
            "error": "Duplicate booking",
            "message": f"Booking {validated_data['channel_booking_id']} already exists",
            "booking_id": existing.nephele_booking.id,
            "confirmation_number": existing.nephele_booking.id
        },
        status=status.HTTP_409_CONFLICT
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


def _create_channel_booking(channel, room, validated_data):
    """Create guest, booking, channel link and availability atomically."""
    with transaction.atomic():
        # Get or create guest
        guest, _ = Guest.objects.get_or_create(
            email=validated_data['guest_email'],
            defaults={
                'first_name': validated_data['guest_first_name'],
                'last_name': validated_data['guest_last_name'],
                'phone_number': validated_data.get('guest_phone', ''),
            }
        )

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
            channel_data=validated_data
        )

        _send_channel_booking_alert(booking, channel)
    return booking


def _ingest_channel_booking(channel, request):
    """Validate webhook payload and create booking; return Response."""
    body_str = _decode_body(request.body)

    auth_error = _webhook_auth_error(channel, request, body_str)
    if auth_error is not None:
        return auth_error

    validated_data, error_response = _parse_booking_payload(body_str)
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

    try:
        booking = _create_channel_booking(channel, room, validated_data)
        ChannelWebhookLog.objects.create(
            channel=channel,
            event='booking',
            payload=validated_data,
            status='processed',
        )
    except Exception as e:
        ChannelWebhookLog.objects.create(
            channel=channel,
            event='booking',
            payload=validated_data,
            status='failed',
            error_message=str(e),
        )
        return Response(
            {"error": "Failed to create booking", "details": str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return Response(
        {
            "booking_id": booking.id,
            "status": "confirmed",
            "confirmation_number": f"BKNG-{booking.id}",
            "booking_created_at": booking.created_at.isoformat()
        },
        status=status.HTTP_201_CREATED
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
        from inventory.models import RatePlan, RoomType

        channel = self.get_object()
        cfg = request.data.get('mapping_config') if request.method == 'POST' else None
        cfg = cfg or channel.mapping_config or {}
        rt_map = cfg.get('room_type_mappings') or {}
        rp_map = cfg.get('rate_plan_mappings') or cfg.get('rate_mappings') or {}

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
        from django.http import HttpResponse
        from .connectors.ical import ICalConnector

        channel = self.get_object()
        connector = ICalConnector()

        if request.method == 'GET':
            if request.query_params.get('url_only') in ('1', 'true', 'True'):
                return Response({
                    "channel_id": channel.id,
                    "property_id": channel.property_id,
                    "ical_url": connector.get_feed_url(channel),
                })
            feed = connector.export_feed(channel)
            return HttpResponse(feed, content_type='text/calendar; charset=utf-8')

        # PUT — configure remote feed URL
        url = request.data.get('ical_url') or request.data.get('url') or ''
        try:
            result = connector.set_feed_url(channel, url)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if request.data.get('import') in (True, 'true', '1', 1):
            pull = connector.pull_bookings(channel)
            result['pull'] = pull
            ChannelWebhookLog.objects.create(
                channel=channel,
                event='ical_import',
                payload={'ical_url': url, 'pull': pull},
                status='processed' if pull.get('status') == 'ok' else 'failed',
                error_message=pull.get('message', ''),
            )
        return Response(result)
