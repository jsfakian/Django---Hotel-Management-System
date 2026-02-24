"""
GDPR Data Export and Privacy Tests
Tests for GDPR compliance (Articles 15, 17, 20)
"""
import json
from io import StringIO

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.management import call_command

from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import Guest, Employee, Role, TravelAgentProfile
from .services.gdpr_export import GDPRExportService, get_gdpr_export_json
from properties.models import Property, TravelAgency
from room.models import Booking
from payments.models import Payment, Invoice

User = get_user_model()


class GDPRExportServiceTests(TestCase):
    """Test GDPR data export service"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        # Create user
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create guest profile
        cls.guest = Guest.objects.create(
            user=cls.user,
            email='test@example.com',
            first_name='Test',
            last_name='User',
            phone_number='+301234567890',
            address='123 Test St',
            city='Test City',
            country='Greece',
            postal_code='12345'
        )
    
    def test_export_service_initialization(self):
        """Test service can be initialized with a user"""
        service = GDPRExportService(self.user)
        self.assertEqual(service.user, self.user)
        self.assertIsNotNone(service.export_date)
    
    def test_user_profile_export(self):
        """Test user profile data export"""
        service = GDPRExportService(self.user)
        profile = service._export_user_profile()
        
        self.assertEqual(profile['id'], self.user.id)
        self.assertEqual(profile['username'], 'testuser')
        self.assertEqual(profile['email'], 'test@example.com')
        self.assertEqual(profile['first_name'], 'Test')
        self.assertTrue(profile['is_active'])
    
    def test_guest_profile_export(self):
        """Test guest profile data export"""
        service = GDPRExportService(self.user)
        guest = service._export_guest_profile()
        
        self.assertIsNotNone(guest)
        self.assertEqual(guest['phone_number'], '+301234567890')
        self.assertEqual(guest['city'], 'Test City')
        self.assertEqual(guest['country'], 'Greece')
    
    def test_complete_export(self):
        """Test complete data export"""
        service = GDPRExportService(self.user)
        export_data = service.export_all_data()
        
        # Check structure
        self.assertIn('export_info', export_data)
        self.assertIn('user_profile', export_data)
        self.assertIn('guest_profile', export_data)
        self.assertIn('bookings', export_data)
        self.assertIn('payments', export_data)
        
        # Check export info
        self.assertEqual(export_data['export_info']['user_id'], self.user.id)
        self.assertIn('GDPR', export_data['export_info']['compliance'])
    
    def test_export_to_json_string(self):
        """Test JSON string export"""
        service = GDPRExportService(self.user)
        json_str = service.export_to_json_string()
        
        # Should be valid JSON
        data = json.loads(json_str)
        self.assertIsNotNone(data)
        self.assertEqual(data['user_profile']['email'], 'test@example.com')
    
    def test_export_to_dict(self):
        """Test dictionary export"""
        service = GDPRExportService(self.user)
        data = service.export_to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertIn('user_profile', data)


class ManagementCommandTests(TestCase):
    """Test management command for data export"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.user = User.objects.create_user(
            username='cmdtest',
            email='cmd@example.com',
            password='testpass123'
        )
    
    def test_export_command_by_id(self):
        """Test export command with user ID"""
        out = StringIO()
        call_command(
            'export_user_data',
            str(self.user.id),
            stdout=out
        )
        
        output = out.getvalue()
        self.assertIn('Found user', output)
        self.assertIn('Export completed', output)
    
    def test_export_command_by_email(self):
        """Test export command with email"""
        out = StringIO()
        call_command(
            'export_user_data',
            'cmd@example.com',
            '--by-email',
            stdout=out
        )
        
        output = out.getvalue()
        self.assertIn('Found user', output)
        self.assertIn('Export completed', output)
    
    def test_export_command_invalid_user(self):
        """Test export command with invalid user"""
        with self.assertRaises(Exception):
            call_command('export_user_data', '99999')


