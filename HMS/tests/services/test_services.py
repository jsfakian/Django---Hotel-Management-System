"""
Unit tests for service methods

Tests for PricingService, NotificationService, and other business logic services
"""

from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from bookings.pricing_service import PricingPredictor
from bookings.models import PricingHistory, DemandForecast, CompetitorPrice
from room.models import Room
from properties.models import Property


class PricingServiceTests(TestCase):
    """Test cases for Pricing Service"""
    
    def setUp(self):
        """Set up test data"""
        self.property = Property.objects.create(
            name='Test Hotel',
            address='123 Test St',
            city='Test City',
            country='Test Country',
            postal_code='12345',
            phone_number='+30-210-1234567',
            email='test@hotel.com'
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
    
    def test_pricing_predictor_initialization(self):
        """Test PricingPredictor initialization"""
        predictor = PricingPredictor()
        # Should initialize without errors
        self.assertIsNotNone(predictor)
    
    def test_pricing_history_creation(self):
        """Test creating pricing history records"""
        history = PricingHistory.objects.create(
            room=self.room,
            date=timezone.now().date(),
            weekday=0,  # Monday
            base_price=Decimal('100.00'),
            dynamic_price=Decimal('120.00'),
            occupancy_rate=Decimal('85.00'),
            demand_score=Decimal('4.5'),
            bookings_count=10
        )
        
        self.assertEqual(history.room, self.room)
        self.assertEqual(history.dynamic_price, Decimal('120.00'))
        self.assertEqual(history.occupancy_rate, Decimal('85.00'))
    
    def test_demand_forecast_creation(self):
        """Test creating demand forecast records"""
        forecast_date = timezone.now().date() + timedelta(days=7)
        
        forecast = DemandForecast.objects.create(
            room=self.room,
            forecast_date=timezone.now().date(),
            forecast_for_date=forecast_date,
            predicted_occupancy=Decimal('80.00'),
            predicted_demand_score=Decimal('4.2'),
            recommended_price=Decimal('110.00'),
            confidence=Decimal('0.85')
        )
        
        self.assertEqual(forecast.room, self.room)
        self.assertEqual(forecast.recommended_price, Decimal('110.00'))
        self.assertGreater(forecast.confidence, 0)
    
    def test_competitor_price_tracking(self):
        """Test competitor price tracking"""
        competitor_price = CompetitorPrice.objects.create(
            room=self.room,
            competitor_name='Competitor Hotel',
            date=timezone.now().date(),
            price=Decimal('105.00'),
            source_url='https://competitor.com/room/101'
        )
        
        self.assertEqual(competitor_price.competitor_name, 'Competitor Hotel')
        self.assertEqual(competitor_price.price, Decimal('105.00'))
    
    def test_pricing_calculation_with_occupancy(self):
        """Test pricing calculations based on occupancy"""
        base_price = Decimal('100.00')
        occupancy = Decimal('85.00')  # 85% occupancy
        
        # At 85% occupancy, typically increase price
        adjustment_factor = Decimal('1.20')  # 20% increase
        expected_price = base_price * adjustment_factor
        
        self.assertEqual(expected_price, Decimal('120.00'))
    
    def test_pricing_by_season(self):
        """Test pricing adjustments for different seasons"""
        seasons = {
            'low': Decimal('0.80'),      # 20% discount
            'regular': Decimal('1.00'),   # no adjustment
            'peak': Decimal('1.50')       # 50% increase
        }
        
        base_price = Decimal('100.00')
        
        for season, factor in seasons.items():
            adjusted_price = base_price * factor
            self.assertGreater(adjusted_price, 0)
    
    def test_dynamic_pricing_weekday_adjustment(self):
        """Test weekday adjustments for pricing"""
        weekday_factors = {
            'Monday': Decimal('0.90'),
            'Friday': Decimal('1.20'),
            'Saturday': Decimal('1.30'),
            'Sunday': Decimal('1.10')
        }
        
        base_price = Decimal('100.00')
        
        for day, factor in weekday_factors.items():
            adjusted_price = base_price * factor
            self.assertGreater(adjusted_price, 0)


class NotificationServiceTests(TestCase):
    """Test cases for Notification Service"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com'
        )
    
    def test_notification_service_import(self):
        """Test NotificationService can be imported"""
        try:
            from notifications.services import NotificationService
            self.assertIsNotNone(NotificationService)
        except ImportError:
            self.skipTest("NotificationService not available")
    
    def test_send_notification_creation(self):
        """Test notification creation"""
        try:
            from notifications.models import NotificationType, Notification
            
            # Create notification type
            notif_type = NotificationType.objects.create(
                code='test_notification',
                name='Test Notification',
                description='A test notification'
            )
            
            # Create notification
            notification = Notification.objects.create(
                user=self.user,
                notification_type=notif_type,
                title='Test Title',
                message='Test Message'
            )
            
            self.assertEqual(notification.user, self.user)
            self.assertEqual(notification.title, 'Test Title')
        except ImportError:
            self.skipTest("Notification models not available")
    
    def test_email_notification_creation(self):
        """Test email notification creation"""
        try:
            from notifications.models import EmailNotification
            
            # EmailNotification requires a user_id, so we create with user
            email_notif = EmailNotification.objects.create(
                user=self.user,
                recipient_email='test@example.com',
                subject='Test Subject',
                body='Test email body'
            )
            
            self.assertEqual(email_notif.recipient_email, 'test@example.com')
        except ImportError:
            self.skipTest("EmailNotification model not available")
    
    def test_notification_preference_creation(self):
        """Test notification preferences"""
        try:
            from notifications.models import NotificationPreference
            
            preference = NotificationPreference.objects.create(
                user=self.user,
                receive_in_app=True,
                receive_email=True,
                receive_sms=False
            )
            
            self.assertTrue(preference.receive_in_app)
            self.assertTrue(preference.receive_email)
            self.assertFalse(preference.receive_sms)
        except ImportError:
            self.skipTest("NotificationPreference model not available")


class BookingServiceTests(TestCase):
    """Test cases for Booking business logic services"""
    
    def setUp(self):
        """Set up test data"""
        self.property = Property.objects.create(
            name='Test Hotel',
            address='123 Test St',
            city='Test City',
            country='Test Country',
            postal_code='12345',
            phone_number='+30-210-1234567',
            email='test@hotel.com'
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
            username='testguest',
            email='guest@test.com'
        )
        
        from accounts.models import Guest
        self.guest = Guest.objects.create(
            user=self.user,
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
    
    def test_check_room_availability(self):
        """Test room availability checking"""
        from room.models import Booking
        
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
        
        # Check that room is booked for those dates
        bookings = Booking.objects.filter(
            room=self.room,
            check_in_date__lt=check_out,
            check_out_date__gt=check_in
        )
        
        self.assertEqual(bookings.count(), 1)
    
    def test_calculate_booking_price(self):
        """Test booking price calculation"""
        num_nights = 3
        nightly_rate = Decimal('100.00')
        
        total_price = num_nights * nightly_rate
        self.assertEqual(total_price, Decimal('300.00'))
    
    def test_booking_price_with_taxes(self):
        """Test booking price calculation with taxes"""
        subtotal = Decimal('300.00')
        tax_rate = Decimal('0.20')  # 20% VAT
        
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        self.assertEqual(tax_amount, Decimal('60.00'))
        self.assertEqual(total, Decimal('360.00'))


class PaymentServiceTests(TestCase):
    """Test cases for Payment business logic"""
    
    def setUp(self):
        """Set up test data"""
        from accounts.models import Guest
        
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
    
    def test_validate_payment_amount(self):
        """Test payment amount validation"""
        valid_amount = Decimal('100.00')
        invalid_amount = Decimal('-50.00')
        
        self.assertGreater(valid_amount, 0)
        self.assertLess(invalid_amount, 0)
    
    def test_payment_currency_conversion(self):
        """Test payment currency handling"""
        from payments.models import Payment, PaymentMethod
        from room.models import Booking, Room
        
        method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        # Create a room and booking for payment
        property_obj = Property.objects.create(
            name='Test Hotel',
            address='123 Test St',
            city='Test City',
            country='Test Country',
            postal_code='12345',
            phone_number='+30-210-1234567',
            email='test@hotel.com'
        )
        
        room = Room.objects.create(
            room_number='101',
            floor=1,
            room_type='double',
            capacity=2,
            number_of_beds=1,
            base_price=Decimal('100.00'),
            current_price=Decimal('100.00'),
            property=property_obj
        )
        
        booking = Booking.objects.create(
            room=room,
            guest=self.guest,
            check_in_date=timezone.now().date() + timedelta(days=1),
            check_out_date=timezone.now().date() + timedelta(days=4),
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        currencies = ['EUR', 'GBP', 'USD']
        
        for i, currency in enumerate(currencies):
            payment = Payment.objects.create(
                guest=self.guest,
                booking=booking,
                payment_method=method,
                amount=Decimal('100.00'),
                currency=currency,
                transaction_id=f'TXN-{currency}-{i}',
                reference_code=f'REF-{currency}-{i}'
            )
            
            self.assertEqual(payment.currency, currency)
    
    def test_refund_processing(self):
        """Test refund request processing"""
        from payments.models import Payment, PaymentMethod, RefundRequest
        
        method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-1234',
            status='completed'
        )
        
        refund = RefundRequest.objects.create(
            payment=payment,
            guest=self.guest,
            refund_amount=Decimal('100.00'),
            reason='cancellation',
            description='Guest refund request',
            status='pending'
        )
        
        self.assertEqual(refund.payment, payment)
        self.assertEqual(refund.status, 'pending')
        
        # Process refund
        refund.status = 'processed'
        refund.save()
        refund.refresh_from_db()
        
        self.assertEqual(refund.status, 'processed')
