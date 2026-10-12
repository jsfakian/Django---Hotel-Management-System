import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "analytics",
            "0003_rename_custom_reports_property_created_idx_custom_repo_propert_edd07d_idx_and_more",
        ),
        ("properties", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customreport",
            name="report_type",
            field=models.CharField(
                choices=[
                    ("revenue", "Revenue Report"),
                    ("occupancy", "Occupancy Report"),
                    ("guest", "Guest Analytics Report"),
                    ("pricing", "Pricing Analysis Report"),
                    ("booking", "Bookings Report"),
                    ("payment", "Payments Report"),
                    ("custom", "Executive Summary"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="customreport",
            name="property",
            field=models.ForeignKey(
                blank=True,
                help_text="Empty means all properties",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="custom_reports",
                to="properties.property",
            ),
        ),
        migrations.AddField(
            model_name="cancellationprediction",
            name="risk_factors",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="noshowprediction",
            name="risk_factors",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
