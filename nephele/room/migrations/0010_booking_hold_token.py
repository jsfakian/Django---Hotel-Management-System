# nephele/room/migrations/0010_booking_hold_token.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("room", "0009_booking_shima_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="hold_token",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Opaque token required for public hold confirm/cancel/modify",
                max_length=64,
                null=True,
                unique=True,
            ),
        ),
    ]
