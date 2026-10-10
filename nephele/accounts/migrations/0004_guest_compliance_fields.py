# nephele/accounts/migrations/0004_guest_compliance_fields.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_travelagentprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="guest",
            name="birth_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="guest",
            name="document_number",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="guest",
            name="document_type",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="guest",
            name="nationality",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