class GDPRAPITests(APITestCase):
    """Test GDPR API endpoints"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.user = User.objects.create_user(
            username='apitest',
            email='api@example.com',
            password='testpass123'
        )
        
        cls.guest = Guest.objects.create(
            user=cls.user,
            email='api@example.com',
            first_name='API',
            last_name='Test',
            phone_number='+301234567890'
        )
    
    def setUp(self):
        """Set up test client"""
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_request_export_anonymous(self):
        """Test export request without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.post(reverse('api:gdpr_request_export'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_request_export_small_data(self):
        """Test export request with small dataset"""
        response = self.client.post(
            reverse('api:gdpr_request_export'),
            {'send_email': False},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('data', response.data)
        self.assertIn('data_size_bytes', response.data)
    
    def test_download_export(self):
        """Test downloading export"""
        response = self.client.get(reverse('api:gdpr_download_export'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Check attachment header
        self.assertIn('Content-Disposition', response)
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_request_deletion_no_confirm(self):
        """Test deletion request without confirmation"""
        response = self.client.post(
            reverse('api:gdpr_request_deletion'),
            {'confirm': False},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_request_deletion_with_confirm(self):
        """Test deletion request with confirmation"""
        response = self.client.post(
            reverse('api:gdpr_request_deletion'),
            {
                'confirm': True,
                'reason': 'User requested deletion'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'requested')


class GDPRExportDataIntegrityTests(TestCase):
    """Test data integrity in GDPR exports"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        # Create user
        cls.user = User.objects.create_user(
            username='integrity',
            email='integrity@example.com',
            password='testpass123'
        )
        
        # Create guest
        cls.guest = Guest.objects.create(
            user=cls.user,
            email='integrity@example.com',
            first_name='Integrity',
            last_name='Test',
            phone_number='+301234567890',
            preferences={'language': 'en', 'currency': 'EUR'}
        )
        
        # Create property and booking
        cls.property = Property.objects.create(
            name='Test Hotel',
            manager=cls.user,
            address='123 Test St',
            city='Test City'
        )
    
    def test_export_contains_all_user_data_categories(self):
        """Test export contains all data categories"""
        service = GDPRExportService(self.user)
        data = service.export_all_data()
        
        required_keys = [
            'export_info',
            'user_profile',
            'guest_profile',
            'bookings',
            'payments',
            'invoices',
            'notifications',
        ]
        
        for key in required_keys:
            self.assertIn(key, data, f"Missing {key} in export")
    
    def test_export_has_valid_timestamps(self):
        """Test exported timestamps are ISO format"""
        service = GDPRExportService(self.user)
        data = service.export_all_data()
        
        # Check export date
        export_date = data['export_info']['export_date']
        # Should be ISO format (contains T)
        self.assertIn('T', export_date)
    
    def test_export_json_serializable(self):
        """Test exported data is JSON serializable"""
        service = GDPRExportService(self.user)
        data = service.export_all_data()
        
        # Should not raise exception
        json_str = json.dumps(data, default=str)
        self.assertIsInstance(json_str, str)
        self.assertGreater(len(json_str), 0)
    
    def test_guest_preferences_included(self):
        """Test guest preferences are exported"""
        service = GDPRExportService(self.user)
        guest_data = service._export_guest_profile()
        
        self.assertIsNotNone(guest_data['preferences'])
        self.assertEqual(guest_data['preferences']['language'], 'en')


class GDPRComplianceTests(TestCase):
    """Test GDPR compliance requirements"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.user = User.objects.create_user(
            username='compliance',
            email='compliance@example.com',
            password='testpass123'
        )
    
    def test_export_includes_dsar_metadata(self):
        """Test export includes Data Subject Access Request metadata"""
        service = GDPRExportService(self.user)
        data = service.export_all_data()
        
        export_info = data['export_info']
        
        # Check GDPR Article 20 compliance
        self.assertIn('Article 20', export_info['compliance'])
        self.assertIn('Data Portability', export_info['compliance'])
    
    def test_export_version_tracking(self):
        """Test export includes version information"""
        service = GDPRExportService(self.user)
        data = service.export_all_data()
        
        self.assertIn('export_version', data['export_info'])
        self.assertEqual(data['export_info']['export_version'], '1.0')
    
    def test_export_includes_user_identifier(self):
        """Test export includes clear user identification"""
        service = GDPRExportService(self.user)
        data = service.export_all_data()
        
        # Should include user ID and email for verification
        self.assertEqual(data['export_info']['user_id'], self.user.id)
        self.assertEqual(data['export_info']['user_email'], self.user.email)


@pytest.mark.django_db
class TestGDPRExportIntegration:
    """Integration tests for GDPR export (pytest style)"""
    
    def test_full_export_workflow(self, django_user_model):
        """Test complete export workflow"""
        # Create user
        user = django_user_model.objects.create_user(
            username='pytest_user',
            email='pytest@example.com',
            password='testpass'
        )
        
        # Create guest
        Guest.objects.create(user=user, phone='+301234567890')
        
        # Export
        service = GDPRExportService(user)
        data = service.export_to_dict()
        
        assert data['user_profile']['email'] == 'pytest@example.com'
        assert data['guest_profile'] is not None
