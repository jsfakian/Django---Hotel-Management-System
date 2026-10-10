"""
Core API ViewSets for NEPHELE HMS.
"""

from datetime import timedelta
from uuid import uuid4

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.api_permissions import HasRolePermission, IsHotelStaff, IsManagement, is_hotel_staff
from accounts.models import Employee, Guest
from accounts.permissions import has_permission
from accounts.serializers import EmployeeSerializer, GuestSerializer, UserSerializer
from bookings.models import PricingHistory
from contracts.models import Contract
from contracts.serializers import ContractDetailedSerializer, ContractSerializer
from notifications.models import Notification
from notifications.serializers import NotificationDetailedSerializer, NotificationSerializer
from payments.models import Invoice, Payment, PaymentMethod, RefundRequest
from payments.serializers import (
    InvoiceSerializer,
    PaymentDetailedSerializer,
    PaymentSerializer,
    RefundRequestSerializer,
)
from properties.models import Property, TravelAgency
from properties.serializers import (
    PropertyDetailSerializer,
    PropertySerializer,
    TravelAgencySerializer,
)
from room.models import Booking, Room
from room.serializers import (
    BookingDetailedSerializer,
    BookingSerializer,
    RoomBasicSerializer,
    RoomDetailedSerializer,
)


def _guest_for(user):
    return getattr(user, 'guest_profile', None)


def _can_manage_payments(user):
    return has_permission(user, 'process_payments') or has_permission(user, 'manage_payments')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    required_permission = 'manage_users'
    required_permission_map = {
        'list': 'manage_users',
        'retrieve': 'manage_users',
        'create': 'manage_users',
        'update': 'manage_users',
        'partial_update': 'manage_users',
        'destroy': 'manage_users',
    }

    def get_permissions(self):
        # Allow users to retrieve/update themselves without manage_users
        if self.action in ('retrieve', 'partial_update', 'update'):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if has_permission(user, 'manage_users') or user.is_superuser:
            queryset = self.queryset
            is_active = self.request.query_params.get('is_active')
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active.lower() == 'true')
            return queryset
        return User.objects.filter(pk=user.pk)

    def update(self, request, *args, **kwargs):
        if not has_permission(request.user, 'manage_users') and not request.user.is_superuser:
            if int(kwargs.get('pk')) != request.user.pk:
                return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.select_related('user').all().order_by('-created_at')
    serializer_class = GuestSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [IsAuthenticated(), IsHotelStaff()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if is_hotel_staff(user):
            queryset = self.queryset
            email = self.request.query_params.get('email')
            if email:
                queryset = queryset.filter(email__icontains=email)
            return queryset
        guest = _guest_for(user)
        if guest:
            return self.queryset.filter(pk=guest.pk)
        return self.queryset.none()

    @action(detail=True, methods=['put'], url_path='preferences')
    def update_preferences(self, request, pk=None):
        guest = self.get_object()
        if not is_hotel_staff(request.user):
            own = _guest_for(request.user)
            if not own or own.pk != guest.pk:
                return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        incoming_preferences = request.data if isinstance(request.data, dict) else {}
        guest.preferences = incoming_preferences
        guest.save(update_fields=['preferences', 'updated_at'])
        return Response({'message': 'Preferences updated', 'preferences': guest.preferences})


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.select_related('user', 'property').all().order_by('-created_at')
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsHotelStaff]

    def get_queryset(self):
        queryset = self.queryset
        status_filter = self.request.query_params.get('status')
        property_id = self.request.query_params.get('property_id')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        return queryset


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.select_related('manager').all()
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsManagement()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PropertyDetailSerializer
        return PropertySerializer


