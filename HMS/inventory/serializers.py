"""
Serializers for Inventory Management API
"""

from rest_framework import serializers
from .models import RoomAvailability, AvailabilitySyncLog
from room.models import Room


class RoomAvailabilitySerializer(serializers.ModelSerializer):
    """Room availability serializer"""
    
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    room_type = serializers.CharField(source='room.room_type', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    occupancy_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = RoomAvailability
        fields = [
            'id', 'room', 'room_number', 'room_type', 'date',
            'total_units', 'available_units', 'booked_units',
            'blocked_units', 'overbooked_units',
            'base_price', 'dynamic_price',
            'is_available', 'occupancy_rate',
            'staff_override', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'occupancy_rate', 'is_available']


class RoomAvailabilityBulkSerializer(serializers.Serializer):
    """Serializer for bulk availability query"""
    
    property_id = serializers.IntegerField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    room_type = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['date_to'] <= data['date_from']:
            raise serializers.ValidationError("date_to must be after date_from")
        return data


class RoomAvailabilityUpdateSerializer(serializers.Serializer):
    """Serializer for updating room availability"""
    
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    available_units = serializers.IntegerField(min_value=0)
    blocked_units = serializers.IntegerField(min_value=0, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['date_to'] <= data['date_from']:
            raise serializers.ValidationError("date_to must be after date_from")
        return data


class OverbookingSerializer(serializers.Serializer):
    """Serializer for overbooking requests"""
    
    REASON_CHOICES = (
        ('group_booking', 'Group Booking Adjustment'),
        ('management_override', 'Management Override'),
        ('vip_guest', 'VIP Guest'),
        ('staff_stay', 'Staff Stay'),
        ('other', 'Other Reason'),
    )
    
    room_id = serializers.IntegerField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    overbook_units = serializers.IntegerField(min_value=1)
    reason = serializers.ChoiceField(choices=REASON_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['date_to'] <= data['date_from']:
            raise serializers.ValidationError("date_to must be after date_from")
        return data


class AvailabilitySyncLogSerializer(serializers.ModelSerializer):
    """Availability sync log serializer"""
    
    channel_name = serializers.CharField(source='channel.get_channel_name_display', read_only=True)
    sync_type_display = serializers.CharField(source='get_sync_type_display', read_only=True)
    sync_status_display = serializers.CharField(source='get_sync_status_display', read_only=True)
    
    class Meta:
        model = AvailabilitySyncLog
        fields = [
            'id', 'property', 'channel', 'channel_name',
            'sync_type', 'sync_type_display',
            'sync_status', 'sync_status_display',
            'rooms_affected', 'date_from', 'date_to',
            'error_message', 'attempt_count', 'response_code',
            'created_at', 'completed_at', 'next_retry_at'
        ]
        read_only_fields = [
            'id', 'channel_name', 'sync_type_display', 'sync_status_display',
            'error_message', 'attempt_count', 'response_code',
            'created_at', 'completed_at', 'next_retry_at'
        ]
