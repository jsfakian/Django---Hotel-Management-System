"""
Unit tests for Room model

Tests for Room entity including creation, validation, and status management
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from room.models import Room
from properties.models import Property


class RoomModelTests(TestCase):
    """Test cases for Room model"""
    
    def setUp(self):
        """Set up test data for room tests"""
        # Create a test property
        self.property = Property.objects.create(
            name='Test Hotel',
            address='123 Test St',
            city='Test City',
            country='Test Country',
            postal_code='12345',
            phone_number='+30-210-1234567',
            email='test@hotel.com'
        )
    
    def test_room_creation_with_valid_data(self):
        """Test creating a room with valid data"""
        room = Room.objects.create(
            room_number='101',
            floor=1,
            room_type='double',
            capacity=2,
            number_of_beds=1,
            base_price=Decimal('100.00'),
            current_price=Decimal('100.00'),
            property=self.property
        )
        
        self.assertEqual(room.room_number, '101')
        self.assertEqual(room.floor, 1)
        self.assertEqual(room.room_type, 'double')
        self.assertEqual(room.capacity, 2)
        self.assertEqual(room.status, 'available')
    
    def test_room_unique_room_number_constraint(self):
        """Test that room_number must be unique"""
        Room.objects.create(
            room_number='101',
            floor=1,
            room_type='single',
            capacity=1,
            number_of_beds=1,
            base_price=Decimal('80.00'),
            current_price=Decimal('80.00'),
            property=self.property
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            Room.objects.create(
                room_number='101',
                floor=1,
                room_type='double',
                capacity=2,
                number_of_beds=1,
                base_price=Decimal('100.00'),
                current_price=Decimal('100.00'),
                property=self.property
            )
    
    def test_room_status_transitions(self):
        """Test room status field and transitions"""
        room = Room.objects.create(
            room_number='102',
            floor=1,
            room_type='single',
            capacity=1,
            number_of_beds=1,
            base_price=Decimal('80.00'),
            current_price=Decimal('80.00'),
            property=self.property
        )
        
        # Test default status
        self.assertEqual(room.status, 'available')
        
        # Test status change
        room.status = 'occupied'
        room.save()
        room.refresh_from_db()
        self.assertEqual(room.status, 'occupied')
        
        # Test maintenance status
        room.status = 'maintenance'
        room.save()
        room.refresh_from_db()
        self.assertEqual(room.status, 'maintenance')
    
    def test_room_amenities_json_field(self):
        """Test amenities JSON field"""
        amenities = ['wifi', 'tv', 'air_conditioning', 'safe']
        room = Room.objects.create(
            room_number='103',
            floor=1,
            room_type='suite',
            capacity=2,
            number_of_beds=2,
            base_price=Decimal('150.00'),
            current_price=Decimal('150.00'),
            property=self.property,
            amenities=amenities
        )
        
        room.refresh_from_db()
        self.assertEqual(room.amenities, amenities)
        self.assertIn('wifi', room.amenities)
    
    def test_room_pricing_fields(self):
        """Test room pricing fields"""
        base_price = Decimal('100.00')
        current_price = Decimal('120.00')
        
        room = Room.objects.create(
            room_number='104',
            floor=1,
            room_type='double',
            capacity=2,
            number_of_beds=1,
            base_price=base_price,
            current_price=current_price,
            property=self.property
        )
        
        self.assertEqual(room.base_price, base_price)
        self.assertEqual(room.current_price, current_price)
    
    def test_room_capacity_and_beds(self):
        """Test room capacity and bed configuration"""
        room = Room.objects.create(
            room_number='105',
            floor=2,
            room_type='suite',
            capacity=4,
            number_of_beds=2,
            base_price=Decimal('200.00'),
            current_price=Decimal('200.00'),
            property=self.property
        )
        
        self.assertEqual(room.capacity, 4)
        self.assertEqual(room.number_of_beds, 2)
    
    def test_room_str_representation(self):
        """Test room string representation"""
        room = Room.objects.create(
            room_number='106',
            floor=1,
            room_type='single',
            capacity=1,
            number_of_beds=1,
            base_price=Decimal('80.00'),
            current_price=Decimal('80.00'),
            property=self.property
        )
        
        expected_str = f"Room 106 - {self.property.name}"
        self.assertEqual(str(room), expected_str)
    
    def test_room_timestamps(self):
        """Test room creation and update timestamps"""
        room = Room.objects.create(
            room_number='107',
            floor=1,
            room_type='double',
            capacity=2,
            number_of_beds=1,
            base_price=Decimal('100.00'),
            current_price=Decimal('100.00'),
            property=self.property
        )
        
        self.assertIsNotNone(room.created_at)
        self.assertIsNotNone(room.updated_at)
        # Check they're very close (within 1 second)
        time_diff = abs((room.created_at - room.updated_at).total_seconds())
        self.assertLess(time_diff, 1.0, "created_at and updated_at should be within 1 second")
        
        # Update and verify updated_at changes
        original_updated = room.updated_at
        room.current_price = Decimal('110.00')
        room.save()
        room.refresh_from_db()
        self.assertGreaterEqual(room.updated_at, original_updated)
    
    def test_room_floor_level_variations(self):
        """Test rooms on different floor levels"""
        for floor in [0, 1, 2, 5, 10]:
            room = Room.objects.create(
                room_number=f'FL{floor}-01',
                floor=floor,
                room_type='single',
                capacity=1,
                number_of_beds=1,
                base_price=Decimal('80.00'),
                current_price=Decimal('80.00'),
                property=self.property
            )
            self.assertEqual(room.floor, floor)
    
    def test_room_type_choices(self):
        """Test all valid room type choices"""
        room_types = ['single', 'double', 'suite', 'deluxe', 'luxury', 'economic']
        
        for idx, room_type in enumerate(room_types):
            room = Room.objects.create(
                room_number=f'TYPE-{idx:03d}',
                floor=1,
                room_type=room_type,
                capacity=1,
                number_of_beds=1,
                base_price=Decimal('80.00'),
                current_price=Decimal('80.00'),
                property=self.property
            )
            self.assertEqual(room.room_type, room_type)
