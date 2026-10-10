from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("room", "0006_webhotelier_parity_p0_p2"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="guest_document_type",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="booking",
            name="guest_document_number",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="booking",
            name="guest_nationality",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="booking",
            name="guest_birth_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="booking",
            name="police_sheet_exported_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
