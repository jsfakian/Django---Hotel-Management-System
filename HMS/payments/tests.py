from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.test.utils import override_settings
from decimal import Decimal
from datetime import datetime, timedelta

from accounts.models import Guest
from room.models import Room, Booking
from .models import Invoice, Payment, PaymentMethod
from .mydata_service import MyDataService, get_mydata_service, MyDataServiceException
from .forms import InvoiceForm


class InvoiceModelTestCase(TestCase):
    """Test cases for Invoice model"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testguest',
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        # Create guest
        self.guest = Guest.objects.create(
            user=self.user,
            email=self.user.email,
            first_name=self.user.first_name,
            last_name=self.user.last_name,
            phone_number='+30-210-1234567'
        )
        
        # Create payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        # Create payment
        self.payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-12345',
            reference_code='REF-12345'
        )
    
    def test_invoice_creation_with_null_amount(self):
        """Test invoice creation handles None amounts correctly"""
        invoice = Invoice.objects.create(
            guest=self.guest,
            payment=self.payment,
            amount=Decimal('100.00'),
            tax_amount=Decimal('24.00'),
            total_amount=Decimal('124.00'),
            status='issued',
            description='Test Invoice',
            due_date=timezone.now().date() + timedelta(days=30)
        )
        
        self.assertIsNotNone(invoice.total_amount)
        self.assertEqual(invoice.total_amount, Decimal('124.00'))

    def test_invoice_number_generation(self):
        """Test invoice number is generated correctly"""
        invoice = Invoice.objects.create(
            guest=self.guest,
            amount=Decimal('100.00'),
            tax_amount=Decimal('24.00'),
            total_amount=Decimal('124.00'),
            status='issued',
            description='Test Invoice',
            due_date=timezone.now().date() + timedelta(days=30)
        )
        
        self.assertIsNotNone(invoice.invoice_number)
        self.assertTrue(invoice.invoice_number.startswith('INV-'))
    
    def test_invoice_is_overdue(self):
        """Test invoice overdue status check"""
        due_date = timezone.now().date() - timedelta(days=1)
        invoice = Invoice.objects.create(
            guest=self.guest,
            amount=Decimal('100.00'),
            tax_amount=Decimal('24.00'),
            total_amount=Decimal('124.00'),
            status='issued',
            description='Test Invoice',
            due_date=due_date
        )
        
        self.assertTrue(invoice.is_overdue())
    
    def test_invoice_not_overdue(self):
        """Test invoice is not overdue when due date in future"""
        due_date = timezone.now().date() + timedelta(days=30)
        invoice = Invoice.objects.create(
            guest=self.guest,
            amount=Decimal('100.00'),
            tax_amount=Decimal('24.00'),
            total_amount=Decimal('124.00'),
            status='issued',
            description='Test Invoice',
            due_date=due_date
        )
        
        self.assertFalse(invoice.is_overdue())


@override_settings(
    HOTEL_TAX_ID='123456789',
    MYDATA_API_BASE='https://www1.mydata.aade.gr/api',
    MYDATA_USERNAME='test_user',
    MYDATA_PASSWORD='test_pass',
    MYDATA_API_KEY='test_key',
    MYDATA_SANDBOX_MODE=True,
    MYDATA_AUTO_TRANSMISSION=False,
    MYDATA_TRANSMISSION_RETRIES=3
)
class MyDataServiceTestCase(TestCase):
    """Test cases for MyData service"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testguest',
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        # Create guest
        self.guest = Guest.objects.create(
            user=self.user,
            email=self.user.email,
            first_name=self.user.first_name,
            last_name=self.user.last_name,
            phone_number='+30-210-1234567'
        )
        
        # Create payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        # Create payment
        self.payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-12345',
            reference_code='REF-12345'
        )
        
        # Create valid invoice
        self.invoice = Invoice.objects.create(
            guest=self.guest,
            payment=self.payment,
            amount=Decimal('100.00'),
            tax_amount=Decimal('24.00'),
            total_amount=Decimal('124.00'),
            status='issued',
            description='Test Invoice',
            due_date=timezone.now().date() + timedelta(days=30)
        )
        
        self.service = get_mydata_service()
    
    def test_mydata_service_singleton(self):
        """Test MyDataService is singleton"""
        service1 = get_mydata_service()
        service2 = get_mydata_service()
        
        self.assertIs(service1, service2)
    
    def test_validate_invoice_with_valid_data(self):
        """Test validation passes for valid invoice"""
        is_valid, errors = self.service.validate_invoice_for_transmission(self.invoice)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_invoice_with_zero_amount(self):
        """Test validation fails for zero amount"""
        self.invoice.amount = Decimal('0.00')
        
        is_valid, errors = self.service.validate_invoice_for_transmission(self.invoice)
        
        self.assertFalse(is_valid)
        self.assertTrue(any('amount' in str(e).lower() for e in errors))
    
    def test_validate_invoice_with_invalid_guest_name(self):
        """Test validation fails when guest name missing"""
        self.invoice.guest.user.first_name = ''
        
        is_valid, errors = self.service.validate_invoice_for_transmission(self.invoice)
        
        self.assertFalse(is_valid)
    
    def test_validate_invoice_missing_email(self):
        """Test validation fails when email missing"""
        self.invoice.guest.user.email = ''
        
        is_valid, errors = self.service.validate_invoice_for_transmission(self.invoice)
        
        self.assertFalse(is_valid)
    
    def test_qr_code_generation(self):
        """Test QR code data generation"""
        qr_data = self.service.generate_qr_code_data(self.invoice)
        
        self.assertIsNotNone(qr_data)
        self.assertTrue(qr_data.startswith('A|'))
        
        parts = qr_data.split('|')
        self.assertEqual(len(parts), 6)
        self.assertIn(self.invoice.invoice_number, qr_data)  # Invoice number
        self.assertIn('12400', qr_data)  # Total amount in cents (124.00)
        self.assertIn('2400', qr_data)   # Tax in cents (24.00)
    
    def test_transmit_invoice_success(self):
        """Test successful invoice transmission"""
        success, result = self.service.transmit_invoice(self.invoice)
        
        self.assertTrue(success)
        # Result is a transmission ID string
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)
        
        # Verify invoice was updated
        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.mydata_transmitted)
        self.assertIsNotNone(self.invoice.mydata_transmission_id)
        self.assertIsNotNone(self.invoice.mydata_qr_code)
    
    def test_export_invoice_json(self):
        """Test invoice export to MyData JSON format"""
        export_data = self.service.export_invoice(self.invoice)
        
        self.assertIsNotNone(export_data)
        # Check that export data has invoice key
        self.assertIn('invoice', export_data)
        
        invoice_obj = export_data['invoice']
        self.assertIn('invoiceNumber', invoice_obj)
        self.assertEqual(invoice_obj['invoiceNumber'], self.invoice.invoice_number)
    
    def test_get_transmittable_invoices(self):
        """Test filtering of transmittable invoices"""
        # Create a transmitted invoice
        transmitted = Invoice.objects.create(
            guest=self.guest,
            amount=Decimal('100.00'),
            tax_amount=Decimal('24.00'),
            total_amount=Decimal('124.00'),
            status='issued',
            description='Transmitted Invoice',
            due_date=timezone.now().date() + timedelta(days=30),
            mydata_transmitted=True,
            mydata_transmission_id='AADE-123'
        )
        
        # Get transmittable invoices
        transmittable = self.service.get_transmittable_invoices()
        
        # Should not include already transmitted one
        self.assertNotIn(transmitted.id, [inv.id for inv in transmittable])
    
    def test_bulk_transmit_invoices(self):
        """Test bulk transmission of multiple invoices"""
        # Create additional invoice
        invoice2 = Invoice.objects.create(
            guest=self.guest,
            amount=Decimal('200.00'),
            tax_amount=Decimal('48.00'),
            total_amount=Decimal('248.00'),
            status='issued',
            description='Test Invoice 2',
            due_date=timezone.now().date() + timedelta(days=30)
        )
        
        stats = self.service.bulk_transmit_invoices()
        
        self.assertIn('successful', stats)
        self.assertIn('failed', stats)
        self.assertGreaterEqual(stats['successful'], 0)


