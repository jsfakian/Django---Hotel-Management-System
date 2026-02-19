"""
Core API ViewSets for NEPHELE HMS.

Provides CRUD/read endpoints for core domain models so Task 4 API coverage
matches implementation claims.
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from properties.models import Property, TravelAgency
from properties.serializers import (
    PropertySerializer,
    PropertyDetailSerializer,
    TravelAgencySerializer,
)
from room.models import Room, Booking
from room.serializers import (
    RoomBasicSerializer,
    RoomDetailedSerializer,
    BookingSerializer,
    BookingDetailedSerializer,
)
from payments.models import Payment, Invoice, RefundRequest
from payments.serializers import (
    PaymentSerializer,
    PaymentDetailedSerializer,
    InvoiceSerializer,
    RefundRequestSerializer,
)
from contracts.models import Contract
from contracts.serializers import ContractSerializer, ContractDetailedSerializer
from notifications.models import Notification
from notifications.serializers import NotificationSerializer, NotificationDetailedSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.select_related('manager').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PropertyDetailSerializer
        return PropertySerializer


class TravelAgencyViewSet(viewsets.ModelViewSet):
    queryset = TravelAgency.objects.all()
    serializer_class = TravelAgencySerializer
    permission_classes = [IsAuthenticated]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related('property').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoomDetailedSerializer
        return RoomBasicSerializer

    def get_queryset(self):
        queryset = self.queryset
        property_id = self.request.query_params.get('property_id')
        status = self.request.query_params.get('status')

        if property_id:
            queryset = queryset.filter(property_id=property_id)
        if status:
            queryset = queryset.filter(status=status)

        return queryset


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('room', 'guest', 'travel_agency').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookingDetailedSerializer
        return BookingSerializer

    def get_queryset(self):
        queryset = self.queryset
        property_id = self.request.query_params.get('property_id')
        status = self.request.query_params.get('status')
        guest_id = self.request.query_params.get('guest_id')

        if property_id:
            queryset = queryset.filter(room__property_id=property_id)
        if status:
            queryset = queryset.filter(status=status)
        if guest_id:
            queryset = queryset.filter(guest_id=guest_id)

        return queryset


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.select_related('property', 'travel_agency', 'property_manager').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ContractDetailedSerializer
        return ContractSerializer

    @action(detail=True, methods=['post'])
    def sign_property(self, request, pk=None):
        contract = self.get_object()
        signature = request.data.get('signature', '')
        contract.sign_property(signature=signature, user=request.user)
        return Response({'status': 'property signature recorded'})

    @action(detail=True, methods=['post'])
    def sign_agency(self, request, pk=None):
        contract = self.get_object()
        signature = request.data.get('signature', '')
        contract.sign_agency(signature=signature)
        return Response({'status': 'agency signature recorded'})


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.select_related('guest', 'booking', 'payment_method').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailedSerializer
        return PaymentSerializer

    def get_queryset(self):
        queryset = self.queryset
        status = self.request.query_params.get('status')
        guest_id = self.request.query_params.get('guest_id')

        if status:
            queryset = queryset.filter(status=status)
        if guest_id:
            queryset = queryset.filter(guest_id=guest_id)

        return queryset


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Invoice.objects.select_related('guest', 'booking', 'payment').all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]


class RefundRequestViewSet(viewsets.ModelViewSet):
    queryset = RefundRequest.objects.select_related('payment', 'guest', 'processed_by').all()
    serializer_class = RefundRequestSerializer
    permission_classes = [IsAuthenticated]


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related('notification_type', 'user').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NotificationDetailedSerializer
        return NotificationSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'read'})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        notification = self.get_object()
        notification.status = 'archived'
        notification.save(update_fields=['status'])
        return Response({'status': 'archived'})
