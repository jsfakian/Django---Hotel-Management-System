"""
Serializers for payments app models

Per Task 4: Payment Processing & Invoice Management
"""

from rest_framework import serializers
from payments.models import (
    PaymentMethod, Payment, Invoice, RefundRequest, PaymentTransaction
)


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for PaymentMethod model"""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'payment_type', 'is_active',
            'requires_verification', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    guest_name = serializers.CharField(source='guest', read_only=True)
    booking_ref = serializers.CharField(source='booking.id', read_only=True, allow_null=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'guest', 'guest_name', 'booking', 'booking_ref',
            'amount', 'currency', 'status', 'payment_method',
            'payment_method_name', 'transaction_id', 'reference_code',
            'description', 'is_verified', 'created_at', 'processed_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'reference_code', 'created_at']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model"""
    
    guest_name = serializers.CharField(source='guest', read_only=True)
    booking_ref = serializers.CharField(source='booking.id', read_only=True, allow_null=True)
    days_until_due = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'guest', 'guest_name',
            'booking', 'booking_ref', 'amount', 'tax_amount',
            'total_amount', 'status', 'description',
            'issued_date', 'due_date', 'paid_date',
            'days_until_due', 'is_overdue', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'created_at', 'updated_at'
        ]
    
    def get_days_until_due(self, obj):
        from datetime import datetime, date
        delta = obj.due_date - date.today()
        return delta.days if delta.days > 0 else 0
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()


class RefundRequestSerializer(serializers.ModelSerializer):
    """Serializer for RefundRequest model"""
    
    guest_name = serializers.CharField(source='guest', read_only=True)
    payment_ref = serializers.CharField(source='payment.reference_code', read_only=True)
    processed_by_name = serializers.CharField(
        source='processed_by.get_full_name', read_only=True, allow_null=True
    )
    
    class Meta:
        model = RefundRequest
        fields = [
            'id', 'payment', 'payment_ref', 'guest', 'guest_name',
            'refund_amount', 'reason', 'description', 'status',
            'requested_at', 'approved_at', 'processed_at',
            'rejection_reason', 'processed_by', 'processed_by_name',
            'created_at'
        ]
        read_only_fields = [
            'id', 'requested_at', 'approved_at', 'processed_at', 'created_at'
        ]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for PaymentTransaction model"""
    
    payment_ref = serializers.CharField(source='payment.reference_code', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'payment', 'payment_ref', 'transaction_type',
            'amount', 'description', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class PaymentDetailedSerializer(PaymentSerializer):
    """Extended payment serializer with related transactions"""
    
    transactions = PaymentTransactionSerializer(many=True, read_only=True)
    invoice = InvoiceSerializer(read_only=True, allow_null=True)
    refund_request = RefundRequestSerializer(read_only=True, allow_null=True)
    
    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields + ['transactions', 'invoice', 'refund_request']
