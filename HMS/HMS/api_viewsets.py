"""
Core API ViewSets for NEPHELE HMS.

Provides CRUD/read endpoints for core domain models so Task 4 API coverage
matches implementation claims.
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from uuid import uuid4

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
from accounts.models import Guest, Employee
from accounts.serializers import UserSerializer, GuestSerializer, EmployeeSerializer
from bookings.models import PricingHistory
from payments.models import PaymentMethod


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.select_related('user').all().order_by('-created_at')
    serializer_class = GuestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(email__icontains=email)
        return queryset

    @action(detail=True, methods=['put'], url_path='preferences')
    def update_preferences(self, request, pk=None):
        guest = self.get_object()
        incoming_preferences = request.data if isinstance(request.data, dict) else {}
        guest.preferences = incoming_preferences
        guest.save(update_fields=['preferences', 'updated_at'])
        return Response({'message': 'Preferences updated', 'preferences': guest.preferences})


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('user', 'property').all().order_by('-created_at')
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        status = self.request.query_params.get('status')
        property_id = self.request.query_params.get('property_id')
        if status:
            queryset = queryset.filter(status=status)
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        return queryset


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

    @action(detail=True, methods=['get'], url_path='availability')
    def availability(self, request, pk=None):
        room = self.get_object()
        check_in = request.query_params.get('check_in')
        check_out = request.query_params.get('check_out')

        overlapping_bookings = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed', 'checked_in'],
        )
        if check_in and check_out:
            overlapping_bookings = overlapping_bookings.filter(
                check_in_date__lt=check_out,
                check_out_date__gt=check_in,
            )

        is_available = overlapping_bookings.count() == 0
        return Response(
            {
                'room_id': room.id,
                'check_in': check_in,
                'check_out': check_out,
                'available': is_available,
                'current_price': room.current_price,
            }
        )

    @action(detail=True, methods=['get'], url_path='pricing-history')
    def pricing_history(self, request, pk=None):
        room = self.get_object()
        days = int(request.query_params.get('days', 30))
        from_date = timezone.now().date() - timedelta(days=days)

        rows = PricingHistory.objects.filter(
            room=room,
            date__gte=from_date,
        ).order_by('-date').values(
            'date',
            'base_price',
            'dynamic_price',
            'competitor_price',
            'occupancy_rate',
            'demand_score',
        )

        return Response({'room_id': room.id, 'days': days, 'history': list(rows)})

    @action(detail=True, methods=['put'], url_path='pricing')
    def pricing(self, request, pk=None):
        room = self.get_object()
        base_price = request.data.get('base_price')

        if base_price is not None:
            room.base_price = base_price
            room.current_price = base_price
            room.save(update_fields=['base_price', 'current_price', 'updated_at'])

        return Response(
            {
                'message': 'Pricing updated',
                'room_id': room.id,
                'base_price': room.base_price,
                'current_price': room.current_price,
            }
        )


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

    @action(detail=True, methods=['get'], url_path='timeline')
    def timeline(self, request, pk=None):
        booking = self.get_object()
        events = [
            {
                'timestamp': booking.created_at,
                'event_type': 'created',
                'description': 'Booking created',
            },
            {
                'timestamp': booking.updated_at,
                'event_type': 'status',
                'description': f'Booking status is {booking.status}',
            },
        ]
        return Response({'events': events})


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

    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request, pk=None):
        invoice = self.get_object()
        if invoice.status == 'paid':
            return Response({'message': 'Invoice already paid'})

        payment_method_name = request.data.get('payment_method', 'card')
        amount = request.data.get('amount') or invoice.total_amount

        payment_method, _ = PaymentMethod.objects.get_or_create(
            name=payment_method_name,
            defaults={'payment_type': 'card'},
        )

        payment = Payment.objects.create(
            guest=invoice.guest,
            booking=invoice.booking,
            payment_method=payment_method,
            amount=amount,
            currency='EUR',
            status='completed',
            transaction_id=f"txn-{uuid4().hex}",
            reference_code=f"ref-{uuid4().hex[:12]}",
            processed_at=timezone.now(),
            is_verified=True,
            description=f'Payment for invoice {invoice.invoice_number}',
        )

        invoice.payment = payment
        invoice.mark_as_paid()

        return Response(
            {
                'message': 'Payment processed',
                'invoice_id': invoice.id,
                'payment_id': payment.id,
                'status': invoice.status,
            }
        )

    @action(detail=True, methods=['get'], url_path='payment-status')
    def payment_status(self, request, pk=None):
        invoice = self.get_object()
        payment = getattr(invoice, 'payment', None)
        return Response(
            {
                'invoice_id': invoice.id,
                'invoice_status': invoice.status,
                'payment_status': payment.status if payment else 'unpaid',
                'paid_date': invoice.paid_date,
            }
        )


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
