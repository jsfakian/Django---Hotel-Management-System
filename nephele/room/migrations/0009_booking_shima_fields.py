# nephele/room/migrations/0009_booking_shima_fields.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("room", "0008_datefield_localdate_defaults"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="mhte_registry_number",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="booking",
            name="shima_stay_purpose",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
