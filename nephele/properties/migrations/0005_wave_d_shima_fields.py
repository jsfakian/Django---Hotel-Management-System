from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("properties", "0004_webhotelier_parity_p0_p2"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="mhte_number",
            field=models.CharField(
                blank=True,
                help_text="ΜΗΤΕ / ΣΗΜΑ registry number",
                max_length=64,
            ),
        ),
        migrations.AddField(
            model_name="property",
            name="tax_id",
            field=models.CharField(
                blank=True,
                help_text="Hotel AFM for MyData / police sheet",
                max_length=20,
            ),
        ),
    ]
