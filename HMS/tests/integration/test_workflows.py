"""
Integration tests for complete workflows

Tests for:
- Booking workflow (list rooms -> create booking -> payment -> invoice)
- Payment processing (create payment -> verify -> reconcile)
- Notification integration (booking event -> email trigger)
"""

from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient

from room.models import Room, Booking
from payments.models import Payment, Invoice, PaymentMethod
from accounts.models import Guest
from properties.models import Property


class BookingWorkflowIntegrationTests(TransactionTestCase):
    """Integration tests for complete booking workflow"""
    
    def setUp(self):
        """Set up test data"""
        # Create property
        self.property = Property.objects.create(
            name='Integration Test Hotel',
            address='123 Integration St',
            city='Test City',
            country='Test Country',
            postal_code='54321',
            phone_number='+30-210-1234567',
            email='integration@hotel.com'
        )
        
        # Create multiple rooms
        self.rooms = []
        for i in range(1, 4):
            room = Room.objects.create(
                room_number=f'{i:03d}',
                floor=(i-1) // 2 + 1,
                room_type='double' if i % 2 == 0 else 'single',
                capacity=2 if i % 2 == 0 else 1,
                number_of_beds=1,
                base_price=Decimal('100.00') * i,
                current_price=Decimal('100.00') * i,
                property=self.property
            )
            self.rooms.append(room)
        
        # Create guest user
        self.user = User.objects.create_user(
            username='integration_guest',
            email='integration@guest.com',
            first_name='Integration',
            last_name='Guest'
        )
        
        self.guest = Guest.objects.create(
            user=self.user,
            email='integration@guest.com',
            first_name='Integration',
            last_name='Guest',
            phone_number='+30-210-9999999'
        )
        
        # Create payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
    
    def test_complete_booking_workflow(self):
        """Test complete booking workflow from search to invoice"""
        # Step 1: Search available rooms
        available_rooms = Room.objects.filter(
            property=self.property,
            status='available'
        )
        self.assertGreater(available_rooms.count(), 0)
        
        # Step 2: Select a room
        selected_room = available_rooms.first()
        self.assertIsNotNone(selected_room)
        
        # Step 3: Create booking
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=3)
        
        booking = Booking.objects.create(
            room=selected_room,
            guest=self.guest,
            check_in_date=check_in,
            check_out_date=check_out,
            number_of_guests=2,
            status='pending',
            base_price=Decimal('300.00')
        )
        
        self.assertEqual(booking.guest, self.guest)
        self.assertEqual(booking.status, 'pending')
        
        # Step 4: Process payment
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=booking.base_price,
            currency='EUR',
            transaction_id='TXN-INT-001',
            status='completed'
        )
        
        self.assertEqual(payment.amount, booking.base_price)
        self.assertEqual(payment.status, 'completed')
        
        # Step 5: Update booking status
        booking.status = 'confirmed'
        booking.payment_status = 'completed'
        booking.save()
        booking.refresh_from_db()
        # Step 6: Generate invoice
        tax_amount_val = booking.base_price * Decimal('0.20')
        total_amount_val = booking.base_price * Decimal('1.20')
        invoice = Invoice.objects.create(
            guest=self.guest,
            booking=booking,
            invoice_number='INV-INT-001',
            amount=booking.base_price,
            tax_amount=tax_amount_val,
            total_amount=total_amount_val,
            status='issued',
            description='Booking invoice',
            due_date=(timezone.now() + timedelta(days=30)).date()
        )
        
        self.assertEqual(invoice.booking, booking)
        self.assertGreater(invoice.total_amount, invoice.amount)
    
    def test_multiple_bookings_different_rooms_same_guest(self):
        """Test guest can book multiple rooms at different times"""
        guest_bookings = []
        
        for i, room in enumerate(self.rooms):
            check_in = timezone.now().date() + timedelta(days=i*5)
            check_out = check_in + timedelta(days=2)
            
            booking = Booking.objects.create(
                room=room,
                guest=self.guest,
                check_in_date=check_in,
                check_out_date=check_out,
                number_of_guests=1,
                status='confirmed',
                base_price=Decimal('200.00')
            )
            guest_bookings.append(booking)
        
        # Verify all bookings exist
        all_guest_bookings = Booking.objects.filter(guest=self.guest)
        self.assertEqual(all_guest_bookings.count(), len(guest_bookings))
    
    def test_booking_date_overlap_detection(self):
        """Test detection of overlapping bookings for same room"""
        check_in1 = timezone.now().date() + timedelta(days=1)
        check_out1 = check_in1 + timedelta(days=3)
        
        # First booking
        booking1 = Booking.objects.create(
            room=self.rooms[0],
            guest=self.guest,
            check_in_date=check_in1,
            check_out_date=check_out1,
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        # Second booking with overlap
        check_in2 = check_in1 + timedelta(days=1)
        check_out2 = check_in2 + timedelta(days=3)
        
        guest2_user = User.objects.create_user(
            username='guest2',
            email='guest2@test.com'
        )
        
        guest2 = Guest.objects.create(
            user=guest2_user,
            email='guest2@test.com',
            first_name='Another',
            last_name='Guest'
        )
        
        # Check for overlapping bookings
        overlapping = Booking.objects.filter(
            room=self.rooms[0],
            check_in_date__lt=check_out2,
            check_out_date__gt=check_in2,
            status__in=['confirmed', 'checked_in']
        )
        
        self.assertEqual(overlapping.count(), 1)


class PaymentIntegrationTests(TransactionTestCase):
    """Integration tests for payment processing workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='payment_user',
            email='payment@test.com'
        )
        
        self.guest = Guest.objects.create(
            user=self.user,
            email='payment@test.com',
            first_name='Payment',
            last_name='User'
        )
        
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
    
    def test_complete_payment_workflow(self):
        """Test complete payment workflow"""
        # Step 1: Create payment
        amount = Decimal('150.00')
        
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=amount,
            currency='EUR',
            transaction_id='TXN-PAY-001',
            status='pending'
        )
        
        self.assertEqual(payment.status, 'pending')
        
        # Step 2: Process payment (simulate gateway)
        payment.status = 'completed'
        payment.save()
        payment.refresh_from_db()
        
        self.assertEqual(payment.status, 'completed')
    
    def test_payment_refund_workflow(self):
        """Test payment refund workflow"""
        from payments.models import RefundRequest
        
        # Create and complete payment
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-REFUND-001',
            status='completed'
        )
        
        # Create refund request
        refund = RefundRequest.objects.create(
            payment=payment,
            guest=self.guest,
            refund_amount=Decimal('100.00'),
            reason='cancellation',
            description='Guest cancellation',
            status='pending'
        )
        
        self.assertEqual(refund.status, 'pending')
        
        # Process refund
        refund.status = 'processed'
        refund.save()
        refund.refresh_from_db()
        
        self.assertEqual(refund.status, 'processed')
        
        # Update payment status
        payment.status = 'refunded'
        payment.save()
        payment.refresh_from_db()
        
        self.assertEqual(payment.status, 'refunded')
    
    def test_payment_transaction_logging(self):
        """Test payment transaction logging"""
        from payments.models import PaymentTransaction
        
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-LOG-001'
        )
        
        # Log charge transaction
        charge_txn = PaymentTransaction.objects.create(
            payment=payment,
            transaction_type='payment',
            amount=Decimal('100.00'),
            description='Payment transaction log'
        )
        
        self.assertEqual(charge_txn.transaction_type, 'payment')
        self.assertIsNotNone(charge_txn.timestamp)


class InvoiceIntegrationTests(TransactionTestCase):
    """Integration tests for invoice generation and management"""
    
    def setUp(self):
        """Set up test data"""
        self.property = Property.objects.create(
            name='Invoice Test Hotel',
            address='123 Invoice St',
            city='Test City',
            country='Test Country',
            postal_code='54321',
            phone_number='+30-210-1234567',
            email='invoice@hotel.com'
        )
        
        self.room = Room.objects.create(
            room_number='001',
            floor=1,
            room_type='double',
            capacity=2,
            number_of_beds=1,
            base_price=Decimal('100.00'),
            current_price=Decimal('100.00'),
            property=self.property
        )
        
        self.user = User.objects.create_user(
            username='invoice_user',
            email='invoice@test.com'
        )
        
        self.guest = Guest.objects.create(
            user=self.user,
            email='invoice@test.com',
            first_name='Invoice',
            last_name='User'
        )
        
        self.booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=timezone.now().date() + timedelta(days=1),
            check_out_date=timezone.now().date() + timedelta(days=4),
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
    
    def test_invoice_generation_from_booking(self):
        """Test invoice generation from booking"""
        tax_amount_val = self.booking.base_price * Decimal('0.20')
        total_amount_val = self.booking.base_price * Decimal('1.20')
        invoice = Invoice.objects.create(
            guest=self.guest,
            booking=self.booking,
            invoice_number='INV-GEN-001',
            amount=self.booking.base_price,
            tax_amount=tax_amount_val,
            total_amount=total_amount_val,
            status='issued',
            description='Booking invoice',
            due_date=(timezone.now() + timedelta(days=30)).date()
        )
        
        self.assertEqual(invoice.booking, self.booking)
        self.assertGreater(invoice.total_amount, invoice.amount)
    
    def test_invoice_payment_status_tracking(self):
        """Test invoice payment status tracking"""
        tax_amount_val = Decimal('60.00')
        total_amount_val = Decimal('360.00')
        invoice = Invoice.objects.create(
            guest=self.guest,
            booking=self.booking,
            invoice_number='INV-PAY-001',
            amount=Decimal('300.00'),
            tax_amount=tax_amount_val,
            total_amount=total_amount_val,
            status='issued',
            description='Booking invoice',
            due_date=(timezone.now() + timedelta(days=30)).date()
        )
        
        # Simulate payment
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=PaymentMethod.objects.create(
                name='Check',
                payment_type='check',
                is_active=True
            ),
            amount=invoice.total_amount,
            reference_code='REF-INV-001',
            transaction_id='TXN-INV-001',
            status='completed'
        )
        
        # Update invoice status
        invoice.status = 'paid'
        invoice.save()
        invoice.refresh_from_db()
        
        self.assertEqual(invoice.status, 'paid')
    
    def test_invoice_discount_calculation(self):
        """Test invoice with discount calculation"""
        base_amount = Decimal('300.00')
        tax_amount_val = base_amount * Decimal('0.20')
        total_amount_val = base_amount + tax_amount_val
        
        invoice = Invoice.objects.create(
            guest=self.guest,
            booking=self.booking,
            invoice_number='INV-DISC-001',
            amount=base_amount,
            tax_amount=tax_amount_val,
            total_amount=total_amount_val,
            status='issued',
            description='Booking invoice with tax',
            due_date=(timezone.now() + timedelta(days=30)).date()
        )
        
        self.assertEqual(invoice.amount, base_amount)
        self.assertEqual(invoice.total_amount, total_amount_val)


class NotificationIntegrationTests(TestCase):
    """Integration tests for notification workflows"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='notif_user',
            email='notif@test.com'
        )
    
    def test_booking_confirmation_notification(self):
        """Test notification triggered on booking confirmation"""
        try:
            from notifications.models import (
                NotificationType, Notification, NotificationPreference
            )
            
            # Create notification type
            notif_type = NotificationType.objects.create(
                code='booking_confirmed',
                name='Booking Confirmed',
                description='Sent when booking is confirmed'
            )
            
            # Create preferences
            preference = NotificationPreference.objects.create(
                user=self.user,
                receive_in_app=True,
                receive_email=True
            )
            
            # Create booking confirmation notification
            notification = Notification.objects.create(
                user=self.user,
                notification_type=notif_type,
                title='Booking Confirmed',
                message='Your booking has been confirmed',
                priority='high'
            )
            
            self.assertEqual(notification.user, self.user)
            self.assertEqual(notification.notification_type, notif_type)
        except ImportError:
            self.skipTest("Notification models not available")
    
    def test_payment_completion_notification(self):
        """Test notification triggered on payment completion"""
        try:
            from notifications.models import (
                NotificationType, Notification
            )
            
            notif_type = NotificationType.objects.create(
                code='payment_received',
                name='Payment Received',
                description='Sent when payment is received'
            )
            
            notification = Notification.objects.create(
                user=self.user,
                notification_type=notif_type,
                title='Payment Received',
                message='Payment of EUR 100.00 has been received',
                priority='medium'
            )
            
            self.assertEqual(notification.notification_type, notif_type)
        except ImportError:
            self.skipTest("Notification models not available")
    
    def test_notification_channel_selection(self):
        """Test notification delivery channel selection"""
        try:
            from notifications.models import (
                NotificationType, Notification, NotificationPreference
            )
            
            notif_type = NotificationType.objects.create(
                code='test_channel',
                name='Test Channel',
                description='Test notification channels'
            )
            
            # Create preferences with different channels
            preference = NotificationPreference.objects.create(
                user=self.user,
                receive_in_app=True,
                receive_email=True,
                receive_sms=False
            )
            
            notification = Notification.objects.create(
                user=self.user,
                notification_type=notif_type,
                title='Multi-channel Test',
                message='Test message'
            )
            
            # Verify notification channels
            self.assertTrue(preference.receive_in_app)
            self.assertTrue(preference.receive_email)
            self.assertFalse(preference.receive_sms)
        except ImportError:
            self.skipTest("Notification models not available")
