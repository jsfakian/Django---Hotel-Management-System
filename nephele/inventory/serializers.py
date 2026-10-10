# nephele/inventory/serializers.py
"""Serializers for Inventory Management API."""

from rest_framework import serializers

from .models import (
    AvailabilitySyncLog,
    RatePlan,
    RatePlanPrice,
    RoomAvailability,
    RoomType,
    RoomTypeAvailability,
)


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


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = [
            'id', 'property', 'code', 'name', 'capacity', 'max_occupancy',
            'base_occupancy', 'amenities', 'base_price', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RatePlanSerializer(serializers.ModelSerializer):
    room_type_ids = serializers.PrimaryKeyRelatedField(
        source='room_types',
        many=True,
        queryset=RoomType.objects.all(),
        required=False,
    )

    class Meta:
        model = RatePlan
        fields = [
            'id', 'property', 'code', 'name', 'meal_plan', 'is_refundable',
            'cancellation_policy', 'room_type_ids', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoomTypeAvailabilitySerializer(serializers.ModelSerializer):
    available_allotment = serializers.IntegerField(read_only=True)

    class Meta:
        model = RoomTypeAvailability
        fields = [
            'id', 'room_type', 'date', 'allotment', 'booked', 'stop_sell',
            'min_stay', 'max_stay', 'cta', 'ctd', 'closed', 'restrictions',
            'available_allotment', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'available_allotment', 'created_at', 'updated_at']


class RoomTypeAvailabilityBulkUpsertSerializer(serializers.Serializer):
    """Bulk upsert calendar rows for a room type."""

    date = serializers.DateField()
    allotment = serializers.IntegerField(min_value=0, required=False)
    booked = serializers.IntegerField(min_value=0, required=False)
    stop_sell = serializers.BooleanField(required=False)
    min_stay = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    max_stay = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    cta = serializers.BooleanField(required=False)
    ctd = serializers.BooleanField(required=False)
    closed = serializers.BooleanField(required=False)
    restrictions = serializers.DictField(required=False)


class AvailabilityQuoteSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    adults = serializers.IntegerField(min_value=1)
    children = serializers.IntegerField(min_value=0, required=False, default=0)
    children_ages = serializers.ListField(
        child=serializers.IntegerField(min_value=0),
        required=False,
        allow_empty=True,
    )

    def validate(self, data):
        if data['check_out'] <= data['check_in']:
            raise serializers.ValidationError('check_out must be after check_in')
        return data


class RatePlanPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatePlanPrice
        fields = [
            'id', 'rate_plan', 'room_type', 'date',
            'price_1', 'price_2', 'price_3', 'price_4',
            'price_by_occupancy', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
