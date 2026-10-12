"""
Recompute stored analytics (daily metrics, forecasts, risk predictions).

    python manage.py rebuild_analytics --days 90
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from analytics import tasks
from properties.models import Property


class Command(BaseCommand):
    help = "Backfill daily dashboard metrics and regenerate forecasts and predictions."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90, help="Days of history")
        parser.add_argument("--property-id", type=int, help="Limit to one property")
        parser.add_argument("--forecast-days", type=int, default=30)

    def handle(self, *args, **opts):
        today = timezone.localdate()
        properties = Property.objects.all()
        if opts["property_id"]:
            properties = properties.filter(id=opts["property_id"])

        for prop in properties:
            for offset in range(opts["days"], -1, -1):
                day = today - timedelta(days=offset)
                tasks.calculate_executive_metrics(property_id=prop.id, metric_date=day)
                tasks.calculate_revenue_metrics(property_id=prop.id, metric_date=day)
                if offset % 7 == 0:
                    tasks.calculate_guest_analytics(
                        property_id=prop.id, analytics_date=day
                    )
            tasks.calculate_operational_status(property_id=prop.id)
            tasks.forecast_occupancy_task(
                property_id=prop.id, forecast_days=opts["forecast_days"]
            )
            tasks.forecast_revenue_task(
                property_id=prop.id, forecast_days=opts["forecast_days"]
            )
            tasks.predict_cancellations_task(property_id=prop.id)
            tasks.predict_noshow_task(property_id=prop.id)
            self.stdout.write(f"  {prop.name}: done")

        self.stdout.write(self.style.SUCCESS("✓ Analytics rebuilt"))
