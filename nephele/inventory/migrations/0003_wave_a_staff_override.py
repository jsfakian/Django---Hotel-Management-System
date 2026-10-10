# Generated manually for Wave A staff override audit fields

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inventory", "0002_webhotelier_parity_p0_p2"),
    ]

    operations = [
        migrations.AddField(
            model_name="roomtypeavailability",
            name="staff_override",
            field=models.BooleanField(
                default=False,
                help_text="When True, automated allotment backfill will not overwrite this row",
            ),
        ),
        migrations.AddField(
            model_name="roomtypeavailability",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="room_type_availability_updates",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
