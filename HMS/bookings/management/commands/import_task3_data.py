import csv
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from properties.models import Property
from room.models import Room
from bookings.models import PricingHistory, CompetitorPrice


class Command(BaseCommand):
    help = 'Import Task3 CSV data into Property/Room/PricingHistory/CompetitorPrice models.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default='../task3-data',
            help='Path to task3-data directory relative to manage.py (default: ../task3-data)',
        )

    def handle(self, *args, **options):
        data_dir = (Path.cwd() / options['data_dir']).resolve()
        if not data_dir.exists():
            raise CommandError(f'Data directory does not exist: {data_dir}')

        self._assert_required_tables()

        properties_file = data_dir / 'properties.csv'
        rooms_file = data_dir / 'rooms.csv'
        pricing_history_file = data_dir / 'pricing_history.csv'
        competitor_pricing_file = data_dir / 'competitor_pricing.csv'

        for required_file in [properties_file, rooms_file, pricing_history_file, competitor_pricing_file]:
            if not required_file.exists():
                raise CommandError(f'Missing required file: {required_file}')

        with transaction.atomic():
            properties_by_code = self._import_properties(properties_file)
            rooms_by_property = self._import_rooms(rooms_file, properties_by_code)
            self._import_pricing_history(pricing_history_file, rooms_by_property)
            self._import_competitor_pricing(competitor_pricing_file, rooms_by_property)

        self.stdout.write(self.style.SUCCESS('Task3 data import completed successfully.'))

    def _assert_required_tables(self):
        required_tables = {
            'properties_property',
            'room_room',
            'bookings_pricinghistory',
            'bookings_competitorprice',
        }
        existing_tables = set(connection.introspection.table_names())
        missing_tables = sorted(required_tables - existing_tables)
        if missing_tables:
            missing = ', '.join(missing_tables)
            raise CommandError(
                f'Missing required database tables: {missing}. Run `python manage.py migrate` first.'
            )

        with connection.cursor() as cursor:
            room_columns = {
                column.name
                for column in connection.introspection.get_table_description(cursor, 'room_room')
            }
        if 'id' not in room_columns:
            raise CommandError(
                'Detected legacy `room_room` schema without `id` primary key column. '
                'Current ORM expects modern room schema; run schema alignment migration/reset before importing Task3 data.'
            )

    def _import_properties(self, properties_file):
        properties_by_code = {}
        created_count = 0
        updated_count = 0

        with properties_file.open('r', encoding='utf-8', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                property_code = (row.get('property_id') or '').strip()
                if not property_code:
                    continue

                city = (row.get('city') or 'Unknown City').strip() or 'Unknown City'
                country = (row.get('country') or 'Unknown Country').strip() or 'Unknown Country'
                address = (row.get('address') or f'{city}, {country}').strip() or f'{city}, {country}'
                total_rooms = self._safe_int(row.get('total_rooms'), 0)

                property_obj, created = Property.objects.update_or_create(
                    name=property_code,
                    defaults={
                        'location': city,
                        'address': address,
                        'city': city,
                        'postal_code': (row.get('postal_code') or '00000').strip() or '00000',
                        'country': country,
                        'phone_number': (row.get('phone_number') or '').strip(),
                        'email': (row.get('email') or '').strip(),
                        'total_rooms': total_rooms,
                        'is_active': True,
                    },
                )

                properties_by_code[property_code] = property_obj
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            f'Properties imported: created={created_count}, updated={updated_count}'
        )
        return properties_by_code

    def _import_rooms(self, rooms_file, properties_by_code):
        rooms_by_property = {}
        created_count = 0
        updated_count = 0

        with rooms_file.open('r', encoding='utf-8', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                property_code = (row.get('property_id') or '').strip()
                property_obj = properties_by_code.get(property_code)
                if not property_obj:
                    continue

                source_room_number = (row.get('room_number') or '').strip() or '0'
                room_number = f'{property_code}-{source_room_number}'
                room_type = self._map_room_type(row.get('room_type'))
                base_price = self._safe_decimal(row.get('base_price_per_night'), 100)

                room_obj, created = Room.objects.update_or_create(
                    room_number=room_number,
                    defaults={
                        'property': property_obj,
                        'floor': self._safe_int(row.get('floor'), 1),
                        'room_type': room_type,
                        'capacity': max(1, self._safe_int(row.get('capacity'), 1)),
                        'number_of_beds': max(1, self._safe_int(row.get('capacity'), 1)),
                        'base_price': base_price,
                        'current_price': base_price,
                        'status': 'available',
                        'amenities': self._parse_amenities(row.get('amenities')),
                    },
                )

                rooms_by_property.setdefault(property_code, []).append(room_obj)
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            f'Rooms imported: created={created_count}, updated={updated_count}'
        )
        return rooms_by_property

    def _import_pricing_history(self, pricing_history_file, rooms_by_property):
        created_count = 0
        updated_count = 0

        with pricing_history_file.open('r', encoding='utf-8', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                property_code = (row.get('property_id') or '').strip()
                anchor_room = self._get_anchor_room(rooms_by_property, property_code)
                if not anchor_room:
                    continue

                record_date = self._safe_date(row.get('date'))
                if not record_date:
                    continue

                defaults = {
                    'weekday': record_date.weekday(),
                    'base_price': self._safe_decimal(row.get('average_nightly_rate'), 0),
                    'dynamic_price': self._safe_decimal(row.get('average_nightly_rate'), 0),
                    'occupancy_rate': self._safe_decimal(row.get('occupancy_rate'), 0) * 100,
                    'bookings_count': self._safe_int(row.get('occupied_rooms'), 0),
                    'season': self._map_season(row.get('season')),
                    'predicted_by_model': False,
                    'model_version': 'task3-import-v1',
                }

                _, created = PricingHistory.objects.update_or_create(
                    room=anchor_room,
                    date=record_date,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            f'Pricing history imported: created={created_count}, updated={updated_count}'
        )

    def _import_competitor_pricing(self, competitor_pricing_file, rooms_by_property):
        created_count = 0
        updated_count = 0

        with competitor_pricing_file.open('r', encoding='utf-8', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                property_code = (row.get('property_id') or '').strip()
                anchor_room = self._get_anchor_room(rooms_by_property, property_code)
                if not anchor_room:
                    continue

                record_date = self._safe_date(row.get('date'))
                competitor_name = (row.get('competitor_name') or '').strip() or 'Unknown Competitor'
                if not record_date:
                    continue

                defaults = {
                    'price': self._safe_decimal(row.get('competitor_price'), 0),
                    'source_url': '',
                }

                _, created = CompetitorPrice.objects.update_or_create(
                    room=anchor_room,
                    competitor_name=competitor_name,
                    date=record_date,
                    defaults=defaults,
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            f'Competitor prices imported: created={created_count}, updated={updated_count}'
        )

    @staticmethod
    def _get_anchor_room(rooms_by_property, property_code):
        rooms = rooms_by_property.get(property_code) or []
        return rooms[0] if rooms else None

    @staticmethod
    def _safe_int(value, default):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_decimal(value, default):
        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_date(value):
        try:
            return date.fromisoformat((value or '').strip())
        except ValueError:
            return None

    @staticmethod
    def _parse_amenities(value):
        if not value:
            return []
        return [item.strip() for item in str(value).split('|') if item.strip()]

    @staticmethod
    def _map_room_type(source_type):
        source = (source_type or '').strip().lower()
        mapping = {
            'standard': 'single',
            'single': 'single',
            'double': 'double',
            'suite': 'suite',
            'deluxe': 'deluxe',
            'luxury': 'luxury',
            'economic': 'economic',
        }
        return mapping.get(source, 'single')

    @staticmethod
    def _map_season(source_season):
        source = (source_season or '').strip().lower()
        mapping = {
            'low': 'low',
            'winter': 'low',
            'medium': 'medium',
            'spring': 'medium',
            'autumn': 'medium',
            'high': 'high',
            'summer': 'high',
            'peak': 'peak',
        }
        return mapping.get(source, 'medium')
