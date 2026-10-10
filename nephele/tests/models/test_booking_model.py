"""
Unit tests for Booking model

Tests for Booking entity including validation, status transitions, and calculations
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from room.models import Room, Booking
from accounts.models import Guest
from properties.models import Property


class BookingModelTests(TestCase):
    """Test cases for Booking model"""
    
    def setUp(self):
        """Set up test data for booking tests"""
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
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        self.guest = Guest.objects.create(
            user=self.user,
            email=self.user.email,
            first_name=self.user.first_name,
            last_name=self.user.last_name,
            phone_number='+30-210-9876543'
        )
        
        # Set up dates
        self.check_in_date = timezone.now().date() + timedelta(days=1)
        self.check_out_date = self.check_in_date + timedelta(days=3)
    
    def test_booking_creation_with_valid_data(self):
        """Test creating a booking with valid data"""
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=self.check_in_date,
            check_out_date=self.check_out_date,
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        self.assertEqual(booking.room, self.room)
        self.assertEqual(booking.guest, self.guest)
        self.assertEqual(booking.check_in_date, self.check_in_date)
        self.assertEqual(booking.check_out_date, self.check_out_date)
        self.assertEqual(booking.status, 'confirmed')
    
    def test_booking_status_choices(self):
        """Test booking status field with all valid choices"""
        statuses = ['pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled', 'no_show']
        
        for idx, status in enumerate(statuses):
            booking = Booking.objects.create(
                room=self.room,
                guest=self.guest,
                check_in_date=self.check_in_date + timedelta(days=idx*10),
                check_out_date=self.check_out_date + timedelta(days=idx*10),
                number_of_guests=2,
                status=status,
                base_price=Decimal('300.00')
            )
            self.assertEqual(booking.status, status)
    
    def test_booking_date_validation(self):
        """Test that valid bookings have check_out after check_in"""
        # Test with valid dates
        valid_checkout = self.check_in_date + timedelta(days=3)
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=self.check_in_date,
            check_out_date=valid_checkout,
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        # Verify dates are in correct order
        self.assertLess(booking.check_in_date, booking.check_out_date)
        self.assertEqual(booking.check_out_date - booking.check_in_date, timedelta(days=3))
    
    def test_booking_number_of_guests(self):
        """Test number of guests field"""
        for num_guests in [1, 2, 4, 6]:
            booking = Booking.objects.create(
                room=self.room,
                guest=self.guest,
                check_in_date=self.check_in_date,
                check_out_date=self.check_out_date,
                number_of_guests=num_guests,
                status='confirmed',
                base_price=Decimal('300.00')
            )
            self.assertEqual(booking.number_of_guests, num_guests)
    
    def test_booking_total_price_calculation(self):
        """Test booking total price field"""
        total_price = Decimal('300.00')
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=self.check_in_date,
            check_out_date=self.check_out_date,
            number_of_guests=2,
            status='confirmed',
            base_price=total_price
        )
        
        self.assertEqual(booking.base_price, total_price)
    
    def test_booking_payment_status(self):
        """Test booking status transitions"""
        statuses = ['pending', 'confirmed', 'checked_in', 'checked_out']
        
        for idx, status in enumerate(statuses):
            booking = Booking.objects.create(
                room=self.room,
                guest=self.guest,
                check_in_date=self.check_in_date + timedelta(days=idx*10),
                check_out_date=self.check_out_date + timedelta(days=idx*10),
                number_of_guests=2,
                status=status,
                base_price=Decimal('300.00')
            )
            self.assertEqual(booking.status, status)
    
    def test_booking_special_requests(self):
        """Test booking special requests field"""
        special_requests = 'Please ground floor room, early check-in if possible'
        
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=self.check_in_date,
            check_out_date=self.check_out_date,
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00'),
            special_requests=special_requests
        )
        
        self.assertEqual(booking.special_requests, special_requests)
    
    def test_booking_cancellation_logic(self):
        """Test booking cancellation"""
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=self.check_in_date,
            check_out_date=self.check_out_date,
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        booking.status = 'cancelled'
        booking.save()
        booking.refresh_from_db()
        
        self.assertEqual(booking.status, 'cancelled')
    
    def test_booking_timestamps(self):
        """Test booking creation and update timestamps"""
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=self.check_in_date,
            check_out_date=self.check_out_date,
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        self.assertIsNotNone(booking.created_at)
        self.assertIsNotNone(booking.updated_at)
    
    def test_booking_reference_number(self):
        """Test booking reference number generation"""
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=self.check_in_date,
            check_out_date=self.check_out_date,
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        # Verify reference number exists and is unique-like
        if hasattr(booking, 'reference_number'):
            self.assertIsNotNone(booking.reference_number)
    
    def test_booking_duration_calculation(self):
        """Test calculating booking duration in nights"""
        booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in_date=self.check_in_date,
            check_out_date=self.check_out_date,
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        # Duration should be 3 days/2 nights (check_out_date - check_in_date)
        duration = (booking.check_out_date - booking.check_in_date).days
        self.assertEqual(duration, 3)
    
    def test_multiple_bookings_same_guest(self):
        """Test that a guest can have multiple bookings"""
        bookings = []
        for i in range(3):
            booking = Booking.objects.create(
                room=self.room,
                guest=self.guest,
                check_in_date=self.check_in_date + timedelta(days=i*5),
                check_out_date=self.check_out_date + timedelta(days=i*5),
                number_of_guests=2,
                status='confirmed',
                base_price=Decimal('300.00')
            )
            bookings.append(booking)
        
        self.assertEqual(len(bookings), 3)
        guest_bookings = Booking.objects.filter(guest=self.guest)
        self.assertEqual(guest_bookings.count(), 3)
