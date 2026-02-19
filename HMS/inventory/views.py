"""
Views for Inventory Management (Nephele) API

Centralized room availability management across all booking sources and channels.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser

from .models import RoomAvailability, AvailabilitySyncLog
from .serializers import (
    RoomAvailabilitySerializer, RoomAvailabilityBulkSerializer,
    RoomAvailabilityUpdateSerializer, OverbookingSerializer,
    AvailabilitySyncLogSerializer
)
from room.models import Room
from properties.models import Property
from channels.models import Channel


class RoomAvailabilityViewSet(viewsets.ViewSet):
    """
    ViewSet for managing centralized room availability.
    
    Endpoints:
    - GET /inventory/availability/{property_id}
    - GET /inventory/rooms/{room_id}/availability
    - PUT /inventory/rooms/{room_id}/availability
    - POST /inventory/overbook
    - GET /inventory/sync-log/{property_id}
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='availability/(?P<property_id>[0-9]+)')
    def get_property_availability(self, request, property_id=None):
        """
        Get availability for all rooms in a property for a date range.
        
        GET /inventory/availability/{property_id}?date_from=2026-03-15&date_to=2026-03-31
        """
        property = get_object_or_404(Property, id=property_id)
        
        # Verify user has access to this property
        if not self._user_can_access_property(request.user, property):
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Parse query parameters
        try:
            date_from = datetime.strptime(request.query_params.get('date_from', ''), '%Y-%m-%d').date()
            date_to = datetime.strptime(request.query_params.get('date_to', ''), '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if date_to <= date_from:
            return Response(
                {"error": "date_to must be after date_from"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get availability for all rooms
        rooms = Room.objects.filter(property=property)
        availability_data = []
        
        for room in rooms:
            room_avail = RoomAvailability.objects.filter(
                room=room,
                date__gte=date_from,
                date__lt=date_to
            ).values('date').distinct()
            
            availability_by_date = []
            for avail in room_avail:
                availability_by_date.append(avail)
            
            availability_data.append({
                "room_id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type,
                "availability_by_date": availability_by_date
            })
        
        return Response({
            "property_id": property.id,
            "date_range": {"from": date_from.isoformat(), "to": date_to.isoformat()},
            "rooms": availability_data
        })
    
    @action(detail=False, methods=['put'], url_path='rooms/(?P<room_id>[0-9]+)/availability')
    def update_room_availability(self, request, room_id=None):
        """
        Update room availability for a date range (staff override).
        
        PUT /inventory/rooms/{room_id}/availability
        
        Body:
        {
            "date_from": "2026-03-15",
            "date_to": "2026-03-20",
            "available_units": 2,
            "blocked_units": 0,
            "notes": "Maintenance scheduled"
        }
        """
        room = get_object_or_404(Room, id=room_id)
        
        # Verify user has access to this property
        if not self._user_can_access_property(request.user, room.property):
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RoomAvailabilityUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        date_from = data['date_from']
        date_to = data['date_to']
        
        try:
            with transaction.atomic():
                current_date = date_from
                while current_date < date_to:
                    avail, created = RoomAvailability.objects.get_or_create(
                        room=room,
                        date=current_date,
                        defaults={
                            'total_units': 1,
                            'available_units': 1,
                            'staff_override': True
                        }
                    )
                    
                    if not created:
                        avail.available_units = data['available_units']
                        avail.blocked_units = data.get('blocked_units', 0)
                        avail.staff_override = True
                        avail.updated_by = request.user
                    
                    if data.get('notes'):
                        avail.notes = data['notes']
                    
                    avail.save()
                    current_date += timedelta(days=1)
                
                num_days = (date_to - date_from).days
                
                # Trigger availability sync to all channels
                try:
                    from channels.tasks import sync_availability_to_channels
                    sync_availability_to_channels.delay(
                        property_id=room.property.id,
                        room_ids=[room.id],
                        date_from=str(date_from),
                        date_to=str(date_to)
                    )
                except Exception:
                    pass  # Continue even if sync fails
        
        except Exception as e:
            return Response(
                {"error": "Failed to update availability", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            "room_id": room.id,
            "dates_updated": num_days,
            "override_applied": True
        })
    
    @action(detail=False, methods=['post'])
    def overbook(self, request):
        """
        Allow overbooking for specific dates (staff controlled).
        
        POST /inventory/overbook
        
        Body:
        {
            "room_id": 123,
            "date_from": "2026-03-15",
            "date_to": "2026-03-20",
            "overbook_units": 2,
            "reason": "group_booking"
        }
        """
        serializer = OverbookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        room = get_object_or_404(Room, id=serializer.validated_data['room_id'])
        
        # Verify user has access
        if not self._user_can_access_property(request.user, room.property):
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = serializer.validated_data
        
        try:
            with transaction.atomic():
                current_date = data['date_from']
                while current_date < data['date_to']:
                    avail, _ = RoomAvailability.objects.get_or_create(
                        room=room,
                        date=current_date,
                        defaults={'total_units': 1, 'available_units': 1}
                    )
                    
                    avail.overbooked_units = data['overbook_units']
                    avail.notes = f"Overbooking: {data['reason']} - {data.get('notes', '')}"
                    avail.updated_by = request.user
                    avail.save()
                    
                    current_date += timedelta(days=1)
        
        except Exception as e:
            return Response(
                {"error": "Failed to create overbooking", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            "room_id": room.id,
            "overbook_id": f"OB-{room.id}-{data['date_from']}",
            "status": "approved"
        })
    
    @action(detail=False, methods=['get'], url_path='sync-log/(?P<property_id>[0-9]+)')
    def sync_log(self, request, property_id=None):
        """
        Get synchronization log for a property.
        
        GET /inventory/sync-log/{property_id}?status=failed&days=7
        """
        property = get_object_or_404(Property, id=property_id)
        
        # Verify access
        if not self._user_can_access_property(request.user, property):
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Filter by status
        logs = AvailabilitySyncLog.objects.filter(property=property)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            logs = logs.filter(sync_status=status_filter)
        
        # Filter by date
        days = int(request.query_params.get('days', 30))
        cutoff_date = datetime.now() - timedelta(days=days)
        logs = logs.filter(created_at__gte=cutoff_date)
        
        logs = logs.order_by('-created_at')[:100]  # Limit to 100 latest
        
        serializer = AvailabilitySyncLogSerializer(logs, many=True)
        
        return Response({
            "property_id": property.id,
            "total_logs": len(logs),
            "sync_logs": serializer.data
        })
    
    def _user_can_access_property(self, user, property):
        """Check if user can access property"""
        # Admin can access all
        if user.is_staff:
            return True
        
        # Check if user is manager
        if hasattr(user, 'managed_properties') and property in user.managed_properties.all():
            return True
        
        # Check if user is staff at property
        if hasattr(user, 'employee'):
            if user.employee.filter(property=property, status='active').exists():
                return True
        
        return False
