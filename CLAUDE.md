# NEPHELE Hotel Management System — Claude Code Configuration

## Project Overview
**Nephele** is a Django 5.2 LTS REST API + web application for hotel management.
It supports five user roles: Admin, Manager, Receptionist, Staff, Guest.

- **Backend**: Django 5.2, Django REST Framework 3.16, PostgreSQL 15, Redis 7
- **Async tasks**: Celery 5.3 + Celery Beat (scheduled tasks via `django_celery_beat`)
- **Auth**: JWT via `djangorestframework-simplejwt`
- **API docs**: drf-spectacular (OpenAPI at `/api/v1/schema/`, Swagger UI at `/api/v1/docs/swagger/`)
- **Monitoring**: Prometheus + Grafana + Alertmanager (via `django-prometheus`)
- **ML/Pricing**: scikit-learn, XGBoost — model stored at `nephele/dynamic_pricing_model.pkl`
- **Greek tax integration**: MyData API (AADE) in `nephele/payments/mydata_service.py`
- **GDPR**: data export/deletion endpoints in `nephele/accounts/views.py`
- **Deployment**: Docker Compose (`docker-compose.yml`), production via `docker-compose.prod.yml`
- **IaC**: Terraform in `terraform/`

## Repository Layout
```
.
├── nephele/                    # Django project root (manage.py lives here)
│   ├── config/                 # settings, urls, celery, API viewsets
│   ├── accounts/ … room/   # domain apps (incl. hotel legacy)
│   ├── templates/          # Django HTML templates
│   └── tests/              # Cross-app pytest suite
├── frontend/               # React SPA (Vite + MUI)
├── ml/                     # ML training (algorithms/) + experiment CSVs (data/)
├── docs/                   # guides/, manuals/, deployment/, archive/
├── deployment/             # nginx.conf + .env.prod.example only
├── scripts/                # backup / health / validate_production / DB helpers
├── monitoring/             # Prometheus, Alertmanager, Grafana
├── terraform/              # AWS infrastructure
├── k8s/                    # Kubernetes manifests
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
└── requirements.txt
```

## Essential Commands
All primary workflows go through `make`. The Django root is `nephele/`.

```bash
# Start full dev stack (Django + Postgres + Redis + Celery + Monitoring)
make up

# Stop stack
make down

# Run all tests (pytest inside the django container)
make test

# Run with coverage (target: 82%+)
make test-cov

# Run only unit / integration / e2e tests
make test-unit
make test-integration
make test-e2e

# GDPR compliance tests
make test-gdpr

# Monitoring tests
make test-monitoring

# Create/apply Django migrations
make makemigrations
make migrate

# Open Django shell inside container
make shell

# Load demo data
make load-demo-data

# Code formatting & linting
make format    # black + isort
make lint      # flake8 + pylint

# Full CI check
make ci-test

# Production deploy (docker-compose.prod.yml + .env.prod)
make deploy

# Database backup + daily cron (see deploy.mk)
make backup
make backup-daily
make backup-cron-install
```

Running Django commands directly (outside Docker):
```bash
cd nephele
python manage.py <command>
```

## Django Apps — Quick Reference
| App | Responsibility |
|---|---|
| `accounts` | User model, Employee, Guest profiles, permissions, GDPR export/deletion |
| `analytics` | Occupancy reports, revenue analytics, BI dashboards, ML forecasting |
| `bookings` | Dynamic pricing engine, ML price predictor, PricingHistory |
| `channels` | OTA platform integration (Booking.com, Expedia, Airbnb) |
| `contracts` | Travel agency contracts and commission management |
| `hotel` | Legacy ops entities (events, bills, storage, announcements) |
| `inventory` | Centralised availability (RoomAvailability model, overbooking logic) |
| `notifications` | Async email/push notifications, pricing alerts via Celery |
| `payments` | Payment processing, invoices, MyData/AADE submission |
| `properties` | Multi-property management (a company can own multiple hotels) |
| `room` | Physical rooms and booking records |

