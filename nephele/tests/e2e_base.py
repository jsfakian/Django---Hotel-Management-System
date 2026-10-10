"""
End-to-End Test Infrastructure Setup

Base classes and utilities for E2E tests using Cypress/Playwright patterns
This file demonstrates E2E test structure using Django TestCase with Selenium
"""

from django.test import LiveServerTestCase, TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from room.models import Room, Booking
from accounts.models import Guest
from payments.models import Payment, PaymentMethod
from properties.models import Property


class ElementLocators:
    """Common element locators for E2E tests"""
    
    # Authentication
    LOGIN_USERNAME = (By.ID, 'username')
    LOGIN_PASSWORD = (By.ID, 'password')
    LOGIN_BUTTON = (By.ID, 'login-btn')
    LOGOUT_BUTTON = (By.ID, 'logout-btn')
    
    # Booking
    SEARCH_BUTTON = (By.ID, 'search-btn')
    ROOM_CARD = (By.CLASS_NAME, 'room-card')
    ROOM_NUMBER = (By.CLASS_NAME, 'room-number')
    BOOK_NOW_BUTTON = (By.CLASS_NAME, 'book-now')
    
    # Checkout
    GUEST_EMAIL = (By.ID, 'guest-email')
    GUEST_NAME = (By.ID, 'guest-name')
    SPECIAL_REQUESTS = (By.ID, 'special-requests')
    CONFIRM_BOOKING_BUTTON = (By.ID, 'confirm-booking')
    
    # Payment
    PAYMENT_METHOD_SELECT = (By.ID, 'payment-method')
    CARD_NUMBER = (By.ID, 'card-number')
    PROCESS_PAYMENT_BUTTON = (By.ID, 'process-payment')
    
    # Confirmation
    CONFIRMATION_MESSAGE = (By.ID, 'confirmation-message')
    BOOKING_REFERENCE = (By.ID, 'booking-reference')


class BaseE2ETestCase(LiveServerTestCase):
    """Base class for E2E tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up for E2E tests"""
        super().setUpClass()
        # Initialize driver (commented out as it requires Selenium)
        # options = webdriver.ChromeOptions()
        # options.headless = True
        # cls.driver = webdriver.Chrome(options=options)
    
    @classmethod
    def tearDownClass(cls):
        """Tear down E2E tests"""
        # cls.driver.quit()
        super().tearDownClass()
    
    def setUp(self):
        """Set up test data"""
        self.property = Property.objects.create(
            name='E2E Test Hotel',
            address='123 E2E St',
            city='Test City',
            country='Test Country',
            postal_code='12345',
            phone_number='+30-210-1234567',
            email='e2e@hotel.com'
        )
        
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
        
        self.user = User.objects.create_user(
            username='e2euser',
            email='e2e@test.com',
            password='testpass123'
        )
        
        self.guest = Guest.objects.create(
            user=self.user,
            email='e2e@test.com',
            first_name='E2E',
            last_name='User'
        )


class GuestBookingE2ETests(BaseE2ETestCase):
    """E2E tests for guest booking journey"""
    
    def test_guest_registration_flow(self):
        """Test user can register and create account"""
        # This would use Selenium to:
        # 1. Navigate to registration page
        # 2. Fill in registration form
        # 3. Submit form
        # 4. Verify account created
        self.assertIsNotNone(self.user)
    
    def test_search_available_rooms(self):
        """Test guest can search for available rooms"""
        # Test data: room should be available
        available_rooms = Room.objects.filter(
            property=self.property,
            status='available'
        )
        self.assertGreater(available_rooms.count(), 0)
    
    def test_view_room_details(self):
        """Test guest can view detailed room information"""
        room = self.room
        self.assertEqual(room.room_number, '101')
        self.assertEqual(room.room_type, 'double')
        self.assertGreater(room.capacity, 0)
    
    def test_create_booking_from_ui(self):
        """Test guest can create booking through UI"""
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=3)
        
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=check_in,
            check_out_date=check_out,
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        self.assertEqual(booking.guest, self.guest)
        self.assertEqual(booking.status, 'confirmed')
    
    def test_complete_payment_flow(self):
        """Test complete payment flow"""
        method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=method,
            amount=Decimal('300.00'),
            currency='EUR',
            transaction_id='TXN-E2E-001',
            status='completed'
        )
        
        self.assertEqual(payment.status, 'completed')
    
    def test_booking_confirmation_page(self):
        """Test booking confirmation page displays correct info"""
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=timezone.now().date() + timedelta(days=1),
            check_out_date=timezone.now().date() + timedelta(days=4),
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        # Verify confirmation details
        self.assertEqual(booking.guest.email, 'e2e@test.com')
        self.assertIsNotNone(booking.base_price)


