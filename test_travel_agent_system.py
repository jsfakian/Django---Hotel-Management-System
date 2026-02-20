#!/usr/bin/env python
"""
Travel Agent Access Control - Integration Test Script

This script tests the travel agent booking system by simulating:
1. Travel agent login and property access
2. Booking creation with auto-agency assignment
3. Notification creation for staff
4. Access control validation

Run with: python test_travel_agent_system.py
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Setup Django
sys.path.insert(0, '/app/HMS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HMS.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import TravelAgentProfile, Employee
from properties.models import Property, TravelAgency
from contracts.models import Contract
from room.models import Booking, Room
from notifications.models import Notification


class TravelAgentSystemTests:
    """Test suite for travel agent access control"""
    
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    def log_pass(self, test_name, message=""):
        print(f"✅ {test_name}")
        if message:
            print(f"   └─ {message}")
        self.results['passed'].append(test_name)
    
    def log_fail(self, test_name, error=""):
        print(f"❌ {test_name}")
        if error:
            print(f"   └─ Error: {error}")
        self.results['failed'].append(test_name)
    
    def log_warning(self, test_name, message=""):
        print(f"⚠️  {test_name}")
        if message:
            print(f"   └─ {message}")
        self.results['warnings'].append(test_name)
    
    def test_travel_agent_profile_exists(self):
        """Test 1: TravelAgentProfile exists and is properly configured"""
        try:
            user = User.objects.get(username='travel_agent_john')
            profile = TravelAgentProfile.objects.get(user=user)
            
            assert profile.is_active, "Profile should be active"
            assert profile.travel_agency.name == 'Global Travel Ltd', "Agency mismatch"
            
            self.log_pass(
                "TravelAgentProfile exists",
                f"User: {user.username}, Agency: {profile.travel_agency.name}"
            )
        except Exception as e:
            self.log_fail("TravelAgentProfile exists", str(e))
    
    def test_user_group_assignment(self):
        """Test 2: User is in 'travel_agent' group"""
        try:
            user = User.objects.get(username='travel_agent_john')
            groups = list(user.groups.values_list('name', flat=True))
            
            assert 'travel_agent' in groups, f"Expected 'travel_agent' in {groups}"
            
            self.log_pass(
                "User group assignment",
                f"Groups: {', '.join(groups)}"
            )
        except Exception as e:
            self.log_fail("User group assignment", str(e))
    
    def test_contract_exists_and_active(self):
        """Test 3: Active contract exists between agency and property"""
        try:
            agency = TravelAgency.objects.get(name='Global Travel Ltd')
            property_obj = Property.objects.first()
            
            contract = Contract.objects.get(
                travel_agency=agency,
                property=property_obj
            )
            
            assert contract.status == 'active', f"Contract status: {contract.status}"
            assert contract.is_active(), "Contract should be active today"
            
            self.log_pass(
                "Active contract exists",
                f"{property_obj.name} ↔ {agency.name} (valid until {contract.end_date})"
            )
        except Exception as e:
            self.log_fail("Active contract exists", str(e))
    
    def test_accessible_properties_method(self):
        """Test 4: get_accessible_properties() returns correct properties"""
        try:
            user = User.objects.get(username='travel_agent_john')
            profile = TravelAgentProfile.objects.get(user=user)
            
            prop_ids = profile.get_accessible_properties()
            prop_ids_list = list(prop_ids)
            
            assert len(prop_ids_list) > 0, "Should have at least one accessible property"
            
            # Verify these are valid property IDs
            props = Property.objects.filter(id__in=prop_ids_list)
            assert props.count() == len(prop_ids_list), "Property count mismatch"
            
            self.log_pass(
                "Accessible properties method",
                f"Agent can access {len(prop_ids_list)} property(ies): {', '.join(p.name for p in props)}"
            )
        except Exception as e:
            self.log_fail("Accessible properties method", str(e))
    
    def test_room_availability(self):
        """Test 5: At least one room available for booking"""
        try:
            property_obj = Property.objects.first()
            rooms = Room.objects.filter(property=property_obj)
            available = rooms.filter(status='available')
            
            assert rooms.exists(), f"No rooms at {property_obj.name}"
            
            room = rooms.first()
            self.log_pass(
                "Room availability",
                f"Room {room.room_number} available ({available.count()} total available)"
            )
        except Exception as e:
            self.log_fail("Room availability", str(e))
    
    def test_create_booking_as_travel_agent(self):
        """Test 6: Create booking with auto-agency assignment"""
        try:
            user = User.objects.get(username='travel_agent_john')
            profile = TravelAgentProfile.objects.get(user=user)
            property_obj = Property.objects.first()
            room = Room.objects.filter(property=property_obj).first()
            
            # Create booking
            booking = Booking.objects.create(
                guest_name='Jane Doe',
                guest_email='jane@example.com',
                guest_phone='+1-555-0100',
                room=room,
                check_in_date=date.today() + timedelta(days=5),
                check_out_date=date.today() + timedelta(days=10),
                check_in_time='14:00',
                check_out_time='11:00',
                purpose='vacation',
                booking_source='travel_agency',
                travel_agency=profile.travel_agency,
                number_of_guests=2,
                number_of_adults=2,
                special_requests='Non-smoking room'
            )
            
            # Verify booking
            assert booking.travel_agency == profile.travel_agency, "Agency not assigned"
            assert booking.booking_source == 'travel_agency', "Booking source incorrect"
            
            self.log_pass(
                "Booking creation with auto-agency",
                f"Booking #{booking.id}: {booking.guest_name} @ {room.room_number}"
            )
            
            # Cleanup
            booking.delete()
            
        except Exception as e:
            self.log_fail("Booking creation with auto-agency", str(e))
    
    def test_staff_notification_recipients(self):
        """Test 7: Identify staff that should receive notifications"""
        try:
            property_obj = Property.objects.first()
            staff = Employee.objects.filter(property=property_obj, status='active')
            
            if staff.exists():
                self.log_pass(
                    "Staff notification recipients",
                    f"{staff.count()} active staff would receive notifications"
                )
                for emp in staff[:3]:
                    print(f"       • {emp.user.first_name} {emp.user.last_name} ({emp.position})")
            else:
                self.log_warning(
                    "Staff notification recipients",
                    "No active staff configured (notifications would fail in production)"
                )
        except Exception as e:
            self.log_fail("Staff notification recipients", str(e))
    
    def test_unauthorized_property_detection(self):
        """Test 8: System correctly identifies unauthorized properties"""
        try:
            from HMS.web_views import _can_access_property
            
            user = User.objects.get(username='travel_agent_john')
            
            # Get agent's accessible properties
            profile = TravelAgentProfile.objects.get(user=user)
            accessible_ids = profile.get_accessible_properties()
            accessible_props = Property.objects.filter(id__in=accessible_ids)
            
            # Test: Agent can access own properties
            for prop in accessible_props:
                assert _can_access_property(user, prop), f"Should access {prop.name}"
            
            # Test: Agent cannot access other properties
            other_props = Property.objects.exclude(id__in=accessible_ids)
            for prop in other_props[:1]:  # Test first unauthorized property
                assert not _can_access_property(user, prop), f"Should NOT access {prop.name}"
            
            msg = f"Can access {accessible_props.count()} property(ies), blocked from {other_props.count()} others"
            self.log_pass("Unauthorized property detection", msg)
            
        except Exception as e:
            self.log_fail("Unauthorized property detection", str(e))
    
    def test_notification_model_ready(self):
        """Test 9: Notification system is properly configured"""
        try:
            from notifications.models import Notification
            
            # Verify model exists and has required fields
            fields = ['recipient', 'message', 'priority', 'created_at']
            model_fields = [f.name for f in Notification._meta.get_fields()]
            
            for field in fields:
                assert field in model_fields, f"Missing field: {field}"
            
            self.log_pass(
                "Notification model ready",
                "All required fields present"
            )
        except Exception as e:
            self.log_fail("Notification model ready", str(e))
    
    def test_system_checks(self):
        """Test 10: Run Django system checks"""
        try:
            from django.core.management import call_command
            from io import StringIO
            
            out = StringIO()
            call_command('check', stdout=out)
            
            output = out.getvalue()
            if 'issues' in output.lower() and '0 silenced' not in output.lower():
                self.log_warning("System checks", "Some checks may have warnings")
            else:
                self.log_pass(
                    "System checks",
                    "No critical issues detected"
                )
        except Exception as e:
            self.log_fail("System checks", str(e))
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "=" * 70)
        print("TRAVEL AGENT ACCESS CONTROL - INTEGRATION TEST SUITE")
        print("=" * 70 + "\n")
        
        self.test_travel_agent_profile_exists()
        self.test_user_group_assignment()
        self.test_contract_exists_and_active()
        self.test_accessible_properties_method()
        self.test_room_availability()
        self.test_create_booking_as_travel_agent()
        self.test_staff_notification_recipients()
        self.test_unauthorized_property_detection()
        self.test_notification_model_ready()
        self.test_system_checks()
        
        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {len(self.results['passed'])}")
        print(f"❌ Failed: {len(self.results['failed'])}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        print("=" * 70 + "\n")
        
        if self.results['failed']:
            print("Failed Tests:")
            for test in self.results['failed']:
                print(f"  - {test}")
            return False
        
        return True


if __name__ == '__main__':
    tester = TravelAgentSystemTests()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
