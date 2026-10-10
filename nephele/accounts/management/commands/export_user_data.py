"""
Django management command: export_user_data

Exports all user data for GDPR compliance (Article 20 - Right to Data Portability)

Usage:
    python manage.py export_user_data <user_id> [--format=json|csv] [--output=/path/to/file]
    python manage.py export_user_data <email> --by-email [--format=json]
"""
import json
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone

from ...services.gdpr_export import GDPRExportService, GDPRDataSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to export user data for GDPR compliance"""
    
    help = 'Export all user data for GDPR Data Subject Access Request (DSAR)'
    
    def add_arguments(self, parser):
        """Add command arguments"""
        parser.add_argument(
            'user_identifier',
            type=str,
            help='User ID or email address'
        )
        parser.add_argument(
            '--by-email',
            action='store_true',
            help='Treat user_identifier as email instead of user ID'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='Export format (default: json)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: exports/user_<id>_<date>.json)'
        )
        parser.add_argument(
            '--archive',
            action='store_true',
            help='Create ZIP archive with exported data'
        )
    
    def handle(self, *args, **options):
        """Execute the command"""
        user_identifier = options['user_identifier']
        by_email = options['by_email']
        output_format = options['format']
        output_path = options['output']
        create_archive = options['archive']
        
        try:
            # Find the user
            user = self._get_user(user_identifier, by_email)
            
            self.stdout.write(
                self.style.SUCCESS(f'Found user: {user.username} ({user.email})')
            )
            
            # Export user data
            self.stdout.write('Exporting user data...')
            service = GDPRExportService(user)
            export_data = service.export_to_dict()
            
            # Determine output path
            if not output_path:
                output_path = self._generate_output_path(user, output_format)
            
            # Create output directory if needed
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write data to file
            if output_format == 'json':
                self._write_json_export(export_data, output_path)
            elif output_format == 'csv':
                self._write_csv_export(export_data, output_path)
            
            # Create archive if requested
            if create_archive:
                archive_path = self._create_archive(output_path)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Archive created: {archive_path}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Export completed: {output_path}')
                )
            
            # Log the export
            self._log_export(user, output_path)
            
        except User.DoesNotExist:
            raise CommandError(
                f'User not found: {user_identifier}'
            )
        except Exception as e:
            logger.error(f'Error exporting user data: {str(e)}')
            raise CommandError(f'Export failed: {str(e)}')
    
    def _get_user(self, identifier: str, by_email: bool) -> User:
        """Get user by ID or email"""
        if by_email:
            return User.objects.get(email=identifier)
        else:
            try:
                user_id = int(identifier)
                return User.objects.get(id=user_id)
            except ValueError:
                # Try email if numeric conversion fails
                return User.objects.get(email=identifier)
    
    def _write_json_export(self, data: dict, output_path: str) -> None:
        """Write export data to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=GDPRDataSerializer, indent=2)
        
        self.stdout.write(f'Exported to: {output_path}')
    
    def _write_csv_export(self, data: dict, output_path: str) -> None:
        """Write export data to CSV files (one per data category)"""
        import csv
        
        base_path = Path(output_path).stem
        base_dir = Path(output_path).parent
        
        # Export user profile
        if data.get('user_profile'):
            csv_path = base_dir / f'{base_path}_user_profile.csv'
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data['user_profile'].keys())
                writer.writeheader()
                writer.writerow(data['user_profile'])
            self.stdout.write(f'Exported to: {csv_path}')
        
        # Export bookings
        if data.get('bookings'):
            csv_path = base_dir / f'{base_path}_bookings.csv'
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = data['bookings'][0].keys() if data['bookings'] else []
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data['bookings'])
            self.stdout.write(f'Exported to: {csv_path}')
        
        # Export payments
        if data.get('payments'):
            csv_path = base_dir / f'{base_path}_payments.csv'
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = data['payments'][0].keys() if data['payments'] else []
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data['payments'])
            self.stdout.write(f'Exported to: {csv_path}')
    
    def _generate_output_path(self, user: User, format: str) -> str:
        """Generate default output file path"""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'user_{user.id}_{timestamp}.{format}'
        return f'exports/{filename}'
    
    def _create_archive(self, file_path: str) -> str:
        """Create ZIP archive of exported files"""
        import shutil
        
        file_path = Path(file_path)
        base_dir = file_path.parent
        archive_name = f'{file_path.stem}_archive'
        archive_path = base_dir / archive_name
        
        # Create ZIP archive
        shutil.make_archive(
            str(archive_path),
            'zip',
            base_dir,
            file_path.name
        )
        
        return f'{archive_path}.zip'
    
    def _log_export(self, user: User, file_path: str) -> None:
        """Log the export for audit purposes"""
        try:
            from django.contrib.admin.models import LogEntry, ADDITION
            
            LogEntry.objects.create(
                user=None,  # System action
                content_type_id=None,
                object_id=str(user.id),
                object_repr=f'GDPR Export - {user.email}',
                action_flag=ADDITION,
                change_message=f'GDPR Data Subject Access Request export to {file_path}',
            )
            logger.info(f'GDPR export logged for user {user.id}: {file_path}')
        except Exception as e:
            logger.warning(f'Could not log export: {str(e)}')
