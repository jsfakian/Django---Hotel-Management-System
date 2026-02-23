"""
Management command to load comprehensive demo data for system testing.

This command populates:
- Properties (hotels)
- Rooms
- Guests
- Bookings (with various statuses for testing)
- Pricing history (for dynamic pricing and forecasting)
- Travel agencies
- Analytics data (for BI demonstrations)
"""

import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from properties.models import Property, TravelAgency
from room.models import Room, Booking
from accounts.models import Guest
from bookings.models import PricingHistory, CompetitorPrice
from analytics.models import (
    DashboardExecutiveMetrics,
    DashboardOperationalStatus,
    DashboardRevenueMetrics,
)


class Command(BaseCommand):
    help = 'Load comprehensive demo data for system testing and demonstrations.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fixtures-dir',
            default='fixtures',
            help='Path to fixtures directory (default: fixtures)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before loading new data',
        )

    def handle(self, *args, **options):
        fixtures_dir = Path(options['fixtures_dir'])
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing demo data...'))
            self._clear_demo_data()

        if not fixtures_dir.exists():
            fixtures_dir.mkdir(parents=True, exist_ok=True)
            self.stdout.write(
                self.style.WARNING(f'Fixtures directory created at {fixtures_dir}')
            )

        demo_data_file = fixtures_dir / 'demo_data.json'
        if not demo_data_file.exists():
            raise CommandError(f'Demo data file not found: {demo_data_file}')

        try:
            with open(demo_data_file, 'r', encoding='utf-8') as f:
                demo_data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON in demo data file: {e}')

        with transaction.atomic():
            self._load_properties(demo_data.get('properties', []))
            self._load_guests(demo_data.get('guests', []))
            self._load_rooms(demo_data.get('rooms', []))
            self._load_travel_agencies(demo_data.get('travel_agencies', []))
            self._load_bookings(demo_data.get('bookings', []))
            self._load_pricing_history(demo_data.get('pricing_history', []))
            self._load_analytics_data(demo_data.get('analytics', []))

        self.stdout.write(self.style.SUCCESS('✓ Demo data loaded successfully'))

    def _clear_demo_data(self):
        """Clear demo data while preserving admin user"""
        # Delete in reverse order of dependencies
        DashboardExecutiveMetrics.objects.all().delete()
        DashboardOperationalStatus.objects.all().delete()
        DashboardRevenueMetrics.objects.all().delete()
        
        PricingHistory.objects.all().delete()
        CompetitorPrice.objects.all().delete()
        Booking.objects.all().delete()
        
        Room.objects.all().delete()
        TravelAgency.objects.all().delete()
        Property.objects.all().delete()
        
        # Keep admin user, only delete demo guests
        Guest.objects.filter(email__startswith='demo_').delete()
        User.objects.filter(username__startswith='demo_').delete()
        
        self.stdout.write(self.style.SUCCESS('✓ Demo data cleared'))

    def _load_properties(self, properties_data):
        """Load property data"""
        count = 0
        for prop_data in properties_data:
            property_obj, created = Property.objects.get_or_create(
                name=prop_data['name'],
                defaults={
                    'location': prop_data.get('location', prop_data['name']),
                    'address': prop_data.get('address', f"123 {prop_data['name']} St"),
                    'city': prop_data.get('city', 'Demo City'),
                    'postal_code': prop_data.get('postal_code', '12345'),
                    'country': prop_data.get('country', 'Demo Country'),
                    'phone_number': prop_data.get('phone_number', '+1-555-0100'),
                    'email': prop_data.get('email', f"info@{prop_data['name'].lower()}.demo"),
                    'website': prop_data.get('website', f"https://{prop_data['name'].lower()}.demo"),
                    'total_rooms': prop_data.get('total_rooms', 50),
                    'star_rating': prop_data.get('star_rating', 4),
                    'is_active': True,
                }
            )
            if created:
                count += 1

        self.stdout.write(f'  Properties: {count} created')

    def _load_guests(self, guests_data):
        """Load guest data"""
        count = 0
        for guest_data in guests_data:
            guest_obj, created = Guest.objects.get_or_create(
                email=guest_data['email'],
                defaults={
                    'first_name': guest_data.get('first_name', 'Demo'),
                    'last_name': guest_data.get('last_name', 'Guest'),
                    'phone_number': guest_data.get('phone_number', '+1-555-0100'),
                    'address': guest_data.get('address', '123 Demo St'),
                    'city': guest_data.get('city', 'Demo City'),
                    'country': guest_data.get('country', 'Demo Country'),
                    'postal_code': guest_data.get('postal_code', '12345'),
                    'preferences': guest_data.get('preferences', {}),
                    'number_of_bookings': guest_data.get('number_of_bookings', 0),
                    'total_nights_stayed': guest_data.get('total_nights_stayed', 0),
                }
            )
            if created:
                count += 1

        self.stdout.write(f'  Guests: {count} created')

    def _load_rooms(self, rooms_data):
        """Load room data"""
        count = 0
        for room_data in rooms_data:
            property_obj = Property.objects.get(name=room_data['property'])
            
            room_obj, created = Room.objects.get_or_create(
                room_number=room_data['room_number'],
                defaults={
                    'property': property_obj,
                    'floor': room_data.get('floor', 1),
                    'room_type': room_data.get('room_type', 'double'),
                    'capacity': room_data.get('capacity', 2),
                    'number_of_beds': room_data.get('number_of_beds', 1),
                    'base_price': Decimal(str(room_data.get('base_price', '100.00'))),
                    'current_price': Decimal(str(room_data.get('current_price', '100.00'))),
                    'status': room_data.get('status', 'available'),
                    'amenities': room_data.get('amenities', []),
                }
            )
            if created:
                count += 1

        self.stdout.write(f'  Rooms: {count} created')

    def _load_travel_agencies(self, agencies_data):
        """Load travel agency data"""
        count = 0
        for agency_data in agencies_data:
            agency_obj, created = TravelAgency.objects.get_or_create(
                name=agency_data['name'],
                defaults={
                    'description': agency_data.get('description', ''),
                    'contact_name': agency_data.get('contact_name', 'Contact'),
                    'email': agency_data.get('email', f"contact@{agency_data['name'].lower()}.demo"),
                    'phone': agency_data.get('phone', '+1-555-0100'),
                    'address': agency_data.get('address', '123 Agency St'),
                    'city': agency_data.get('city', 'Demo City'),
                    'country': agency_data.get('country', 'Demo Country'),
                    'status': agency_data.get('status', 'active'),
                    'commission_percentage': Decimal(str(agency_data.get('commission_rate', '10.00'))),
                }
            )
            if created:
                count += 1

        self.stdout.write(f'  Travel Agencies: {count} created')

    def _load_bookings(self, bookings_data):
        """Load booking data"""
        count = 0
        for booking_data in bookings_data:
            room_obj = Room.objects.get(room_number=booking_data['room_number'])
            guest_obj = Guest.objects.get(email=booking_data['guest_email'])
            
            check_in = self._parse_date(booking_data['check_in_date'])
            check_out = self._parse_date(booking_data['check_out_date'])
            
            booking_obj, created = Booking.objects.get_or_create(
                room=room_obj,
                guest=guest_obj,
                check_in_date=check_in,
                check_out_date=check_out,
                defaults={
                    'date_of_reservation': self._parse_date(booking_data.get('date_of_reservation', str(date.today()))),
                    'number_of_guests': booking_data.get('number_of_guests', 1),
                    'status': booking_data.get('status', 'confirmed'),
                    'base_price': Decimal(str(booking_data.get('base_price', '100.00'))),
                    'actual_price': Decimal(str(booking_data.get('actual_price', '100.00'))),
                    'booking_source': booking_data.get('booking_source', 'direct_website'),
                    'special_requests': booking_data.get('special_requests', ''),
                }
            )
            if created:
                count += 1

        self.stdout.write(f'  Bookings: {count} created')

    def _load_pricing_history(self, pricing_data):
        """Load pricing history data for BI and forecasting"""
        count = 0
        for price_data in pricing_data:
            room_obj = Room.objects.get(room_number=price_data['room_number'])
            history_date = self._parse_date(price_data['date'])
            
            price_obj, created = PricingHistory.objects.get_or_create(
                room=room_obj,
                date=history_date,
                defaults={
                    'weekday': history_date.weekday(),
                    'base_price': Decimal(str(price_data.get('base_price', '100.00'))),
                    'dynamic_price': Decimal(str(price_data.get('dynamic_price', '100.00'))),
                    'competitor_price': Decimal(str(price_data.get('competitor_price', '100.00'))),
                    'occupancy_rate': Decimal(str(price_data.get('occupancy_rate', '50.00'))),
                    'demand_score': Decimal(str(price_data.get('demand_score', '50.00'))),
                    'bookings_count': price_data.get('bookings_count', 0),
                    'cancellation_rate': Decimal(str(price_data.get('cancellation_rate', '5.00'))),
                    'season': price_data.get('season', 'medium'),
                    'external_events': price_data.get('external_events', ''),
                    'predicted_by_model': price_data.get('predicted_by_model', False),
                    'model_version': price_data.get('model_version', ''),
                    'confidence_score': Decimal(str(price_data.get('confidence_score', '0.00'))),
                }
            )
            if created:
                count += 1

        self.stdout.write(f'  Pricing History: {count} created')

    def _load_analytics_data(self, analytics_data):
        """Load analytics/dashboard data"""
        count = 0
        for metric_data in analytics_data:
            property_obj = Property.objects.get(name=metric_data['property'])
            metric_date = self._parse_date(metric_data['metric_date'])
            
            # Create executive metrics
            exec_metric, created = DashboardExecutiveMetrics.objects.get_or_create(
                property=property_obj,
                metric_date=metric_date,
                defaults={
                    'total_revenue': Decimal(str(metric_data.get('total_revenue', '5000.00'))),
                    'avg_daily_rate': Decimal(str(metric_data.get('avg_daily_rate', '150.00'))),
                    'occupancy_rate': Decimal(str(metric_data.get('occupancy_rate', '75.00'))),
                    'revpar': Decimal(str(metric_data.get('revpar', '112.50'))),
                    'booking_count': metric_data.get('booking_count', 10),
                    'revenue_trend_30d': metric_data.get('revenue_trend_30d', {}),
                    'occupancy_trend_30d': metric_data.get('occupancy_trend_30d', {}),
                    'adr_trend_30d': metric_data.get('adr_trend_30d', {}),
                    'yoy_revenue_change': Decimal(str(metric_data.get('yoy_revenue_change', '10.00'))),
                    'yoy_occupancy_change': Decimal(str(metric_data.get('yoy_occupancy_change', '5.00'))),
                }
            )
            if created:
                count += 1

        self.stdout.write(f'  Analytics Metrics: {count} created')

    def _parse_date(self, date_str):
        """Parse date string to date object"""
        if isinstance(date_str, str):
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            # If no format matched, try to parse as relative days
            if date_str.startswith('+'):
                days = int(date_str[1:])
                return date.today() + timedelta(days=days)
            elif date_str.startswith('-'):
                days = int(date_str[1:])
                return date.today() - timedelta(days=days)
        return date.today()
