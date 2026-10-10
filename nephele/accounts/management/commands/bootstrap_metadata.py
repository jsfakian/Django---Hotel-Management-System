from django.apps import apps
from django.contrib.auth.management import create_permissions
from django.contrib.contenttypes.management import create_contenttypes
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Populate/refresh django_content_type and auth_permission rows.'

    def handle(self, *args, **options):
        app_configs = list(apps.get_app_configs())

        for app_config in app_configs:
            create_contenttypes(app_config, verbosity=0)

        for app_config in app_configs:
            create_permissions(app_config, verbosity=0)

        self.stdout.write(self.style.SUCCESS('Metadata bootstrap complete: content types and permissions are synced.'))
