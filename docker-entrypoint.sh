#!/bin/bash
set -e

echo "========================================="
echo "HMS Django Entrypoint Script"
echo "========================================="

# Wait for PostgreSQL
echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
python << 'EOF'
import os
import time
import psycopg2
from psycopg2 import OperationalError

db_host = os.getenv("DB_HOST", "postgres")
db_port = int(os.getenv("DB_PORT", "5432"))
db_name = os.getenv("DB_NAME", "hms")
db_user = os.getenv("DB_USER", "hms")
db_password = os.getenv("DB_PASSWORD", "hms_password")

for attempt in range(60):
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        conn.close()
        print("✓ PostgreSQL is ready!")
        break
    except OperationalError as e:
        if attempt < 59:
            print(f"  Attempt {attempt + 1}/60: PostgreSQL not ready, retrying...")
            time.sleep(1)
        else:
            print(f"✗ Failed to connect to PostgreSQL: {e}")
            exit(1)
EOF

# Run migrations
echo ""
echo "Running Django migrations..."
python manage.py migrate --noinput
echo "✓ Migrations completed"

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "✓ Static files collected"

# Create superuser and demo user if they don't exist
echo ""
echo "Setting up users..."
python manage.py shell << 'EOF'
import os
from django.contrib.auth.models import User

# Create superuser
admin_username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
admin_email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
admin_password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')

if not User.objects.filter(username=admin_username).exists():
    User.objects.create_superuser(
        username=admin_username,
        email=admin_email,
        password=admin_password
    )
    print(f"✓ Superuser '{admin_username}' created")
else:
    print(f"✓ Superuser '{admin_username}' already exists")

# Create demo test user
demo_username = os.getenv('DJANGO_TEST_USER_USERNAME', 'demo')
demo_email = os.getenv('DJANGO_TEST_USER_EMAIL', 'demo@example.com')
demo_password = os.getenv('DJANGO_TEST_USER_PASSWORD', 'demo123')

if not User.objects.filter(username=demo_username).exists():
    User.objects.create_user(
        username=demo_username,
        email=demo_email,
        password=demo_password
    )
    print(f"✓ Demo user '{demo_username}' created")
else:
    print(f"✓ Demo user '{demo_username}' already exists")
EOF

# Run the main command
echo ""
echo "========================================="
echo "Starting Django development server..."
echo "========================================="
echo ""

if [ "$#" -eq 0 ]; then
    # Default: run Django development server
    python manage.py runserver 0.0.0.0:8000
else
    # Run provided command
    exec "$@"
fi
