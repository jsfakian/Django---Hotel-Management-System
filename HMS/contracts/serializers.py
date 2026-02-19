"""
Serializers for contracts app models

Per Task 4: Contract Management & Travel Agency Agreements
"""

from rest_framework import serializers
from contracts.models import Contract


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for Contract model"""
    
    property_name = serializers.CharField(source='property.name', read_only=True)
    travel_agency_name = serializers.CharField(source='travel_agency.name', read_only=True)
    manager_name = serializers.CharField(
        source='property_manager.get_full_name', read_only=True, allow_null=True
    )
    is_active = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = Contract
        fields = [
            'id', 'property', 'property_name', 'travel_agency',
            'travel_agency_name', 'contract_type', 'status',
            'allocation_percentage', 'allocated_rooms',
            'commission_percentage', 'payment_terms',
            'cancellation_policy', 'special_terms',
            'start_date', 'end_date', 'days_until_expiry',
            'is_active', 'is_expired',
            'property_manager', 'manager_name',
            'property_manager_signed_at', 'travel_agency_signed_at',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'property_manager_signed_at',
            'travel_agency_signed_at', 'created_at', 'updated_at'
        ]
    
    def get_is_active(self, obj) -> bool:
        """Check if contract is currently active"""
        return obj.is_active()
    
    def get_is_expired(self, obj) -> bool:
        """Check if contract has expired"""
        return obj.is_expired()
    
    def get_days_until_expiry(self, obj) -> int:
        """Calculate days until expiry"""
        from datetime import date
        delta = obj.end_date - date.today()
        return delta.days if delta.days > 0 else 0


class ContractDetailedSerializer(ContractSerializer):
    """Extended contract serializer with document data"""
    
    document_url = serializers.SerializerMethodField()
    bookings_count = serializers.SerializerMethodField()
    
    class Meta(ContractSerializer.Meta):
        fields = ContractSerializer.Meta.fields + [
            'contract_text', 'document_file', 'document_url',
            'property_manager_signature', 'travel_agency_signature',
            'bookings_count'
        ]
    
    def get_document_url(self, obj) -> str | None:
        if obj.document_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document_file.url)
        return None
    
    def get_bookings_count(self, obj) -> int:
        """Count bookings made through this contract"""
        from room.models import Booking
        return Booking.objects.filter(
            travel_agency=obj.travel_agency,
            room__property=obj.property
        ).count()


class ContractSignSerializer(serializers.Serializer):
    """Serializer for signing contracts"""
    
    signature = serializers.CharField(max_length=255)
    password = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Password for verification"
    )