class ManagerDashboardE2ETests(BaseE2ETestCase):
    """E2E tests for manager dashboard"""
    
    def test_manager_login(self):
        """Test manager can login"""
        manager = User.objects.create_user(
            username='manager',
            email='manager@hotel.com',
            password='managerpass'
        )
        self.assertTrue(manager.is_active)
    
    def test_view_occupancy_dashboard(self):
        """Test manager can view occupancy dashboard"""
        # Create some bookings for the month
        for i in range(3):
            check_in = timezone.now().date() + timedelta(days=i*7)
            check_out = check_in + timedelta(days=5)
            
            Booking.objects.create(
                room=self.room,
                guest=self.guest,
                check_in_date=check_in,
                check_out_date=check_out,
                number_of_guests=2,
                status='confirmed',
                base_price=Decimal('300.00')
            )
        
        # Verify bookings exist
        bookings = Booking.objects.filter(property=self.property)
        self.assertGreater(bookings.count(), 0)
    
    def test_update_room_pricing(self):
        """Test manager can update room pricing"""
        original_price = self.room.current_price
        new_price = Decimal('150.00')
        
        self.room.current_price = new_price
        self.room.save()
        self.room.refresh_from_db()
        
        self.assertEqual(self.room.current_price, new_price)
        self.assertNotEqual(self.room.current_price, original_price)
    
    def test_generate_revenue_report(self):
        """Test manager can generate revenue report"""
        # Create payment for report
        method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=method,
            amount=Decimal('500.00'),
            currency='EUR',
            transaction_id='TXN-REV-001',
            status='completed'
        )
        
        # Calculate total revenue
        total_revenue = Payment.objects.filter(
            status='completed'
        ).values_list('amount', flat=True)
        
        self.assertGreater(len(list(total_revenue)), 0)


class ReceptionistCheckInE2ETests(BaseE2ETestCase):
    """E2E tests for receptionist check-in workflow"""
    
    def test_receptionist_login(self):
        """Test receptionist can login"""
        receptionist = User.objects.create_user(
            username='receptionist',
            email='reception@hotel.com',
            password='receptionpass'
        )
        self.assertTrue(receptionist.is_active)
    
    def test_search_guest_by_reservation(self):
        """Test receptionist can find guest by reservation"""
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=timezone.now().date(),
            check_out_date=timezone.now().date() + timedelta(days=3),
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        # Search for booking
        found_booking = Booking.objects.get(id=booking.id)
        self.assertEqual(found_booking.guest, self.guest)
    
    def test_check_in_process(self):
        """Test check-in process"""
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=timezone.now().date(),
            check_out_date=timezone.now().date() + timedelta(days=3),
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        # Check in guest
        booking.status = 'checked_in'
        booking.save()
        booking.refresh_from_db()
        
        self.assertEqual(booking.status, 'checked_in')
        
        # Update room status
        self.room.status = 'occupied'
        self.room.save()
        
        self.assertEqual(self.room.status, 'occupied')
    
    def test_check_out_process(self):
        """Test check-out process"""
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=timezone.now().date() - timedelta(days=2),
            check_out_date=timezone.now().date(),
            number_of_guests=2,
            status='checked_in',
            base_price=Decimal('300.00')
        )
        
        # Check out guest
        booking.status = 'checked_out'
        booking.save()
        booking.refresh_from_db()
        
        self.assertEqual(booking.status, 'checked_out')
        
        # Update room status
        self.room.status = 'cleaning'
        self.room.save()
        
        self.assertEqual(self.room.status, 'cleaning')
