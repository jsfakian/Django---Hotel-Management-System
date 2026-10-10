from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def rebuild_room_schema(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()
    is_sqlite = connection.vendor == 'sqlite'

    if is_sqlite:
        cursor.execute('PRAGMA foreign_keys = OFF;')

    drop_suffix = '' if is_sqlite else ' CASCADE'

    cursor.execute(f'DROP TABLE IF EXISTS room_roomservice{drop_suffix};')
    cursor.execute(f'DROP TABLE IF EXISTS room_roomservices{drop_suffix};')
    cursor.execute(f'DROP TABLE IF EXISTS room_refund{drop_suffix};')
    cursor.execute(f'DROP TABLE IF EXISTS room_dependees{drop_suffix};')
    cursor.execute(f'DROP TABLE IF EXISTS room_booking{drop_suffix};')
    cursor.execute(f'DROP TABLE IF EXISTS room_room{drop_suffix};')

    pk_sql = 'INTEGER PRIMARY KEY AUTOINCREMENT' if is_sqlite else 'BIGSERIAL PRIMARY KEY'
    datetime_sql = 'DATETIME' if is_sqlite else 'TIMESTAMP'
    json_default_sql = "TEXT NOT NULL DEFAULT '[]'" if is_sqlite else "JSONB NOT NULL DEFAULT '[]'::jsonb"

    cursor.execute(
        f'''
        CREATE TABLE room_room (
            id {pk_sql},
            room_number VARCHAR(50) NOT NULL UNIQUE,
            floor INTEGER NOT NULL,
            room_type VARCHAR(50) NOT NULL,
            capacity INTEGER NOT NULL,
            number_of_beds INTEGER NOT NULL,
            base_price DECIMAL(10,2) NOT NULL,
            current_price DECIMAL(10,2) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'available',
            status_start_date DATE NULL,
            status_end_date DATE NULL,
            amenities {json_default_sql},
            property_id BIGINT NULL REFERENCES properties_property(id) ON DELETE CASCADE,
            created_at {datetime_sql} NOT NULL,
            updated_at {datetime_sql} NOT NULL
        );
        '''
    )

    cursor.execute(
        f'''
        CREATE TABLE room_booking (
            id {pk_sql},
            check_in_date DATE NOT NULL,
            check_out_date DATE NOT NULL,
            date_of_reservation DATE NOT NULL,
            number_of_guests INTEGER NOT NULL DEFAULT 1,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            base_price DECIMAL(10,2) NOT NULL,
            actual_price DECIMAL(10,2) NULL,
            notes TEXT NOT NULL DEFAULT '',
            special_requests TEXT NOT NULL DEFAULT '',
            room_id INTEGER NOT NULL REFERENCES room_room(id) ON DELETE CASCADE,
            guest_id BIGINT NULL REFERENCES accounts_guest(id) ON DELETE CASCADE,
            travel_agency_id BIGINT NULL REFERENCES properties_travelagency(id) ON DELETE SET NULL,
            created_at {datetime_sql} NOT NULL,
            updated_at {datetime_sql} NOT NULL
        );
        '''
    )

    cursor.execute(
        f'''
        CREATE TABLE room_dependees (
            id {pk_sql},
            name VARCHAR(100) NOT NULL,
            relationship VARCHAR(50) NOT NULL DEFAULT '',
            created_at {datetime_sql} NOT NULL,
            booking_id INTEGER NOT NULL REFERENCES room_booking(id) ON DELETE CASCADE
        );
        '''
    )

    cursor.execute(
        f'''
        CREATE TABLE room_refund (
            id {pk_sql},
            reason TEXT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            refund_amount DECIMAL(10,2) NULL,
            created_at {datetime_sql} NOT NULL,
            updated_at {datetime_sql} NOT NULL,
            guest_id BIGINT NOT NULL REFERENCES accounts_guest(id) ON DELETE CASCADE,
            booking_id INTEGER NOT NULL REFERENCES room_booking(id) ON DELETE CASCADE
        );
        '''
    )

    cursor.execute(
        f'''
        CREATE TABLE room_roomservice (
            id {pk_sql},
            service_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            description TEXT NOT NULL DEFAULT '',
            price DECIMAL(10,2) NOT NULL DEFAULT 0,
            created_date DATE NOT NULL,
            created_at {datetime_sql} NOT NULL,
            completed_at {datetime_sql} NULL,
            booking_id INTEGER NULL REFERENCES room_booking(id) ON DELETE CASCADE,
            room_id INTEGER NOT NULL REFERENCES room_room(id) ON DELETE CASCADE
        );
        '''
    )

    cursor.execute('CREATE INDEX room_room_property_status_idx ON room_room(property_id, status);')
    cursor.execute('CREATE INDEX room_room_room_number_idx ON room_room(room_number);')
    cursor.execute('CREATE INDEX room_booking_room_dates_idx ON room_booking(room_id, check_in_date, check_out_date);')
    cursor.execute('CREATE INDEX room_booking_guest_status_idx ON room_booking(guest_id, status);')
    cursor.execute('CREATE INDEX room_booking_status_idx ON room_booking(status);')
    cursor.execute('CREATE INDEX room_roomservice_room_status_idx ON room_roomservice(room_id, status);')
    cursor.execute('CREATE INDEX room_roomservice_created_idx ON room_roomservice(created_at);')

    if is_sqlite:
        cursor.execute('PRAGMA foreign_keys = ON;')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('properties', '0002_travelagency'),
        ('room', '0002_room_property'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(rebuild_room_schema, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.DeleteModel(name='RoomServices'),
                migrations.DeleteModel(name='Refund'),
                migrations.DeleteModel(name='Dependees'),
                migrations.DeleteModel(name='Booking'),
                migrations.DeleteModel(name='Room'),
                migrations.CreateModel(
                    name='Room',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('room_number', models.CharField(max_length=50, unique=True)),
                        ('floor', models.IntegerField()),
                        ('room_type', models.CharField(choices=[('single', 'Single Room'), ('double', 'Double Room'), ('suite', 'Suite'), ('deluxe', 'Deluxe'), ('luxury', 'Luxury'), ('economic', 'Economic')], max_length=50)),
                        ('capacity', models.PositiveIntegerField()),
                        ('number_of_beds', models.PositiveIntegerField()),
                        ('base_price', models.DecimalField(decimal_places=2, max_digits=10)),
                        ('current_price', models.DecimalField(decimal_places=2, max_digits=10)),
                        ('status', models.CharField(choices=[('available', 'Available'), ('occupied', 'Occupied'), ('maintenance', 'Maintenance'), ('cleaning', 'Cleaning'), ('reserved', 'Reserved')], default='available', max_length=20)),
                        ('status_start_date', models.DateField(blank=True, null=True)),
                        ('status_end_date', models.DateField(blank=True, null=True)),
                        ('amenities', models.JSONField(blank=True, default=list, help_text='JSON array of room amenities')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rooms', to='properties.property')),
                    ],
                    options={
                        'ordering': ['property', 'room_number'],
                        'indexes': [models.Index(fields=['property', 'status'], name='room_room_property_status_idx'), models.Index(fields=['room_number'], name='room_room_room_number_idx')],
                    },
                ),
                migrations.CreateModel(
                    name='Booking',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('check_in_date', models.DateField()),
                        ('check_out_date', models.DateField()),
                        ('date_of_reservation', models.DateField(default=django.utils.timezone.now)),
                        ('number_of_guests', models.PositiveIntegerField(default=1)),
                        ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('checked_in', 'Checked In'), ('checked_out', 'Checked Out'), ('cancelled', 'Cancelled'), ('no_show', 'No-Show')], default='pending', max_length=20)),
                        ('base_price', models.DecimalField(decimal_places=2, max_digits=10)),
                        ('actual_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                        ('notes', models.TextField(blank=True)),
                        ('special_requests', models.TextField(blank=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('guest', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='accounts.guest')),
                        ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='room.room')),
                        ('travel_agency', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bookings', to='properties.travelagency')),
                    ],
                    options={
                        'ordering': ['-check_in_date'],
                        'indexes': [models.Index(fields=['room', 'check_in_date', 'check_out_date'], name='room_booking_room_dates_idx'), models.Index(fields=['guest', 'status'], name='room_booking_guest_status_idx'), models.Index(fields=['status'], name='room_booking_status_idx')],
                    },
                ),
                migrations.CreateModel(
                    name='Dependees',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=100)),
                        ('relationship', models.CharField(blank=True, max_length=50)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guests_list', to='room.booking')),
                    ],
                    options={
                        'verbose_name_plural': 'Dependees',
                    },
                ),
                migrations.CreateModel(
                    name='Refund',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('reason', models.TextField()),
                        ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('processed', 'Processed')], default='pending', max_length=20)),
                        ('refund_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refunds', to='room.booking')),
                        ('guest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refunds', to='accounts.guest')),
                    ],
                ),
                migrations.CreateModel(
                    name='RoomService',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('service_type', models.CharField(choices=[('food', 'Food Service'), ('cleaning', 'Cleaning Service'), ('technical', 'Technical Service'), ('maintenance', 'Maintenance'), ('concierge', 'Concierge'), ('laundry', 'Laundry'), ('other', 'Other')], max_length=50)),
                        ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                        ('description', models.TextField(blank=True)),
                        ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                        ('created_date', models.DateField(default=django.utils.timezone.now)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('completed_at', models.DateTimeField(blank=True, null=True)),
                        ('booking', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='room_services', to='room.booking')),
                        ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='services', to='room.room')),
                    ],
                    options={
                        'ordering': ['-created_at'],
                        'indexes': [models.Index(fields=['room', 'status'], name='room_roomservice_room_status_idx'), models.Index(fields=['created_at'], name='room_roomservice_created_idx')],
                    },
                ),
            ],
        ),
    ]
