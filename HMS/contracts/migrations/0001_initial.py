from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('properties', '0002_travelagency'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contract_type', models.CharField(choices=[('guarantee', 'Guarantee Contract'), ('allotment', 'Allotment Contract'), ('commission', 'Commission Agreement'), ('exclusive', 'Exclusive Agreement')], default='allotment', max_length=50)),
                ('allocation_percentage', models.DecimalField(blank=True, decimal_places=2, help_text='Percentage of rooms allocated (for Allotment contracts)', max_digits=5, null=True)),
                ('allocated_rooms', models.PositiveIntegerField(blank=True, help_text='Fixed number of rooms (for Guarantee contracts)', null=True)),
                ('commission_percentage', models.DecimalField(decimal_places=2, help_text='Commission percentage for the travel agency', max_digits=5)),
                ('payment_terms', models.TextField(help_text='Describe payment frequency, deposit requirements, etc.')),
                ('cancellation_policy', models.TextField(help_text='Describe cancellation terms and penalties.')),
                ('special_terms', models.TextField(blank=True, help_text='Additional special terms or conditions')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('contract_text', models.TextField()),
                ('document_file', models.FileField(blank=True, null=True, upload_to='contracts/%Y/%m/')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending', 'Pending Review'), ('signed_property', 'Signed by Property'), ('signed_agency', 'Signed by Agency'), ('active', 'Active'), ('expired', 'Expired'), ('terminated', 'Terminated'), ('rejected', 'Rejected')], default='draft', max_length=30)),
                ('property_manager_signed_at', models.DateTimeField(blank=True, null=True)),
                ('property_manager_signature', models.CharField(blank=True, max_length=255)),
                ('travel_agency_signed_at', models.DateTimeField(blank=True, null=True)),
                ('travel_agency_signature', models.CharField(blank=True, max_length=255)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to='properties.property')),
                ('property_manager', models.ForeignKey(limit_choices_to={'groups__name': 'hotel_manager'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contracts_created', to=settings.AUTH_USER_MODEL)),
                ('travel_agency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to='properties.travelagency')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('property', 'travel_agency')},
            },
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['status'], name='contracts_c_status_1d6701_idx'),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['property', 'status'], name='contracts_c_propert_5d6174_idx'),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['start_date', 'end_date'], name='contracts_c_start_d_156a87_idx'),
        ),
    ]
