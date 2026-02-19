"""
Analytics Tests
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from properties.models import Property
from .models import (
    DashboardExecutiveMetrics,
    DashboardOperationalStatus,
    DashboardRevenueMetrics,
    DashboardGuestAnalytics,
    CustomReport,
)

User = get_user_model()


class DashboardMetricsTestCase(TestCase):
    """Tests for dashboard metrics models"""
    
    def setUp(self):
        """Set up test data"""
        # Use minimal fields to avoid migration/model mismatch issues
        self.property = Property.objects.create(
            name=f'Hotel {hash(self)%10000}',
            location='Test Location',
            address='123 Test St',
            city='Test City',
            postal_code='12345',
            country='Test Country'
        )
    
    def test_executive_metrics_creation(self):
        """Test creating executive metrics"""
        metric = DashboardExecutiveMetrics.objects.create(
            property=self.property,
            metric_date='2026-02-19',
            total_revenue=5000.00,
            avg_daily_rate=150.00,
            occupancy_rate=85.00,
            revpar=127.50,
            booking_count=42,
        )
        
        self.assertEqual(metric.property.id, self.property.id)
        self.assertEqual(metric.occupancy_rate, 85.00)
        self.assertTrue(metric.id)
    
    def test_operational_status_creation(self):
        """Test creating operational status"""

        status = DashboardOperationalStatus.objects.create(
            property=self.property,
            status_date='2026-02-19',
            status_time=timezone.now(),
            occupied_count=42,
            vacant_count=8,
            cleaning_count=0,
        )
        
        self.assertEqual(status.occupied_count, 42)
        total_rooms = status.occupied_count + status.vacant_count + status.cleaning_count
        self.assertEqual(total_rooms, 50)
    
    def test_revenue_metrics_creation(self):
        """Test creating revenue metrics"""
        metric = DashboardRevenueMetrics.objects.create(
            property=self.property,
            metric_date='2026-02-19',
            total_revenue=5000.00,
            revenue_direct=2500.00,
            revenue_ota=1500.00,
            revenue_agency=1000.00,
            avg_daily_rate=150.00,
            revpar=127.50,
            occupancy_rate=85.00,
            booking_count=42,
        )
        
        self.assertAlmostEqual(metric.total_revenue, 5000.00)
        self.assertAlmostEqual(
            metric.revenue_direct + metric.revenue_ota + metric.revenue_agency,
            metric.total_revenue
        )
    
    def test_guest_analytics_creation(self):
        """Test creating guest analytics"""
        analytics = DashboardGuestAnalytics.objects.create(
            property=self.property,
            analytics_date='2026-02-19',
            total_unique_guests=42,
            new_guests=10,
            returning_guests=32,
            retention_rate=76.19,
            avg_review_score=4.5,
        )
        
        self.assertEqual(analytics.total_unique_guests, 42)
        self.assertEqual(
            analytics.new_guests + analytics.returning_guests,
            analytics.total_unique_guests
        )


class CustomReportTestCase(TestCase):
    """Tests for custom reports"""
    
    def setUp(self):
        """Set up test data"""
        # Use minimal fields to avoid migration/model mismatch issues
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        self.property = Property.objects.create(
            name=f'Report Hotel {hash(self)%10000}',
            location='Test Location',
            address='123 Test St',
            city='Test City',
            postal_code='12345',
            country='Test Country'
        )
    
    def test_custom_report_creation(self):
        """Test creating custom report"""
        import datetime
        
        report = CustomReport.objects.create(
            property=self.property,
            created_by=self.user,
            name='Monthly Revenue Report',
            report_type='revenue',
            from_date=datetime.date(2026, 2, 1),
            to_date=datetime.date(2026, 2, 28),
            export_format='pdf',
        )
        
        self.assertEqual(report.name, 'Monthly Revenue Report')
        self.assertEqual(report.status, 'pending')
        self.assertEqual(report.created_by, self.user)
    
    def test_report_status_workflow(self):
        """Test report status workflow"""
        import datetime
        
        report = CustomReport.objects.create(
            property=self.property,
            created_by=self.user,
            name='Test Report',
            report_type='custom',
            from_date=datetime.date(2026, 2, 1),
            to_date=datetime.date(2026, 2, 28),
        )
        
        # Initially pending
        self.assertEqual(report.status, 'pending')
        
        # Update to generated
        report.status = 'generated'
        report.file_path = '/reports/test-report.pdf'
        report.save()
        
        # Verify updates
        refreshed = CustomReport.objects.get(pk=report.pk)
        self.assertEqual(refreshed.status, 'generated')
        self.assertEqual(refreshed.file_path, '/reports/test-report.pdf')
