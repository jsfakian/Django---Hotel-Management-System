"""
Unit tests for Payment and Invoice models

Tests for Payment, Invoice, PaymentMethod, and RefundRequest models
"""

from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from payments.models import Payment, Invoice, PaymentMethod, RefundRequest, PaymentTransaction
from room.models import Room, Booking
from accounts.models import Guest
from properties.models import Property


class PaymentMethodModelTests(TestCase):
    """Test cases for PaymentMethod model"""
    
    def test_payment_method_creation(self):
        """Test creating a payment method"""
        method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        self.assertEqual(method.name, 'Credit Card')
        self.assertEqual(method.payment_type, 'card')
        self.assertTrue(method.is_active)
    
    def test_payment_method_types(self):
        """Test various payment method types"""
        methods = [
            ('card', 'Credit Card'),
            ('bank_transfer', 'Bank Transfer'),
            ('cash', 'Cash'),
            ('check', 'Check')
        ]
        
        for ptype, name in methods:
            method = PaymentMethod.objects.create(
                name=name,
                payment_type=ptype,
                is_active=True
            )
            self.assertEqual(method.payment_type, ptype)


class PaymentModelTests(TestCase):
    """Test cases for Payment model"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and guest
        self.user = User.objects.create_user(
            username='testguest',
            email='guest@test.com'
        )
        
        self.guest = Guest.objects.create(
            user=self.user,
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        # Create payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
    
    def test_payment_creation_with_valid_data(self):
        """Test creating a payment with valid data"""
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-12345',
            reference_code='REF-12345'
        )
        
        self.assertEqual(payment.amount, Decimal('100.00'))
        self.assertEqual(payment.currency, 'EUR')
        self.assertEqual(payment.transaction_id, 'TXN-12345')
    
    def test_payment_amount_validation(self):
        """Test payment amount is positive"""
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('50.00'),
            currency='EUR',
            transaction_id='TXN-12346',
            reference_code='REF-12346'
        )
        
        self.assertGreater(payment.amount, 0)
    
    def test_payment_status_transitions(self):
        """Test payment status field"""
        statuses = ['pending', 'completed', 'failed', 'refunded']
        
        for status in statuses:
            payment = Payment.objects.create(
                guest=self.guest,
                payment_method=self.payment_method,
                amount=Decimal('100.00'),
                currency='EUR',
                transaction_id=f'TXN-{status}',
                reference_code=f'REF-{status}',
                status=status
            )
            self.assertEqual(payment.status, status)
    
    def test_payment_currency_field(self):
        """Test payment currency field"""
        currencies = ['EUR', 'GBP', 'USD', 'JPY']
        
        for currency in currencies:
            payment = Payment.objects.create(
                guest=self.guest,
                payment_method=self.payment_method,
                amount=Decimal('100.00'),
                currency=currency,
                transaction_id=f'TXN-{currency}',
                reference_code=f'REF-{currency}'
            )
            self.assertEqual(payment.currency, currency)
    
    def test_payment_timestamps(self):
        """Test payment timestamps"""
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-12347',
            reference_code='REF-12347'
        )
        
        self.assertIsNotNone(payment.created_at)
        self.assertIsNotNone(payment.updated_at)


class InvoiceModelTests(TestCase):
    """Test cases for Invoice model"""
    
    def setUp(self):
        """Set up test data"""
        # Create property
        self.property = Property.objects.create(
            name='Test Hotel',
            address='123 Test St',
            city='Test City',
            country='Test Country',
            postal_code='12345',
            phone_number='+30-210-1234567',
            email='test@hotel.com'
        )
        
        # Create room
        self.room = Room.objects.create(
            room_number='101',
            floor=1,
            room_type='double',
            capacity=2,
            number_of_beds=1,
            base_price=Decimal('100.00'),
            current_price=Decimal('100.00'),
            property=self.property
        )
        
        # Create user and guest
        self.user = User.objects.create_user(
            username='testguest',
            email='guest@test.com'
        )
        
        self.guest = Guest.objects.create(
            user=self.user,
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        # Create booking
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=3)
        
        self.booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=check_in,
            check_out_date=check_out,
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        # Create payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
    
    def test_invoice_creation_with_valid_data(self):
        """Test creating an invoice with valid data"""
        from datetime import timedelta
        
        due_date = timezone.now().date() + timedelta(days=30)
        
        invoice = Invoice.objects.create(
            guest=self.guest,
            booking=self.booking,
            invoice_number='INV-001',
            amount=Decimal('300.00'),
            tax_amount=Decimal('60.00'),
            total_amount=Decimal('360.00'),
            due_date=due_date,
            description='Test invoice'
        )
        
        self.assertEqual(invoice.guest, self.guest)
        self.assertEqual(invoice.booking, self.booking)
        self.assertEqual(invoice.invoice_number, 'INV-001')
        self.assertEqual(invoice.total_amount, Decimal('360.00'))
    
    def test_invoice_number_unique_constraint(self):
        """Test that invoice number must be unique"""
        from datetime import timedelta
        
        due_date = timezone.now().date() + timedelta(days=30)
        
        Invoice.objects.create(
            guest=self.guest,
            booking=self.booking,
            invoice_number='INV-UNIQUE',
            amount=Decimal('300.00'),
            tax_amount=Decimal('60.00'),
            total_amount=Decimal('360.00'),
            due_date=due_date,
            description='First invoice'
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            Invoice.objects.create(
                guest=self.guest,
                booking=self.booking,
                invoice_number='INV-UNIQUE',
                amount=Decimal('300.00'),
                tax_amount=Decimal('60.00'),
                total_amount=Decimal('360.00'),
                due_date=due_date,
                description='Duplicate invoice'
            )
    
    def test_invoice_calculation_fields(self):
        """Test invoice calculation fields"""
        from datetime import timedelta
        
        due_date = timezone.now().date() + timedelta(days=30)
        
        invoice = Invoice.objects.create(
            guest=self.guest,
            booking=self.booking,
            invoice_number='INV-002',
            amount=Decimal('300.00'),
            tax_amount=Decimal('60.00'),
            total_amount=Decimal('360.00'),
            due_date=due_date,
            description='Test calculation'
        )
        
        self.assertEqual(invoice.amount, Decimal('300.00'))
        self.assertEqual(invoice.tax_amount, Decimal('60.00'))
        self.assertEqual(invoice.total_amount, Decimal('360.00'))
    
    def test_invoice_status_field(self):
        """Test invoice status field"""
        from datetime import timedelta
        
        due_date = timezone.now().date() + timedelta(days=30)
        statuses = ['draft', 'issued', 'paid', 'partially_paid', 'overdue', 'cancelled']
        
        for idx, status in enumerate(statuses):
            invoice = Invoice.objects.create(
                guest=self.guest,
                booking=self.booking,
                invoice_number=f'INV-{idx:03d}',
                amount=Decimal('300.00'),
                tax_amount=Decimal('60.00'),
                total_amount=Decimal('360.00'),
                due_date=due_date,
                status=status,
                description=f'Invoice {idx}'
            )
            self.assertEqual(invoice.status, status)
    
    def test_invoice_due_date(self):
        """Test invoice due date field"""
        due_date = timezone.now().date() + timedelta(days=30)
        
        invoice = Invoice.objects.create(
            guest=self.guest,
            booking=self.booking,
            invoice_number='INV-003',
            amount=Decimal('300.00'),
            tax_amount=Decimal('60.00'),
            total_amount=Decimal('360.00'),
            due_date=due_date,
            description='Test invoice with due date'
        )
        
        self.assertEqual(invoice.due_date, due_date)
    
    def test_invoice_timestamps(self):
        """Test invoice timestamps"""
        due_date = timezone.now().date() + timedelta(days=30)
        
        invoice = Invoice.objects.create(
            guest=self.guest,
            booking=self.booking,
            invoice_number='INV-004',
            amount=Decimal('300.00'),
            tax_amount=Decimal('60.00'),
            total_amount=Decimal('360.00'),
            due_date=due_date,
            description='Test timestamps'
        )
        
        self.assertIsNotNone(invoice.created_at)
        self.assertIsNotNone(invoice.updated_at)


class RefundRequestModelTests(TestCase):
    """Test cases for RefundRequest model"""
    
    def setUp(self):
        """Set up test data"""
        # Create payment
        self.user = User.objects.create_user(
            username='testguest',
            email='guest@test.com'
        )
        
        self.guest = Guest.objects.create(
            user=self.user,
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        self.payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-12345'
        )
    
    def test_refund_request_creation(self):
        """Test creating a refund request"""
        refund = RefundRequest.objects.create(
            payment=self.payment,
            guest=self.guest,
            refund_amount=Decimal('100.00'),
            reason='cancellation',
            description='Guest requested cancellation',
            status='pending'
        )
        
        self.assertEqual(refund.payment, self.payment)
        self.assertEqual(refund.refund_amount, Decimal('100.00'))
        self.assertEqual(refund.reason, 'cancellation')
    
    def test_refund_status_transitions(self):
        """Test refund status field"""
        statuses = ['pending', 'approved', 'rejected', 'processed', 'cancelled']
        
        for status in statuses:
            refund = RefundRequest.objects.create(
                payment=self.payment,
                guest=self.guest,
                refund_amount=Decimal('50.00'),
                reason='cancellation',
                description=f'Refund {status}',
                status=status
            )
            self.assertEqual(refund.status, status)


class PaymentTransactionModelTests(TestCase):
    """Test cases for PaymentTransaction model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testguest',
            email='guest@test.com'
        )
        
        self.guest = Guest.objects.create(
            user=self.user,
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        self.payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-12345'
        )
    
    def test_payment_transaction_creation(self):
        """Test creating a payment transaction"""
        transaction = PaymentTransaction.objects.create(
            payment=self.payment,
            transaction_type='payment',
            amount=Decimal('100.00'),
            description='Payment transaction for booking'
        )
        
        self.assertEqual(transaction.payment, self.payment)
        self.assertEqual(transaction.transaction_type, 'payment')
        self.assertEqual(transaction.amount, Decimal('100.00'))
    
    def test_payment_transaction_types(self):
        """Test various transaction types"""
        types = ['payment', 'refund', 'adjustment', 'fee']
        
        for ttype in types:
            transaction = PaymentTransaction.objects.create(
                payment=self.payment,
                transaction_type=ttype,
                amount=Decimal('100.00'),
                description=f'{ttype} transaction'
            )
            self.assertEqual(transaction.transaction_type, ttype)