class TravelAgencyViewSet(viewsets.ModelViewSet):
    queryset = TravelAgency.objects.all()
    serializer_class = TravelAgencySerializer
    permission_classes = [IsAuthenticated, IsHotelStaff]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related('property').all()
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'pricing'):
            return [IsAuthenticated(), IsHotelStaff()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoomDetailedSerializer
        return RoomBasicSerializer

    def get_queryset(self):
        queryset = self.queryset
        property_id = self.request.query_params.get('property_id')
        status_filter = self.request.query_params.get('status')

        if property_id:
            queryset = queryset.filter(property_id=property_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

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
        try:
            days = int(request.query_params.get('days', 30))
        except (TypeError, ValueError):
            return Response({'detail': 'days must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        days = max(1, min(days, 365))
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

    def get_permissions(self):
        # Guests may create/list/retrieve; mutations of existing bookings are staff-only
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsHotelStaff()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BookingDetailedSerializer
        return BookingSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        if not is_hotel_staff(user):
            guest = _guest_for(user)
            if not guest:
                return queryset.none()
            queryset = queryset.filter(guest=guest)
        property_id = self.request.query_params.get('property_id')
        status_filter = self.request.query_params.get('status')
        guest_id = self.request.query_params.get('guest_id')

        if property_id and is_hotel_staff(user):
            queryset = queryset.filter(room__property_id=property_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if guest_id and is_hotel_staff(user):
            queryset = queryset.filter(guest_id=guest_id)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if is_hotel_staff(user):
            serializer.save()
            return
        guest = _guest_for(user)
        if not guest:
            raise PermissionDenied('Guest profile required')
        serializer.save(guest=guest, status='pending')

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
    permission_classes = [IsAuthenticated, IsHotelStaff]

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

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsHotelStaff()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailedSerializer
        return PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        if not is_hotel_staff(user):
            guest = _guest_for(user)
            if not guest:
                return queryset.none()
            return queryset.filter(guest=guest)

        status_filter = self.request.query_params.get('status')
        guest_id = self.request.query_params.get('guest_id')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if guest_id:
            queryset = queryset.filter(guest_id=guest_id)
        return queryset

    @action(detail=True, methods=['post'], url_path='verify')
    def verify(self, request, pk=None):
        """Verify a pending payment with the emailed verification code."""
        payment = self.get_object()
        code = (request.data.get('verification_code') or '').strip()
        if not code:
            return Response({'error': 'verification_code is required'}, status=status.HTTP_400_BAD_REQUEST)
        if payment.is_expired():
            payment.mark_as_failed('Verification code expired')
            return Response(
                {'error': 'Verification code has expired'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if payment.is_verified or payment.status == 'completed':
            invoice = getattr(payment, 'invoice', None)
            if invoice and invoice.status != 'paid':
                invoice.mark_as_paid()
            return Response({'message': 'Payment already verified', 'status': payment.status})
        if payment.verify(code):
            payment.refresh_from_db()
            invoice = getattr(payment, 'invoice', None)
            if invoice and invoice.status != 'paid':
                invoice.mark_as_paid()
            return Response({'message': 'Payment verified successfully', 'status': payment.status})
        return Response({'error': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Invoice.objects.select_related('guest', 'booking', 'payment').all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if is_hotel_staff(user):
            return self.queryset
        guest = _guest_for(user)
        if not guest:
            return self.queryset.none()
        return self.queryset.filter(guest=guest)

    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request, pk=None):
        """
        Record a payment against an invoice.

        Staff with process_payments may mark paid (demo path; gateway later).
        Guests may only create a pending payment on their own invoice.
        Amount is always taken from the invoice — never from the client.
        """
        invoice = self.get_object()
        if invoice.status == 'paid':
            return Response({'message': 'Invoice already paid'})

        linked = invoice.payment
        if linked and (linked.status in ('completed', 'processing') or linked.is_verified):
            if invoice.status != 'paid':
                invoice.mark_as_paid()
            return Response(
                {
                    'message': 'Invoice already paid',
                    'invoice_id': invoice.id,
                    'payment_id': linked.id,
                    'status': invoice.status,
                    'payment_status': linked.status,
                }
            )

        can_complete = _can_manage_payments(request.user)
        guest = _guest_for(request.user)
        if not can_complete:
            if not guest or invoice.guest_id != guest.id:
                return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        existing_pending = None
        if linked and linked.status == 'pending':
            existing_pending = linked
        else:
            existing_pending = Payment.objects.filter(
                guest=invoice.guest,
                status='pending',
                description__contains=str(invoice.invoice_number),
            ).first()

        # Guests: do not create duplicates; staff: complete the pending row instead
        if existing_pending and not can_complete:
            if not invoice.payment_id:
                invoice.payment = existing_pending
                invoice.save(update_fields=['payment'])
            from payments.views import send_verification_email

            # Always (re)send so a prior email failure cannot trap the guest
            code = existing_pending.generate_verification_code()
            sent = send_verification_email(existing_pending, code)
            if not sent:
                return Response(
                    {
                        'message': 'Payment pending but verification email failed',
                        'payment_id': existing_pending.id,
                        'payment_status': existing_pending.status,
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            return Response(
                {
                    'message': 'Payment already pending verification',
                    'payment_id': existing_pending.id,
                    'payment_status': existing_pending.status,
                }
            )

        if existing_pending and can_complete:
            existing_pending.status = 'completed'
            existing_pending.is_verified = True
            existing_pending.processed_at = timezone.now()
            existing_pending.amount = invoice.total_amount
            existing_pending.save(
                update_fields=['status', 'is_verified', 'processed_at', 'amount']
            )
            invoice.payment = existing_pending
            invoice.mark_as_paid()
            return Response(
                {
                    'message': 'Payment processed',
                    'invoice_id': invoice.id,
                    'payment_id': existing_pending.id,
                    'status': invoice.status,
                    'payment_status': existing_pending.status,
                }
            )

        payment_method_name = request.data.get('payment_method', 'card')
        payment_method, _ = PaymentMethod.objects.get_or_create(
            name=payment_method_name,
            defaults={'payment_type': 'card'},
        )

        payment_status = 'completed' if can_complete else 'pending'
        payment = Payment.objects.create(
            guest=invoice.guest,
            booking=invoice.booking,
            payment_method=payment_method,
            amount=invoice.total_amount,
            currency='EUR',
            status=payment_status,
            transaction_id=f"txn-{uuid4().hex}",
            reference_code=f"ref-{uuid4().hex[:12]}",
            processed_at=timezone.now() if can_complete else None,
            is_verified=bool(can_complete),
            description=f'Payment for invoice {invoice.invoice_number}',
        )

        invoice.payment = payment
        if can_complete:
            invoice.mark_as_paid()
        else:
            invoice.save(update_fields=['payment'])
            from payments.views import send_verification_email

            code = payment.generate_verification_code()
            sent = send_verification_email(payment, code)
            if not sent:
                return Response(
                    {
                        'message': 'Payment created but verification email failed',
                        'invoice_id': invoice.id,
                        'payment_id': payment.id,
                        'payment_status': payment.status,
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response(
            {
                'message': 'Payment processed' if can_complete else 'Payment pending verification',
                'invoice_id': invoice.id,
                'payment_id': payment.id,
                'status': invoice.status,
                'payment_status': payment.status,
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

    @action(detail=True, methods=['post'], url_path='mydata/transmit')
    def mydata_transmit(self, request, pk=None):
        """Transmit invoice to MyData (AADE). Requires payment management permission."""
        if not _can_manage_payments(request.user):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        from payments.mydata_service import get_mydata_service

        invoice = self.get_object()
        if getattr(invoice, 'mydata_transmitted', False):
            return Response({'message': 'Already transmitted', 'transmission_id': invoice.mydata_transmission_id})
        service = get_mydata_service()
        is_valid, validation_errors = service.validate_invoice_for_transmission(invoice)
        if not is_valid:
            return Response({'error': 'Validation failed', 'details': validation_errors}, status=400)
        success, result = service.transmit_invoice(invoice)
        if success:
            return Response({'message': 'Transmitted', 'transmission_id': result})
        return Response({'error': result}, status=400)

    @action(detail=True, methods=['get'], url_path='mydata/status')
    def mydata_status(self, request, pk=None):
        invoice = self.get_object()
        if not is_hotel_staff(request.user):
            guest = _guest_for(request.user)
            if not guest or invoice.guest_id != guest.id:
                return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                'invoice_number': invoice.invoice_number,
                'mydata_transmitted': getattr(invoice, 'mydata_transmitted', False),
                'transmission_id': getattr(invoice, 'mydata_transmission_id', None) or '',
                'transmission_date': (
                    invoice.mydata_transmission_date.isoformat()
                    if getattr(invoice, 'mydata_transmission_date', None)
                    else None
                ),
                'qr_code': getattr(invoice, 'mydata_qr_code', None) or '',
            }
        )

    @action(detail=False, methods=['post'], url_path='mydata/bulk-transmit')
    def mydata_bulk_transmit(self, request):
        if not _can_manage_payments(request.user):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        from payments.mydata_service import get_mydata_service

        results = get_mydata_service().bulk_transmit_invoices()
        return Response(results)


class RefundRequestViewSet(viewsets.ModelViewSet):
    queryset = RefundRequest.objects.select_related('payment', 'guest', 'processed_by').all()
    serializer_class = RefundRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if is_hotel_staff(user):
            return self.queryset
        guest = _guest_for(user)
        if not guest:
            return self.queryset.none()
        return self.queryset.filter(guest=guest)

    def perform_create(self, serializer):
        guest = _guest_for(self.request.user)
        payment = serializer.validated_data.get('payment')
        if is_hotel_staff(self.request.user):
            serializer.save()
            return
        if not guest:
            raise PermissionDenied('Guest profile required')
        if not payment or payment.guest_id != guest.id:
            raise PermissionDenied('Payment does not belong to this guest')
        serializer.save(guest=guest, status='pending')


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.select_related('notification_type', 'user').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NotificationDetailedSerializer
        return NotificationSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
