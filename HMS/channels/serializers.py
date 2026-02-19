"""
Serializers for Channel Integration API
"""

from rest_framework import serializers
from .models import Channel, ChannelBooking
from room.models import Booking
from properties.models import Property


class ChannelSerializer(serializers.ModelSerializer):
    """Channel configuration serializer"""
    
    class Meta:
        model = Channel
        fields = [
            'id', 'property', 'channel_name', 'channel_type',
            'account_id', 'is_active', 'sync_enabled', 'accept_bookings',
            'last_sync_at', 'last_error', 'error_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_sync_at', 'last_error', 'error_count', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Mask API key in responses"""
        data = super().to_representation(instance)
        if instance.api_key:
            data['api_key'] = instance.get_readable_api_key()
        return data


class ChannelDetailSerializer(ChannelSerializer):
    """Detailed channel serializer with mapping config"""
    
    class Meta:
        model = Channel
        fields = [
            'id', 'property', 'channel_name', 'channel_type',
            'account_id', 'is_active', 'sync_enabled', 'accept_bookings',
            'mapping_config', 'last_sync_at', 'last_error', 'error_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_sync_at', 'last_error', 'error_count', 'created_at', 'updated_at']


class ChannelBookingSerializer(serializers.ModelSerializer):
    """Channel booking reference serializer"""
    
    class Meta:
        model = ChannelBooking
        fields = [
            'id', 'channel', 'channel_booking_id', 'nephele_booking',
            'sync_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChannelBookingReceiptSerializer(serializers.Serializer):
    """Serializer for receiving bookings from OTA channels"""
    
    channel_booking_id = serializers.CharField(max_length=255)
    timestamp = serializers.IntegerField()
    event = serializers.CharField(default='booking_created')
    
    # Guest data
    guest_first_name = serializers.CharField(max_length=100)
    guest_last_name = serializers.CharField(max_length=100)
    guest_email = serializers.EmailField()
    guest_phone = serializers.CharField(max_length=20, required=False)
    
    # Booking details
    room_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    number_of_guests = serializers.IntegerField()
    special_requests = serializers.CharField(required=False, allow_blank=True)
    
    # Pricing
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(default='USD')
    
    def validate(self, data):
        """Validate booking data"""
        if data['check_out'] <= data['check_in']:
            raise serializers.ValidationError("Check-out must be after check-in")
        if data['number_of_guests'] < 1:
            raise serializers.ValidationError("Number of guests must be at least 1")
        return data


class ChannelAvailabilityStatusSerializer(serializers.Serializer):
    """Serializer for channel availability /status endpoint"""
    
    channel_name = serializers.CharField(read_only=True)
    property_id = serializers.IntegerField(read_only=True)
    last_sync_at = serializers.DateTimeField(read_only=True)
    sync_status = serializers.CharField(read_only=True)
    rooms_synced = serializers.IntegerField(read_only=True)
    pending_sync_count = serializers.IntegerField(read_only=True)
    last_error = serializers.CharField(read_only=True, allow_null=True)


class ChannelAvailabilitySyncSerializer(serializers.Serializer):
    """Serializer for triggering availability sync"""
    
    SYNC_TYPE_CHOICES = (
        ('full_sync', 'Full Synchronization'),
        ('incremental_sync', 'Incremental Sync'),
        ('date_range', 'Date Range Sync'),
    )
    
    sync_type = serializers.ChoiceField(choices=SYNC_TYPE_CHOICES)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    override_staff = serializers.BooleanField(default=False)
    
    def validate(self, data):
        """Validate sync request"""
        if data['sync_type'] == 'date_range':
            if not data.get('date_from') or not data.get('date_to'):
                raise serializers.ValidationError(
                    "date_from and date_to required for date_range sync type"
                )
            if data['date_to'] <= data['date_from']:
                raise serializers.ValidationError("date_to must be after date_from")
        return data
