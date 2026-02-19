"""
Serializers for room app models (bookings, rooms, services)

Per Task 4: API Design Specifications
"""

from rest_framework import serializers
from decimal import Decimal
from room.models import Room, Booking, Dependees, Refund, RoomService


class RoomBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for Room model"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 'room_number', 'floor', 'room_type', 'capacity',
            'number_of_beds', 'base_price', 'current_price', 'status',
            'property', 'property_name', 'amenities'
        ]
        read_only_fields = ['id']


class RoomDetailedSerializer(RoomBasicSerializer):
    """Detailed serializer with additional room information"""
    
    availability = serializers.SerializerMethodField()
    
    class Meta(RoomBasicSerializer.Meta):
        fields = RoomBasicSerializer.Meta.fields + [
            'status_start_date', 'status_end_date', 'created_at',
            'updated_at', 'availability'
        ]
        read_only_fields = RoomBasicSerializer.Meta.read_only_fields + ['created_at', 'updated_at']
    
    def get_availability(self, obj) -> bool:
        """Check room availability for requested dates"""
        request = self.context.get('request')
        if request and hasattr(request, 'query_params'):
            check_in = request.query_params.get('check_in')
            check_out = request.query_params.get('check_out')
            if check_in and check_out:
                # Check for overlapping bookings
                bookings = Booking.objects.filter(
                    room=obj,
                    check_in_date__lt=check_out,
                    check_out_date__gt=check_in,
                    status__in=['confirmed', 'checked_in']
                )
                return bookings.count() == 0
        return True


class DependeesSerializer(serializers.ModelSerializer):
    """Serializer for guest dependents"""
    
    class Meta:
        model = Dependees
        fields = ['id', 'name', 'relationship', 'created_at']
        read_only_fields = ['id', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model"""
    
    room_detail = RoomBasicSerializer(source='room', read_only=True)
    guest_name = serializers.SerializerMethodField()
    travel_agency_name = serializers.CharField(source='travel_agency.name', read_only=True)
    dependees = DependeesSerializer(source='guests_list', many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    nights_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Booking
        fields = [
            'id', 'room', 'room_detail', 'guest', 'guest_name',
            'check_in_date', 'check_out_date', 'date_of_reservation',
            'number_of_guests', 'status', 'base_price', 'actual_price',
            'total_price', 'nights_count',
            'travel_agency', 'travel_agency_name',
            'notes', 'special_requests', 'dependees',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_guest_name(self, obj) -> str:
        if obj.guest:
            return f"{obj.guest.first_name} {obj.guest.last_name}"
        return "Unknown"
    
    def get_total_price(self, obj) -> Decimal:
        return obj.actual_price or obj.base_price
    
    def get_nights_count(self, obj) -> int:
        delta = obj.check_out_date - obj.check_in_date
        return delta.days


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for Refund model"""
    
    guest_name = serializers.CharField(source='guest', read_only=True)
    booking_ref = serializers.CharField(source='booking.id', read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'guest', 'guest_name', 'booking', 'booking_ref',
            'reason', 'status', 'refund_amount', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoomServiceSerializer(serializers.ModelSerializer):
    """Serializer for RoomService model"""
    
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    booking_ref = serializers.CharField(source='booking.id', read_only=True, allow_null=True)
    
    class Meta:
        model = RoomService
        fields = [
            'id', 'booking', 'booking_ref', 'room', 'room_number',
            'service_type', 'status', 'description', 'price',
            'created_date', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at']


class BookingDetailedSerializer(BookingSerializer):
    """Extended booking serializer with related data"""
    
    room_detail = RoomDetailedSerializer(source='room', read_only=True)
    services = RoomServiceSerializer(source='room_services', many=True, read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)
    
    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + ['services', 'refunds']
