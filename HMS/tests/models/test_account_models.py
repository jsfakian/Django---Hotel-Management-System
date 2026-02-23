"""
Unit tests for Guest and Account models

Tests for Guest, Employee, Role, and Task models
"""

from django.test import TestCase
from django.contrib.auth.models import User
import pytest

from accounts.models import Guest, Employee, Role, Task


class GuestModelTests(TestCase):
    """Test cases for Guest model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testguest',
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
    
    def test_guest_creation_with_valid_data(self):
        """Test creating a guest with valid data"""
        guest = Guest.objects.create(
            user=self.user,
            email='guest@test.com',
            first_name='John',
            last_name='Doe',
            phone_number='+30-210-1234567'
        )
        
        self.assertEqual(guest.email, 'guest@test.com')
        self.assertEqual(guest.first_name, 'John')
        self.assertEqual(guest.last_name, 'Doe')
        self.assertEqual(guest.phone_number, '+30-210-1234567')
    
    def test_guest_email_unique_constraint(self):
        """Test that email must be unique"""
        guest1 = Guest.objects.create(
            email='duplicate@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            Guest.objects.create(
                email='duplicate@test.com',
                first_name='Jane',
                last_name='Smith'
            )
    
    def test_guest_optional_address_fields(self):
        """Test guest address fields (optional)"""
        guest = Guest.objects.create(
            user=self.user,
            email='guest@test.com',
            first_name='John',
            last_name='Doe',
            address='123 Main St',
            city='Athens',
            country='Greece',
            postal_code='10001'
        )
        
        self.assertEqual(guest.address, '123 Main St')
        self.assertEqual(guest.city, 'Athens')
        self.assertEqual(guest.country, 'Greece')
        self.assertEqual(guest.postal_code, '10001')
    
    def test_guest_preferences_json_field(self):
        """Test guest preferences JSON field"""
        preferences = {
            'room_type': 'double',
            'floor_preference': 'high',
            'amenities': ['wifi', 'bath_tub']
        }
        
        guest = Guest.objects.create(
            email='guest@test.com',
            first_name='John',
            last_name='Doe',
            preferences=preferences
        )
        
        guest.refresh_from_db()
        self.assertEqual(guest.preferences['room_type'], 'double')
        self.assertIn('wifi', guest.preferences['amenities'])
    
    def test_guest_booking_statistics(self):
        """Test guest booking count statistics"""
        guest = Guest.objects.create(
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        self.assertEqual(guest.number_of_bookings, 0)
        self.assertEqual(guest.total_nights_stayed, 0)
        
        # Update statistics
        guest.number_of_bookings = 5
        guest.total_nights_stayed = 20
        guest.save()
        guest.refresh_from_db()
        
        self.assertEqual(guest.number_of_bookings, 5)
        self.assertEqual(guest.total_nights_stayed, 20)
    
    def test_guest_str_representation(self):
        """Test guest string representation"""
        guest = Guest.objects.create(
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        self.assertEqual(str(guest), 'John Doe')
    
    def test_guest_timestamps(self):
        """Test guest creation and update timestamps"""
        guest = Guest.objects.create(
            email='guest@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        self.assertIsNotNone(guest.created_at)
        self.assertIsNotNone(guest.updated_at)
    
    def test_guest_legacy_methods(self):
        """Test legacy backward compatibility methods"""
        guest = Guest.objects.create(
            email='guest@test.com',
            first_name='John',
            last_name='Doe',
            number_of_bookings=5,
            total_nights_stayed=20
        )
        
        # Test legacy method names
        self.assertEqual(guest.num_of_booking(), 5)
        self.assertEqual(guest.num_of_days(), 20)


class RoleModelTests(TestCase):
    """Test cases for Role model"""
    
    def test_role_creation(self):
        """Test creating a role with valid data"""
        role = Role.objects.create(
            name='admin',
            description='System Administrator'
        )
        
        self.assertEqual(role.name, 'admin')
        self.assertEqual(role.description, 'System Administrator')
    
    def test_role_unique_name_constraint(self):
        """Test that role name must be unique"""
        Role.objects.create(name='admin', description='Admin Role')
        
        with self.assertRaises(Exception):  # IntegrityError
            Role.objects.create(name='admin', description='Another Admin')
    
    def test_role_permissions_json_field(self):
        """Test role permissions JSON field"""
        permissions = {
            'users': ['create', 'read', 'update', 'delete'],
            'reports': ['read', 'export'],
            'settings': ['update']
        }
        
        role = Role.objects.create(
            name='manager',
            description='Manager Role',
            permissions=permissions
        )
        
        role.refresh_from_db()
        self.assertIn('users', role.permissions)
        self.assertIn('create', role.permissions['users'])


class EmployeeModelTests(TestCase):
    """Test cases for Employee model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testemployee',
            email='employee@test.com',
            first_name='Jane',
            last_name='Smith'
        )
    
    def test_employee_creation(self):
        """Test creating an employee"""
        employee = Employee.objects.create(
            user=self.user,
            position='Receptionist',
            department='Front Desk',
            phone_number='+30-210-1234567',
            salary=1500.00,
            hire_date='2024-01-01',
            status='active'
        )
        
        self.assertEqual(employee.position, 'Receptionist')
        self.assertEqual(employee.department, 'Front Desk')
        self.assertEqual(employee.status, 'active')


class TaskModelTests(TestCase):
    """Test cases for Task model"""
    
    def setUp(self):
        """Set up test data"""
        from django.utils import timezone
        from accounts.models import Employee
        
        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com'
        )
        
        # Create employee for task assignment
        self.employee = Employee.objects.create(
            user=self.user,
            position='Manager',
            department='Operations'
        )
    
    def test_task_creation(self):
        """Test creating a task"""
        from django.utils import timezone
        from datetime import timedelta
        
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=2)
        
        task = Task.objects.create(
            employee=self.employee,
            title='Test Task',
            description='This is a test task',
            start_time=start_time,
            end_time=end_time,
            status='pending'
        )
        
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.status, 'pending')
        self.assertEqual(task.employee, self.employee)
    
    def test_task_status_choices(self):
        """Test task status field"""
        from django.utils import timezone
        from datetime import timedelta
        
        statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=2)
        
        for idx, status in enumerate(statuses):
            task = Task.objects.create(
                employee=self.employee,
                title=f'Task {idx}',
                description=f'Task description {idx}',
                start_time=start_time,
                end_time=end_time,
                status=status
            )
            self.assertEqual(task.status, status)
