# NEPHELE Hotel Management System

Django 4.2 REST API + React SPA for multi-property hotel operations. Supports Admin, Manager, Receptionist, Staff, and Guest roles with JWT auth, dynamic pricing, OTA channels, Greek MyData (AADE) invoicing, GDPR export/deletion, and a Prometheus/Grafana monitoring stack.

> **Note:** The previous root README described a Django 3.1 server-rendered setup. That guide is obsolete. Use this file and [ARCHITECTURE.md](ARCHITECTURE.md).

## Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 4.2.7, Django REST Framework 3.14, SimpleJWT |
| API docs | drf-spectacular (OpenAPI / Swagger) |
| Database | PostgreSQL 15 |
| Cache / broker | Redis 7 |
| Async | Celery 5.3 + django-celery-beat |
| Frontend | React 18, Vite 5, MUI 5, Redux Toolkit, Axios |
| ML pricing | scikit-learn, XGBoost (`HMS/dynamic_pricing_model.pkl`) |
| Monitoring | django-prometheus, Prometheus, Grafana, Alertmanager |
| Deploy | Docker Compose, optional Terraform (AWS) + Kubernetes manifests |

## Quick start (Docker)

Prerequisites: Docker Compose v2, Make, and (for local pytest) Python 3.11+ with a `.venv`.

```bash
cp .env.example .env
make setup          # build/start stack, migrate, bootstrap metadata
make create-admin   # if needed — uses DJANGO_SUPERUSER_* from .env
make load-demo-data # optional demo properties, rooms, bookings
```

| Service | URL |
|---------|-----|
| React SPA | http://localhost:3000 |
| Django / API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/api/v1/docs/swagger/ |
| OpenAPI schema | http://localhost:8000/api/v1/schema/ |
| Django Admin | http://localhost:8000/admin/ |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |

Default host ports for data services: PostgreSQL `5433`, Redis `6380`.

Default admin credentials come from `.env` (`DJANGO_SUPERUSER_USERNAME` / `PASSWORD`, typically `admin` / `admin123` for local dev only).

```bash
make down    # stop
make logs    # follow logs
make help    # full command list
```

## Repository layout

```
.
├── HMS/                    # Django project (manage.py lives here)
│   ├── HMS/                # settings, urls, celery, API viewsets
│   ├── accounts/           # users, employees, guests, GDPR
│   ├── analytics/          # BI, reports, forecasting
│   ├── bookings/           # dynamic pricing, ML predictor, Celery pricing tasks
│   ├── channels/           # OTA integration (Booking.com, Airbnb, Expedia, …)
│   ├── contracts/          # travel agency contracts
│   ├── hotel/              # legacy hotel ops models/views
│   ├── inventory/          # centralized room availability
│   ├── notifications/      # email / in-app notifications
│   ├── payments/           # payments, invoices, MyData/AADE
│   ├── properties/         # multi-property + travel agencies
│   ├── room/               # rooms, bookings domain models
│   ├── templates/          # server-rendered pages (legacy / portal)
│   └── tests/              # pytest suite
├── frontend/               # React SPA (Vite)
├── monitoring/             # Prometheus, Alertmanager, Grafana provisioning
├── terraform/              # AWS infrastructure
├── k8s/                    # Kubernetes manifests
├── deployment/             # nginx, prod deployment guides
├── scripts/                # backup / health / ops scripts
├── manuals/                # end-user role manuals
├── task3-algorithms/       # ML training / pricing models (Celery hooks)
├── task3-data/             # small CSVs for pricing experiments
├── docker-compose.yml      # development stack
├── docker-compose.prod.yml # production stack (nginx + Django + Celery)
├── Makefile                # primary developer interface
├── ARCHITECTURE.md         # system design
├── CONTRIBUTING.md         # development & testing conventions
└── docs/
    ├── README.md           # documentation index
    ├── guides/             # ops & domain guides
    └── archive/            # historical deliverables (not runbooks)
```

## API overview

Base URL: `/api/v1/`

| Area | Endpoints |
|------|-----------|
| Auth | `POST auth/login/`, `auth/refresh/`, `auth/register/`, `auth/logout/`, `auth/forgot-password/` |
| Core CRUD | `users/`, `guests/`, `employees/`, `properties/`, `travel-agencies/`, `rooms/`, `bookings/`, `contracts/`, `payments/`, `invoices/`, `refund-requests/`, `notifications/`, `channels/` |
| Inventory | `inventory/` |
| Analytics | `analytics/` |
| Pricing | under `bookings/` (predict, history, scenario, models, …) |
| GDPR | `gdpr/request-export/`, `gdpr/download-export/`, `gdpr/export-status/<task_id>/`, `gdpr/request-deletion/` |
| Dashboard | `dashboard/stats/`, `trends/` |
| Ops | `/health/`, `/health/db/`, `/health/cache/`, `/metrics/` |

Auth for the SPA is JWT (Bearer). Session auth remains available for Django templates and admin.

## Roles

Django Groups drive runtime roles: `admin`, `manager`, `receptionist`, `staff`, `guest`. The SPA routes each role to its dashboard (`frontend/src/App.jsx`). Public self-registration is for guests; employees are created by admins/managers.

End-user manuals: [manuals/](manuals/README.md).

## Common Make targets

```bash
# Development
make up / make down / make restart / make shell / make logs

# Database
make makemigrations / make migrate / make bootstrap / make load-demo-data

# Quality
make test / make test-cov / make test-unit / make test-integration / make test-e2e
make test-gdpr / make test-monitoring / make lint / make format / make ci-test

# Production (docker-compose.prod.yml + .env.prod)
make prod-up / make prod-migrate / make prod-health / make prod-backup
```

## Environment

Copy `.env.example` → `.env` for development. Important variables:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Django core |
| `POSTGRES_*`, `DB_*`, `POSTGRES_HOST_PORT` | Database |
| `REDIS_*`, `CACHE_URL`, `CELERY_*` | Cache & Celery |
| `DJANGO_SUPERUSER_*` | Bootstrap admin |
| `MYDATA_*`, `HOTEL_TAX_ID` | Greek AADE MyData |
| `STRIPE_*` | Optional card payments |
| `SLACK_WEBHOOK_URL` | Alertmanager (compose) |

Production templates: `.env.prod.example`, `deployment/.env.prod.example`. Frontend API base: `frontend/.env.development` (`VITE_API_BASE_URL=http://localhost:8000/api/v1`).

## Testing

```bash
make test          # full pytest suite
make test-cov      # coverage (target 82%+)
make test-gdpr     # GDPR compliance
make smoke         # hits OpenAPI schema
```

Config: `HMS/pytest.ini`, settings `HMS/HMS/test_settings.py`, fixtures `HMS/conftest.py`. Markers: `unit`, `integration`, `e2e`, `performance`, `slow`, `functional`.

## Documentation map

| Doc | Contents |
|-----|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, data flow, apps, deployments |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Local workflow, style, PR expectations |
| [docs/README.md](docs/README.md) | Index of guides + archive |
| [docs/guides/](docs/guides/) | MyData, monitoring, Docker, GDPR, … |
| [CLAUDE.md](CLAUDE.md) | Agent/project conventions for AI-assisted work |
| [manuals/](manuals/README.md) | Role-based user manuals |
| [deployment/](deployment/) | Production deploy & backup procedures |
| [docs/archive/](docs/archive/) | Historical deliverables / phase notes (audit only) |

## License / origin

Evolved from an open-source Django hotel management starter into the NEPHELE HMS product stack (API, SPA, ML pricing, compliance, and ops tooling). Older research artifacts live under `docs/archive/research/`.
