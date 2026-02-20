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
from datetime import datetime, timedelta
from decimal import Decimal

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser

from .models import Channel, ChannelBooking
from .serializers import (
    ChannelSerializer, ChannelDetailSerializer, ChannelBookingSerializer,
    ChannelBookingReceiptSerializer, ChannelAvailabilityStatusSerializer,
    ChannelAvailabilitySyncSerializer
)
from room.models import Room, Booking
from accounts.models import Guest
from inventory.models import RoomAvailability, AvailabilitySyncLog
from properties.models import Property


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
    filterset_fields = ['property', 'channel_name', 'is_active']
    search_fields = ['channel_name', 'account_id']
    ordering_fields = ['created_at', 'last_sync_at']
    
    def get_queryset(self):
        """Filter channels by user's accessible properties"""
        user = self.request.user
        # Staff can see channels for their properties
        if hasattr(user, 'employee'):
            properties = user.employee.filter(status='active').values_list('property', flat=True)
            return Channel.objects.filter(property__in=properties)
        # Managers can see all channels for their properties
        if hasattr(user, 'managed_properties'):
            return Channel.objects.filter(property__in=user.managed_properties.all())
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
        """
        channel = self.get_object()
        
        if not channel.accept_bookings:
            return Response(
                {"error": "Channel not accepting bookings"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Parse request body for signature verification
        body = request.body
        if isinstance(body, bytes):
            body_str = body.decode('utf-8')
        else:
            body_str = body
        
        # Verify webhook signature if secret is configured
        if channel.api_secret:
            signature = request.headers.get('X-Webhook-Signature', '').replace('sha256=', '')
            if not signature or not channel.verify_webhook_signature(body_str, signature):
                return Response(
                    {"error": "Invalid webhook signature"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # Parse and validate booking data
        try:
            data = json.loads(body_str)
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON body"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ChannelBookingReceiptSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {"error": "Validation error", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        # Check for duplicate booking
        try:
            existing = ChannelBooking.objects.get(
                channel=channel,
                channel_booking_id=validated_data['channel_booking_id']
            )
            return Response(
                {
                    "error": "Duplicate booking",
                    "message": f"Booking {validated_data['channel_booking_id']} already exists",
                    "booking_id": existing.nephele_booking.id,
                    "confirmation_number": existing.nephele_booking.id
                },
                status=status.HTTP_409_CONFLICT
            )
        except ChannelBooking.DoesNotExist:
            pass
        
        # Verify room exists and is accessible by property
        try:
            room = Room.objects.get(id=validated_data['room_id'], property=channel.property)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found", "room_id": validated_data['room_id']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check availability
        availability = RoomAvailability.objects.filter(
            room=room,
            date__gte=validated_data['check_in'],
            date__lt=validated_data['check_out']
        ).values_list('available_units', flat=True)
        
        if availability.exists() and any(units == 0 for units in availability):
            return Response(
                {
                    "error": "Room not available",
                    "message": f"Room not available for selected dates",
                    "available_rooms": list(
                        Room.objects.filter(property=channel.property).values_list('id', flat=True)[:5]
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Get or create guest
                guest, _ = Guest.objects.get_or_create(
                    email=validated_data['guest_email'],
                    defaults={
                        'first_name': validated_data['guest_first_name'],
                        'last_name': validated_data['guest_last_name'],
                        'phone': validated_data.get('guest_phone', ''),
                    }
                )
                
                # Create booking
                booking = Booking.objects.create(
                    room=room,
                    guest=guest,
                    check_in_date=validated_data['check_in'],
                    check_out_date=validated_data['check_out'],
                    number_of_guests=validated_data['number_of_guests'],
                    base_price=validated_data['total_price'],
                    actual_price=validated_data['total_price'],
                    booking_source=channel.channel_name[-3:].upper() if len(channel.channel_name) > 3 else channel.channel_name,
                    special_requests=validated_data.get('special_requests', ''),
                    status='confirmed'
                )
                
                # Track channel booking
                channel_booking = ChannelBooking.objects.create(
                    channel=channel,
                    channel_booking_id=validated_data['channel_booking_id'],
                    nephele_booking=booking,
                    sync_status='synced',
                    channel_data=validated_data
                )
                
                # Update availability - decrement available units
                num_nights = (validated_data['check_out'] - validated_data['check_in']).days
                for i in range(num_nights):
                    check_date = validated_data['check_in'] + timedelta(days=i)
                    avail, _ = RoomAvailability.objects.get_or_create(
                        room=room,
                        date=check_date,
                        defaults={'total_units': 1, 'available_units': 1}
                    )
                    avail.booked_units += 1
                    avail.available_units = max(0, avail.total_units - avail.booked_units - avail.blocked_units - avail.overbooked_units)
                    avail.save()
                
                # Send staff notification asynchronously
                try:
                    from notifications.tasks import send_channel_booking_alert
                    send_channel_booking_alert.delay(
                        booking_id=booking.id,
                        channel_name=channel.get_channel_name_display()
                    )
                except Exception:
                    pass  # Continue even if notification fails
                
        except Exception as e:
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
