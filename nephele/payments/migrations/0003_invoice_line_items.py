# nephele/payments/migrations/0003_invoice_line_items.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_add_mydata_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="line_items",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Structured invoice lines (room, VAT, climate fee, extras)",
            ),
        ),
    ]
