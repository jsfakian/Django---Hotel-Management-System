#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for PostgreSQL at ${DB_HOST:-postgres}:${DB_PORT:-5432}..."
python - <<'PY'
import os
import time
import psycopg2

host = os.getenv("DB_HOST", "postgres")
port = int(os.getenv("DB_PORT", "5432"))
name = os.getenv("DB_NAME", "hms")
user = os.getenv("DB_USER", "hms")
password = os.getenv("DB_PASSWORD", "hms")

for attempt in range(1, 61):
    try:
        conn = psycopg2.connect(host=host, port=port, dbname=name, user=user, password=password)
        conn.close()
        print("PostgreSQL is ready")
        break
    except Exception as exc:
        if attempt == 60:
            raise SystemExit(f"PostgreSQL did not become ready: {exc}")
        time.sleep(1)
PY

echo "Running migrations..."
python manage.py migrate --noinput

echo "Bootstrapping metadata (django_content_type/auth_permission)..."
python manage.py bootstrap_metadata

echo "Ensuring admin user exists..."
python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv('DJANGO_SUPERUSER_USERNAME')
email = os.getenv('DJANGO_SUPERUSER_EMAIL')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

if username and email and password:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        },
    )
    if created:
        user.set_password(password)
        user.save(update_fields=['password'])
        print(f'Created admin user: {username}')
    else:
        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True
        user.set_password(password)
        changed = True
        if changed:
            user.save()
        print(f'Updated admin user: {username}')
else:
    print('Admin environment variables not fully set; skipping admin bootstrap')

test_username = os.getenv('DJANGO_TEST_USER_USERNAME')
test_email = os.getenv('DJANGO_TEST_USER_EMAIL')
test_password = os.getenv('DJANGO_TEST_USER_PASSWORD')

if test_username and test_email and test_password:
    test_user, created = User.objects.get_or_create(
        username=test_username,
        defaults={
            'email': test_email,
            'is_staff': False,
            'is_superuser': False,
            'is_active': True,
        },
    )

    changed = False
    if test_user.email != test_email:
        test_user.email = test_email
        changed = True
    if not test_user.is_active:
        test_user.is_active = True
        changed = True
    if test_user.is_staff:
        test_user.is_staff = False
        changed = True
    if test_user.is_superuser:
        test_user.is_superuser = False
        changed = True

    test_user.set_password(test_password)
    changed = True

    if changed:
        test_user.save()

    print(f'Test user ready: {test_username} (created={created})')
else:
    print('Test user environment variables not fully set; skipping test user bootstrap')
PY

echo "Setup complete"
