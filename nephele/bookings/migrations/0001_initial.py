from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('room', '0003_schema_alignment'),
    ]

    operations = [
        migrations.CreateModel(
            name='PricingHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('weekday', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], null=True)),
                ('base_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('dynamic_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('competitor_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('occupancy_rate', models.DecimalField(blank=True, decimal_places=2, help_text='Occupancy rate (0-100%)', max_digits=5, null=True)),
                ('demand_score', models.DecimalField(blank=True, decimal_places=2, help_text='Demand score (0-100)', max_digits=5, null=True)),
                ('bookings_count', models.IntegerField(default=0)),
                ('cancellation_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('season', models.CharField(choices=[('low', 'Low Season'), ('medium', 'Medium Season'), ('high', 'High Season'), ('peak', 'Peak Season')], default='medium', max_length=20)),
                ('external_events', models.CharField(blank=True, help_text='Description of external events affecting demand', max_length=255)),
                ('predicted_by_model', models.BooleanField(default=False)),
                ('model_version', models.CharField(blank=True, max_length=50)),
                ('confidence_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pricing_history', to='room.room')),
            ],
            options={
                'verbose_name_plural': 'Pricing Histories',
                'ordering': ['-date'],
                'unique_together': {('room', 'date')},
            },
        ),
        migrations.CreateModel(
            name='DemandForecast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forecast_date', models.DateField()),
                ('forecast_for_date', models.DateField()),
                ('predicted_occupancy', models.DecimalField(decimal_places=2, max_digits=5)),
                ('predicted_demand_score', models.DecimalField(decimal_places=2, max_digits=5)),
                ('recommended_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('confidence', models.DecimalField(decimal_places=2, max_digits=5)),
                ('model_name', models.CharField(max_length=100)),
                ('model_version', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='demand_forecasts', to='room.room')),
            ],
            options={
                'ordering': ['-forecast_for_date'],
                'unique_together': {('room', 'forecast_date', 'forecast_for_date')},
            },
        ),
        migrations.CreateModel(
            name='CompetitorPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('competitor_name', models.CharField(max_length=255)),
                ('date', models.DateField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('source_url', models.URLField(blank=True)),
                ('last_checked', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competitor_prices', to='room.room')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.AddIndex(
            model_name='pricinghistory',
            index=models.Index(fields=['room', '-date'], name='bookings_pr_room_id_a7772b_idx'),
        ),
        migrations.AddIndex(
            model_name='pricinghistory',
            index=models.Index(fields=['date'], name='bookings_pr_date_6ad651_idx'),
        ),
        migrations.AddIndex(
            model_name='pricinghistory',
            index=models.Index(fields=['room', 'season'], name='bookings_pr_room_id_e4f4b8_idx'),
        ),
        migrations.AddIndex(
            model_name='demandforecast',
            index=models.Index(fields=['room', 'forecast_for_date'], name='bookings_de_room_id_74f8f4_idx'),
        ),
        migrations.AddIndex(
            model_name='competitorprice',
            index=models.Index(fields=['room', '-date'], name='bookings_co_room_id_27128a_idx'),
        ),
    ]
