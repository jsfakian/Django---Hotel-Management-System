# GitHub Copilot Instructions — NEPHELE Hotel Management System

## Project Identity
This is **NEPHELE HMS** — a Django 4.2 multi-property hotel management system with a REST API, dynamic ML-based pricing, Greek MyData (AADE) tax integration, GDPR compliance, and full observability via Prometheus/Grafana.

## Tech Stack
- **Python 3.10**, **Django 4.2**, **Django REST Framework 3.14**
- **Database**: PostgreSQL 15 (psycopg2-binary), SQLite for local dev
- **Cache / Queue broker**: Redis 7
- **Task queue**: Celery 5.3 + Celery Beat with `django_celery_beat`
- **Auth**: JWT — `djangorestframework-simplejwt`
- **API docs**: drf-spectacular (OpenAPI 3)
- **ML / Pricing**: scikit-learn, XGBoost, pandas, numpy
- **Monitoring**: `django-prometheus`, Prometheus, Grafana, Alertmanager
- **Testing**: pytest, pytest-django, factory-boy, faker
- **Code quality**: black (88), isort, flake8, pylint, mypy

## Project Structure
```
HMS/                  ← Django project root (run manage.py from here)
├── HMS/              ← settings, urls, celery, wsgi, asgi
├── accounts/         ← users, employees, guests, permissions, GDPR
├── analytics/        ← BI dashboards, forecasting, reports
├── bookings/         ← reservations, dynamic pricing, ML predictor
├── channels/         ← OTA integrations (Booking.com, Expedia, Airbnb)
├── contracts/        ← travel agency contracts
├── hotel/            ← hotel entity, amenities
├── inventory/        ← centralised room availability
├── notifications/    ← async email/push, pricing alerts
├── payments/         ← payments, invoices, MyData/AADE
├── properties/       ← multi-property management
├── room/             ← room types, PricingHistory
└── tests/            ← cross-app integration & performance tests
```

## Coding Conventions

### Models
- Inherit from `django.db.models.Model`; always define `__str__`
- Use `db_index=True` on frequently filtered fields
- Prefer `ForeignKey` with explicit `on_delete` and `related_name`
- Soft-delete pattern: `is_active = models.BooleanField(default=True)`
- Decimal fields for money: `DecimalField(max_digits=10, decimal_places=2)`

### Serializers
- Use `ModelSerializer` as the default base class
- Validate business rules in `validate_<field>` or `validate` methods
- Use `read_only_fields` for computed or system-managed fields
- Nested serializers: use `SerializerMethodField` for computed representations

### ViewSets
- Use `ModelViewSet` for full CRUD; use `ReadOnlyModelViewSet` for read-only resources
- Always define `permission_classes` and `authentication_classes` explicitly
- Filter with `django-filter` (`filterset_class` attribute)
- Pagination: use the global `DEFAULT_PAGINATION_CLASS` from settings (PageNumber)
- Override `get_queryset()` to apply role-based data scoping

### URL Patterns
- All REST endpoints live under `/api/v1/` via `HMS/HMS/api_urls.py`
- Register ViewSets on the `DefaultRouter` in `api_urls.py`
- Legacy/web views are in `HMS/HMS/urls.py`

### Celery Tasks
- Define tasks in `<app>/tasks.py` with `@shared_task`
- Use `bind=True` with `self.retry()` for retryable tasks
- Always set `max_retries` and `default_retry_delay`
- Beat schedule configuration in `HMS/HMS/celery_config.py`

### Permissions
Role constants are defined in `HMS/accounts/permissions.py`.
User groups: `admin`, `manager`, `receptionist`, `staff`, `guest`.
Use `IsAuthenticated` + group-level permission classes. Never bypass permission checks.

### Tests
- Use `pytest` + `pytest-django`; test files are `tests.py` or `tests/` inside each app
- Use `factory-boy` factories for model creation — avoid raw `Model.objects.create()` in tests
- Mark tests: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`
- Integration tests use a real database (PostgreSQL in CI) — **do not mock the DB**
- Coverage target: **82%+**

### Environment / Configuration
- Settings loaded from env vars via `os.environ.get()`
- Never hard-code credentials; reference `.env` for local dev values
- Test settings override: `HMS/HMS/test_settings.py`

## Key Design Patterns

### Dynamic Pricing Flow
`BookingViewSet` → `bookings/pricing_service.py` → `bookings/price_predictor.py` (loads `dynamic_pricing_model.pkl`) → returns calculated price using occupancy, season, demand score.

### Payment / Invoice Flow
`PaymentViewSet` → `payments/views.py` → `payments/mydata_service.py` (submits to AADE MyData API for Greek e-invoicing).

### Availability / Channel Sync
`inventory/views.py` (RoomAvailabilityViewSet) ↔ `channels/tasks.py` (async Celery task syncs availability to OTA channels).

### Notifications
Triggered via Celery tasks in `notifications/tasks.py`. Templates in `templates/notifications/`.

## What Copilot Should Avoid
- Do not suggest `Model.objects.all()` without `.select_related()` / `.prefetch_related()` where FK traversal occurs
- Do not generate `except Exception: pass` — always log or re-raise
- Do not suggest storing secrets in source code or settings files
- Do not generate test code that mocks `django.db` — use real DB fixtures/factories instead
- Do not generate `ALLOWED_HOSTS = ['*']` in production context
- Do not add `DEBUG = True` in `docker-compose.prod.yml` or production configs

## File Naming
- Models: singular noun (`Booking`, not `Bookings`)
- Serializers: `<Model>Serializer`
- ViewSets: `<Model>ViewSet`
- Tasks: verbs (`send_notification_email`, `sync_channel_availability`)
- Tests: `test_<what_is_being_tested>.py`

## Running Things
```bash
# Full dev stack
make up

# Tests
make test          # all
make test-unit     # unit only
make test-cov      # with coverage

# Migrations
make makemigrations
make migrate

# Shell
make shell

# Lint / format
make lint
make format
```
