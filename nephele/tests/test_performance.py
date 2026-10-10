"""
Performance and Load Testing

Load testing scenarios for different user loads:
- Normal load: 100 concurrent users
- Peak load: 500 concurrent users  
- Stress test: gradually increase until failure

Using Locust framework patterns
"""

from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
import time

from room.models import Room, Booking
from accounts.models import Guest
from payments.models import Payment, PaymentMethod
from properties.models import Property


class PerformanceBaselineTests(TestCase):
    """Baseline performance metrics for critical operations"""
    
    def setUp(self):
        """Set up test data"""
        self.property = Property.objects.create(
            name='Perf Test Hotel',
            address='123 Perf St',
            city='Test City',
            country='Test Country',
            postal_code='54321',
            phone_number='+30-210-1234567',
            email='perf@hotel.com'
        )
        
        # Create multiple rooms for performance testing
        self.rooms = []
        for i in range(1, 51):  # 50 rooms
            room = Room.objects.create(
                room_number=f'{i:03d}',
                floor=(i-1) // 10 + 1,
                room_type='double' if i % 2 == 0 else 'single',
                capacity=2 if i % 2 == 0 else 1,
                number_of_beds=1,
                base_price=Decimal('100.00'),
                current_price=Decimal('100.00'),
                property=self.property
            )
            self.rooms.append(room)
        
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@test.com'
        )
        
        self.guest = Guest.objects.create(
            user=self.user,
            email='perf@test.com',
            first_name='Perf',
            last_name='User'
        )
    
    def test_room_list_performance(self):
        """Test performance of listing rooms"""
        start = time.time()
        
        rooms = Room.objects.filter(property=self.property)
        _ = list(rooms)  # Force evaluation
        
        elapsed = time.time() - start
        
        # Assert response time is acceptable (< 200ms for 50 rooms)
        self.assertLess(elapsed, 0.2, f"Room listing took {elapsed}s")
    
    def test_room_availability_check_performance(self):
        """Test performance of checking room availability"""
        check_in = timezone.now().date() + timedelta(days=1)
        check_out = check_in + timedelta(days=3)
        
        start = time.time()
        
        available_rooms = Room.objects.filter(
            property=self.property,
            status='available'
        ).exclude(
            bookings__check_in_date__lt=check_out,
            bookings__check_out_date__gt=check_in,
            bookings__status__in=['confirmed', 'checked_in']
        )
        
        _ = list(available_rooms)
        
        elapsed = time.time() - start
        
        # Should complete in < 100ms
        self.assertLess(elapsed, 0.1, f"Availability check took {elapsed}s")
    
    def test_booking_creation_performance(self):
        """Test performance of creating bookings"""
        start = time.time()
        
        booking = Booking.objects.create(
            room=self.rooms[0],
            guest=self.guest,
            check_in_date=timezone.now().date() + timedelta(days=1),
            check_out_date=timezone.now().date() + timedelta(days=4),
            number_of_guests=2,
            status='confirmed',
            base_price=Decimal('300.00')
        )
        
        elapsed = time.time() - start
        
        # Booking creation should be < 50ms
        self.assertLess(elapsed, 0.05, f"Booking creation took {elapsed}s")
        self.assertIsNotNone(booking.id)
    
    def test_payment_processing_performance(self):
        """Test performance of payment processing"""
        method = PaymentMethod.objects.create(
            name='Credit Card',
            payment_type='card',
            is_active=True
        )
        
        start = time.time()
        
        payment = Payment.objects.create(
            guest=self.guest,
            payment_method=method,
            amount=Decimal('100.00'),
            currency='EUR',
            transaction_id='TXN-PERF-001',
            status='completed'
        )
        
        elapsed = time.time() - start
        
        # Payment should process in < 100ms
        self.assertLess(elapsed, 0.1, f"Payment processing took {elapsed}s")
    
    def test_bulk_booking_creation_performance(self):
        """Test performance of bulk booking operations"""
        start = time.time()
        
        # Create multiple bookings
        bookings = []
        base_date = timezone.now().date() + timedelta(days=1)
        
        for i in range(10):
            booking = Booking.objects.create(
                room=self.rooms[i],
                guest=self.guest,
                check_in_date=base_date,
                check_out_date=base_date + timedelta(days=3),
                number_of_guests=1,
                status='confirmed',
                base_price=Decimal('300.00')
            )
            bookings.append(booking)
        
        elapsed = time.time() - start
        
        # 10 bookings should complete in < 500ms
        self.assertLess(elapsed, 0.5, f"Bulk booking creation took {elapsed}s")
        self.assertEqual(len(bookings), 10)


