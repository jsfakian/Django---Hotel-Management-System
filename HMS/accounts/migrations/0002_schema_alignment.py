from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('properties', '0002_travelagency'),
        ('room', '0003_schema_alignment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('admin', 'System Administrator'), ('hotel_manager', 'Hotel Manager'), ('receptionist', 'Receptionist'), ('travel_agent', 'Travel Agent'), ('guest', 'Guest'), ('employee', 'Employee')], help_text='Role name matching Django groups', max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('permissions', models.JSONField(blank=True, default=dict, help_text='JSON object defining role permissions')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.DeleteModel(
            name='Task',
        ),
        migrations.DeleteModel(
            name='Employee',
        ),
        migrations.DeleteModel(
            name='Guest',
        ),
        migrations.CreateModel(
            name='Guest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('address', models.TextField(blank=True)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('postal_code', models.CharField(blank=True, max_length=20)),
                ('preferences', models.JSONField(blank=True, default=dict, help_text='Guest preferences for room type, floor, amenities, etc.')),
                ('number_of_bookings', models.IntegerField(default=0)),
                ('total_nights_stayed', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='guest_profile', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('salary', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('position', models.CharField(blank=True, max_length=100)),
                ('department', models.CharField(blank=True, max_length=100)),
                ('hire_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive'), ('on_leave', 'On Leave'), ('terminated', 'Terminated')], default='active', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('property', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='properties.property')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='employee_profile', to='auth.user')),
            ],
            options={
                'verbose_name_plural': 'Employees',
                'ordering': ['user__first_name'],
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('booking', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='room.booking')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='accounts.employee')),
                ('property', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='properties.property')),
            ],
            options={
                'ordering': ['-priority', 'start_time'],
            },
        ),
        migrations.AddIndex(
            model_name='guest',
            index=models.Index(fields=['email'], name='accounts_gu_email_15e636_idx'),
        ),
        migrations.AddIndex(
            model_name='guest',
            index=models.Index(fields=['created_at'], name='accounts_gu_created_284793_idx'),
        ),
        migrations.AddIndex(
            model_name='employee',
            index=models.Index(fields=['status', 'property'], name='accounts_em_status_1c318f_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['employee', 'status'], name='accounts_ta_employe_b7eed3_idx'),
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['start_time'], name='accounts_ta_start_t_1aa3c5_idx'),
        ),
    ]