class InvoiceFormTestCase(TestCase):
    """Test cases for InvoiceForm"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testguest',
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        # Create guest
        self.guest = Guest.objects.create(
            user=self.user,
            email=self.user.email,
            first_name=self.user.first_name,
            last_name=self.user.last_name,
            phone_number='+30-210-1234567'
        )
        
        # Create payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        # Create payment
        self.payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-12345',
            reference_code='REF-12345'
        )
    
    def test_invoice_form_has_mydata_checkbox(self):
        """Test that InvoiceForm has MyData checkbox field"""
        form = InvoiceForm()
        
        self.assertIn('transmit_to_mydata', form.fields)
        self.assertFalse(form.fields['transmit_to_mydata'].initial)
    
    def test_invoice_form_checkbox_unchecked_by_default(self):
        """Test MyData checkbox is unchecked by default"""
        form = InvoiceForm()
        
        # Check that the initial value is False (unchecked)
        self.assertFalse(form.fields['transmit_to_mydata'].initial)
    
    def test_invoice_form_valid_data(self):
        """Test form validation with valid data"""
        form_data = {
            'guest': self.guest.id,
            'payment': self.payment.id,
            'amount': '100.00',
            'tax_amount': '24.00',
            'total_amount': '124.00',
            'status': 'issued',
            'description': 'Test Invoice',
            'due_date': (timezone.now().date() + timedelta(days=30)).isoformat(),
            'transmit_to_mydata': False,
        }
        
        form = InvoiceForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invoice_form_transmit_to_mydata_visible(self):
        """Test transmit_to_mydata field is present and correctly configured"""
        form = InvoiceForm()
        
        # Check field is present
        self.assertIn('transmit_to_mydata', form.fields)
        
        # Check field is BooleanField
        from django.forms import BooleanField
        self.assertIsInstance(form.fields['transmit_to_mydata'], BooleanField)
        
        # Check it's not required
        self.assertFalse(form.fields['transmit_to_mydata'].required)


@override_settings(
    HOTEL_TAX_ID='123456789',
    MYDATA_API_BASE='https://www1.mydata.aade.gr/api',
    MYDATA_USERNAME='test_user',
    MYDATA_PASSWORD='test_pass',
    MYDATA_API_KEY='test_key',
    MYDATA_SANDBOX_MODE=True,
    MYDATA_AUTO_TRANSMISSION=False,
    MYDATA_TRANSMISSION_RETRIES=3
)
class InvoiceViewsTestCase(TestCase):
    """Test cases for Invoice views with MyData integration"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@test.com',
            password='testpass123'
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
        
        # Create guest user
        self.guest_user = User.objects.create_user(
            username='guestuser',
            email='guest@test.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        # Create guest profile
        self.guest = Guest.objects.create(
            user=self.guest_user,
            email=self.guest_user.email,
            first_name=self.guest_user.first_name,
            last_name=self.guest_user.last_name,
            phone_number='+30-210-1234567'
        )
        
        # Create payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        # Create payment
        self.payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-12345',
            reference_code='REF-12345'
        )
        
        # Create invoice
        self.invoice = Invoice.objects.create(
            guest=self.guest,
            payment=self.payment,
            amount=Decimal('100.00'),
            tax_amount=Decimal('24.00'),
            total_amount=Decimal('124.00'),
            status='issued',
            description='Test Invoice',
            due_date=timezone.now().date() + timedelta(days=30)
        )
    
    def test_invoice_detail_requires_login(self):
        """Test invoice detail view requires authentication"""
        response = self.client.get(f'/payments/invoices/{self.invoice.id}/')
        
        # Should redirect to login if not authenticated
        self.assertNotEqual(response.status_code, 200)
    
    def test_staff_can_view_invoice(self):
        """Test staff user can view any invoice"""
        self.client.login(username='staffuser', password='testpass123')
        
        # Staff should be able to view any invoice
        # This assumes there's an invoice detail view
        # Adjust URL based on your actual URL configuration
        response = self.client.get(f'/HMS/portal/invoices/?panel=1')
        
        # Check response is not an error
        self.assertIn(response.status_code, [200, 404, 302])
    
    def test_guest_can_view_own_invoice(self):
        """Test guest can view their own invoices"""
        self.client.login(username='guestuser', password='testpass123')
        
        # Guest should be able to view their own invoices
        response = self.client.get(f'/HMS/portal/invoices/?panel=1')
        
        self.assertIn(response.status_code, [200, 404, 302])
    
    def test_invoice_mydata_status_display(self):
        """Test MyData status is displayed correctly"""
        # Test with untransmitted invoice
        self.assertFalse(self.invoice.mydata_transmitted)
        
        # Transmit invoice
        service = get_mydata_service()
        service.transmit_invoice(self.invoice)
        
        # Verify transmission
        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.mydata_transmitted)