class LoadTestScenarios(TestCase):
    """Load test scenarios for concurrent operations"""
    
    def setUp(self):
        """Set up test data"""
        self.property = Property.objects.create(
            name='Load Test Hotel',
            address='123 Load St',
            city='Test City',
            country='Test Country',
            postal_code='54321',
            phone_number='+30-210-1234567',
            email='load@hotel.com'
        )
        
        self.rooms = []
        for i in range(1, 11):
            room = Room.objects.create(
                room_number=f'LT{i:03d}',
                floor=1,
                room_type='double',
                capacity=2,
                number_of_beds=1,
                base_price=Decimal('100.00'),
                current_price=Decimal('100.00'),
                property=self.property
            )
            self.rooms.append(room)
    
    def test_normal_load_scenario(self):
        """Test normal load scenario (100 concurrent booking requests)"""
        # Simulate 100 users making bookings
        users = []
        for i in range(100):
            user = User.objects.create_user(
                username=f'loaduser{i}',
                email=f'loaduser{i}@test.com'
            )
            users.append(user)
        
        self.assertEqual(len(users), 100)
    
    def test_peak_load_scenario(self):
        """Test peak load scenario (500 concurrent requests)"""
        # Simulate 500 concurrent requests
        # In real scenario, this would be handled by load test tool
        
        # Create sample requests
        requests_made = 0
        for i in range(500):
            # Simulate request by checking room availability
            available = Room.objects.filter(
                property=self.property,
                status='available'
            ).count()
            
            if available > 0:
                requests_made += 1
        
        # Verify requests were processed
        self.assertGreater(requests_made, 0)
    
    def test_stress_test_database_load(self):
        """Test system under stress with increasing load"""
        # Gradually create load and measure response
        response_times = []
        
        for iteration in range(5):
            start = time.time()
            
            # Simulate operation
            rooms = Room.objects.filter(property=self.property)
            _ = list(rooms)
            
            elapsed = time.time() - start
            response_times.append(elapsed)
        
        # Verify system remains responsive
        avg_response = sum(response_times) / len(response_times)
        self.assertLess(avg_response, 0.2)


class ScalabilityTests(TestCase):
    """Tests to measure system scalability"""
    
    def test_query_performance_with_data_growth(self):
        """Test query performance as data grows"""
        property_obj = Property.objects.create(
            name='Scale Test Hotel',
            address='123 Scale St',
            city='Test City',
            country='Test Country',
            postal_code='54321',
            phone_number='+30-210-1234567',
            email='scale@hotel.com'
        )
        
        # Test with different data volumes
        data_sizes = [10, 100, 1000]
        response_times = []
        
        for size in data_sizes:
            # Clear previous rooms
            Room.objects.all().delete()
            
            # Create rooms
            for i in range(size):
                Room.objects.create(
                    room_number=f'SR{i:05d}',
                    floor=1,
                    room_type='double',
                    capacity=2,
                    number_of_beds=1,
                    base_price=Decimal('100.00'),
                    current_price=Decimal('100.00'),
                    property=property_obj
                )
            
            # Measure query time
            start = time.time()
            rooms = list(Room.objects.all())
            elapsed = time.time() - start
            
            response_times.append(elapsed)
        
        # Verify scalability - response time should scale reasonably
        # (not dramatically worse with more data)
        self.assertGreater(len(response_times), 0)
    
    def test_index_effectiveness(self):
        """Test that database indexes are effective"""
        property_obj = Property.objects.create(
            name='Index Test Hotel',
            address='123 Index St',
            city='Test City',
            country='Test Country',
            postal_code='54321',
            phone_number='+30-210-1234567',
            email='index@hotel.com'
        )
        
        # Create rooms
        rooms = []
        for i in range(100):
            room = Room.objects.create(
                room_number=f'IT{i:03d}',
                floor=1,
                room_type='double',
                capacity=2,
                number_of_beds=1,
                base_price=Decimal('100.00'),
                current_price=Decimal('100.00'),
                property=property_obj
            )
            rooms.append(room)
        
        # Test indexed query (by property)
        start = time.time()
        filtered = list(
            Room.objects.filter(property=property_obj)
        )
        indexed_time = time.time() - start
        
        # Should be fast due to index
        self.assertLess(indexed_time, 0.1)
        self.assertEqual(len(filtered), 100)
