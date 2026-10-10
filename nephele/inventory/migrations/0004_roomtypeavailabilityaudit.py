# Generated manually for Wave A availability audit trail

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inventory", "0003_wave_a_staff_override"),
    ]

    operations = [
        migrations.CreateModel(
            name="RoomTypeAvailabilityAudit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField()),
                ("old_allotment", models.PositiveIntegerField(blank=True, null=True)),
                ("new_allotment", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "old_staff_override",
                    models.BooleanField(blank=True, null=True),
                ),
                (
                    "new_staff_override",
                    models.BooleanField(blank=True, null=True),
                ),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("note", models.CharField(blank=True, default="", max_length=255)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="room_type_availability_audits",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "room_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="availability_audits",
                        to="inventory.roomtype",
                    ),
                ),
            ],
            options={
                "ordering": ["-changed_at"],
            },
        ),
        migrations.AddIndex(
            model_name="roomtypeavailabilityaudit",
            index=models.Index(
                fields=["room_type", "date"],
                name="inventory_r_room_ty_audit_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="roomtypeavailabilityaudit",
            index=models.Index(
                fields=["changed_at"],
                name="inventory_r_changed_audit_idx",
            ),
        ),
    ]