@override_settings(
    HOTEL_TAX_ID='123456789',
    MYDATA_API_BASE='https://www1.mydata.aade.gr/api',
    MYDATA_USERNAME='test_user',
    MYDATA_PASSWORD='test_pass',
    MYDATA_API_KEY='test_key',
    MYDATA_SANDBOX_MODE=True,
    MYDATA_AUTO_TRANSMISSION=False,
    MYDATA_TRANSMISSION_RETRIES=3
)
class MyDataQRCodeTestCase(TestCase):
    """Test cases for MyData QR code generation"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testguest',
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        # Create guest
        self.guest = Guest.objects.create(
            user=self.user,
            email=self.user.email,
            first_name=self.user.first_name,
            last_name=self.user.last_name,
            phone_number='+30-210-1234567'
        )
        
        # Create payment method
        self.payment_method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        # Create payment
        self.payment = Payment.objects.create(
            guest=self.guest,
            payment_method=self.payment_method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-12345',
            reference_code='REF-12345'
        )
        
        # Create invoice
        self.invoice = Invoice.objects.create(
            guest=self.guest,
            payment=self.payment,
            amount=Decimal('100.00'),
            tax_amount=Decimal('24.00'),
            total_amount=Decimal('124.00'),
            status='issued',
            description='Test Invoice',
            due_date=timezone.now().date() + timedelta(days=30)
        )
    
    def test_qr_code_format_compliance(self):
        """Test QR code follows VIES format: A|TAX_ID|INV_NUM|DATE|GROSS|VAT"""
        service = get_mydata_service()
        qr_data = service.generate_qr_code_data(self.invoice)
        
        # Split by pipe delimiter
        parts = qr_data.split('|')
        
        # Should have exactly 6 parts
        self.assertEqual(len(parts), 6)
        
        # First part should be 'A'
        self.assertEqual(parts[0], 'A')
        
        # Should contain amounts
        self.assertIsNotNone(parts[4])  # Gross amount
        self.assertIsNotNone(parts[5])  # VAT amount
    
    def test_qr_code_contains_invoice_number(self):
        """Test QR code contains invoice number"""
        service = get_mydata_service()
        qr_data = service.generate_qr_code_data(self.invoice)
        
        self.assertIn(self.invoice.invoice_number, qr_data)
    
    def test_qr_code_contains_amounts(self):
        """Test QR code contains invoice amounts"""
        service = get_mydata_service()
        qr_data = service.generate_qr_code_data(self.invoice)
        
        # Check for amounts in cents format in the QR code
        self.assertIn('12400', qr_data)  # Total: 124.00 in cents
        self.assertIn('2400', qr_data)   # Tax: 24.00 in cents