## API Structure
Base URL: `/api/v1/`

| Endpoint | ViewSet |
|---|---|
| `auth/login/` | JWT token obtain |
| `auth/refresh/` | JWT token refresh |
| `users/` | UserViewSet |
| `guests/` | GuestViewSet |
| `employees/` | EmployeeViewSet |
| `properties/` | PropertyViewSet |
| `rooms/` | RoomViewSet |
| `bookings/` | BookingViewSet |
| `contracts/` | ContractViewSet |
| `payments/` | PaymentViewSet |
| `invoices/` | InvoiceViewSet |
| `channels/` | ChannelViewSet |
| `analytics/` | Analytics endpoints |

Full Swagger UI: `http://localhost:8000/api/v1/docs/swagger/`

Canonical docs: `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `docs/guides/`, `docs/README.md`. Historical paperwork: `docs/archive/`.
## Testing Conventions
- **Framework**: pytest + pytest-django
- **Config**: `nephele/pytest.ini`, `nephele/conftest.py`
- **Test settings**: `nephele/config/test_settings.py`
- **Coverage target**: 82%+
- **Test pyramid**: ~70% unit, ~20% integration, ~5% E2E, ~5% performance
- Use `factory-boy` for model factories (not fixtures where possible)
- Integration tests hit a real DB — do not mock the database

Marking tests:
```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.performance
@pytest.mark.slow
```

## Code Style
- **Formatter**: `black` (line length 88)
- **Imports**: `isort` (django profile)
- **Linter**: `flake8` + `pylint`
- **Type hints**: `mypy` for new code
- Models use docstrings only when the purpose isn't obvious from the name
- Serializers and ViewSets follow DRF conventions; prefer `ModelSerializer`

## Environment Variables (`.env`)
Key variables (see `.env` for full list):

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` / `False` |
| `POSTGRES_DB/USER/PASSWORD` | Database credentials |
| `REDIS_PORT` | Redis host port (default 6380) |
| `CELERY_TASK_ALWAYS_EAGER` | Set `True` in tests to run tasks synchronously |
| `DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD` | Auto-created admin on bootstrap |
| `MYDATA_USERNAME/SUBSCRIPTION_KEY` | Greek AADE MyData API credentials |
| `SLACK_WEBHOOK_URL` | Alertmanager Slack notifications |

## Infrastructure Ports (dev)
| Service | Port |
|---|---|
| React SPA | 3000 |
| Django | 8000 |
| PostgreSQL | 5433 |
| Redis | 6380 |
| Prometheus | 9090 |
| Grafana | 3001 |
| Alertmanager | 9093 |
| Celery Flower | 5555 (if enabled) |

## Celery Tasks
Tasks are defined in `<app>/tasks.py`. Active beat schedule is `CELERY_BEAT_SCHEDULE` in `nephele/config/settings.py` (compose also uses `django_celery_beat` DatabaseScheduler). `nephele/config/celery_config.py` is an alternate schedule file not wired into settings.
Key task modules: `bookings/tasks.py`, `analytics/tasks.py`, `notifications/tasks.py`, `channels/tasks.py`, `accounts/tasks.py`.

## Dynamic Pricing
The ML pricing engine lives in `nephele/bookings/`:
- `price_predictor.py` — loads `dynamic_pricing_model.pkl`, wraps scikit-learn/XGBoost model
- Pricing REST under `/api/v1/bookings/` (predict, history, scenario, models, …)
- `PricingHistory` model in `nephele/bookings/models.py` stores historical data for training

## MyData (AADE) Integration
Greek tax authority electronic invoicing. See `nephele/payments/mydata_service.py`.
API reference: `MYDATA_API_REFERENCE.md`.
Credentials via `MYDATA_USERNAME` and `MYDATA_SUBSCRIPTION_KEY` env vars.

## GDPR
Data export and deletion endpoints under `/api/v1/gdpr/`. Implementation in `nephele/accounts/views.py` and `nephele/accounts/tests_gdpr.py`. Run `make test-gdpr` to verify compliance.
