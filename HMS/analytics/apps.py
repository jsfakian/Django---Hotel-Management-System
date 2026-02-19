from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'
    verbose_name = 'Business Intelligence & Analytics'

    def ready(self):
        """Initialize analytics tasks on app startup"""
        from django.core.management import call_command
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info("Analytics app initialized")
