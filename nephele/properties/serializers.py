"""
Serializers for properties app models

Per Task 4: API Design Specifications
"""

from rest_framework import serializers
from properties.models import Property, TravelAgency


class PropertySerializer(serializers.ModelSerializer):
    """Serializer for Property model"""
    
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    rooms_count = serializers.SerializerMethodField()
    available_rooms = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'name', 'location', 'address',
            'city', 'postal_code', 'country', 'phone_number', 'email',
            'website', 'total_rooms', 'star_rating', 'manager',
            'manager_name', 'rooms_count', 'available_rooms',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'rooms_count', 'available_rooms']
    
    def get_rooms_count(self, obj) -> int:
        return obj.rooms.count()
    
    def get_available_rooms(self, obj) -> int:
        return obj.available_rooms()


class TravelAgencySerializer(serializers.ModelSerializer):
    """Serializer for TravelAgency model"""
    
    active_contracts = serializers.SerializerMethodField()
    
    class Meta:
        model = TravelAgency
        fields = [
            'id', 'name', 'description', 'contact_name', 'email',
            'phone', 'website', 'address', 'city', 'country',
            'commission_percentage', 'status', 'active_contracts',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_active_contracts(self, obj) -> int:
        from contracts.models import Contract
        return Contract.objects.filter(
            travel_agency=obj,
            status='active'
        ).count()


class PropertyDetailSerializer(PropertySerializer):
    """Extended serializer with related room data"""
    
    rooms = serializers.SerializerMethodField()
    employees = serializers.SerializerMethodField()
    
    def get_rooms(self, obj) -> list[dict]:
        from room.serializers import RoomBasicSerializer
        rooms = obj.rooms.all()
        return RoomBasicSerializer(rooms, many=True).data
    
    def get_employees(self, obj) -> list[dict]:
        from accounts.serializers import EmployeeSerializer
        employees = obj.employees.all()
        return EmployeeSerializer(employees, many=True).data

    class Meta(PropertySerializer.Meta):
        fields = PropertySerializer.Meta.fields + ['rooms', 'employees']
