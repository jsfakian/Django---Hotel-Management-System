# Nephele — Architecture

This document describes the **current** runtime architecture as implemented in the repository (Django 4.2 API, React SPA, Celery, Postgres/Redis, monitoring). Historical design essays live in `DELIVERABLES-Task4-SystemArchitecture.md` and related task docs; when they conflict with this file or the code, **trust the code**.

## 1. System context

```
                   ┌─────────────────┐
   Guests / staff  │  React SPA      │  :3000 (Vite)
                   │  (JWT Bearer)   │
                   └────────┬────────┘
                            │ HTTP /api/v1
                            ▼
┌──────────────┐   ┌─────────────────┐   ┌──────────────┐
│ Django Admin │   │  Django + DRF   │──▶│ PostgreSQL   │
│ Templates    │──▶│  Gunicorn/run   │   │     15       │
│ /portal/*    │   │  :8000          │   └──────────────┘
└──────────────┘   └────────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         ┌────────┐   ┌──────────┐  ┌────────────┐
         │ Redis  │   │ Celery   │  │ Prometheus │
         │ cache  │◀──│ worker + │  │ Grafana    │
         │ broker │   │ beat     │  │ Alertmgr   │
         └────────┘   └────┬─────┘  └────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ML pricing   OTA sync     Email / GDPR
         MyData AADE  reports      notifications
```

**External systems**

| System | Direction | Purpose |
|--------|-----------|---------|
| MyData (AADE) | Outbound | Greek e-invoicing (`payments/mydata_service.py`) |
| Stripe | Outbound | Optional card payments |
| OTA APIs | Bidirectional (via channel adapters) | Booking.com, Airbnb, Expedia, etc. |
| SMTP | Outbound | Transactional email |
| Slack / PagerDuty | Outbound | Alertmanager notifications |

## 2. Runtime components

### 2.1 API / web (Django)

- Project package: `nephele/config/`
- Entry: `manage.py`, WSGI/ASGI under `nephele/config/`
- Settings: `nephele/config/settings.py` (prod via env); tests: `nephele/config/test_settings.py`
- URL roots (`nephele/config/urls.py`):
  - REST: `/api/v1/` → `nephele/config/api_urls.py`
  - Health: `/health/`, `/health/db/`, `/health/cache/`, `/healthz/`
  - Metrics: `/metrics/` (django-prometheus)
  - Admin: `/admin/`
  - Legacy HTML: `/`, `/login/`, `/portal/…`, `/properties/`, `/payments/`, `/notifications/`, `/contracts/`, `/analytics/` (web)

### 2.2 Frontend (React SPA)

- Location: `frontend/`
- Stack: React 18, Vite 5, MUI 5, Redux Toolkit + RTK Query, React Router 6, Axios
- API base: `VITE_API_BASE_URL` (dev default `http://localhost:8000/api/v1`)
- Auth: JWT in `localStorage`, refresh via `auth/refresh/`, role claim drives dashboard routing
- Role trees: `/admin/*`, `/manager/*`, `/receptionist/*`, `/staff/*`, `/guest/*`, `/analytics/*`

Django templates remain for landing/portal and some ops pages; the SPA is the primary product UI.

### 2.3 Async workers (Celery)

| Piece | Location |
|-------|----------|
| App | `nephele/config/celery.py` |
| Broker / results | Redis (`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`) |
| Beat schedule (code) | `CELERY_BEAT_SCHEDULE` in `settings.py` |
| Beat runtime | `django_celery_beat` DatabaseScheduler (compose) |
| Alternate schedule file | `nephele/config/celery_config.py` (not imported by settings) |

**Task modules**

| Module | Responsibility |
|--------|----------------|
| `bookings/tasks.py` | Model training hooks, auto-pricing, pricing reports, cleanup |
| `analytics/tasks.py` | ETL, scheduled reports, retention cleanup |
| `channels/tasks.py` | OTA availability / booking sync |
| `notifications/tasks.py` | Email and alert delivery |
| `accounts/tasks.py` | Async GDPR data export |

### 2.4 Data stores

| Store | Use |
|-------|-----|
| PostgreSQL 15 | System of record |
| Redis DB 0 | Celery broker |
| Redis DB 1 | Celery results |
| Redis DB 2 | Django cache (`CACHE_URL`) |
| File / media | Uploads, GDPR export artifacts under app `exports/` |

### 2.5 Observability

- App metrics: `django-prometheus` middleware → scrape `/metrics/`
- Stack (dev compose): Prometheus `:9090`, Grafana `:3001`, Alertmanager `:9093`, postgres/redis/node exporters
- Config: `monitoring/prometheus.yml`, `monitoring/alerts.yml`, `monitoring/alertmanager.yml`, Grafana provisioning under `monitoring/grafana-provisioning/`

## 3. Django domain apps

| App | Responsibility | Notable models / services |
|-----|----------------|---------------------------|
| `accounts` | Identity profiles, roles metadata, GDPR | `Guest`, `Employee`, `Role`; `services/gdpr_export.py` |
| `properties` | Hotels and travel agencies | `Property`, `TravelAgency` |
| `room` | Physical rooms and booking records | `Room`, `Booking`, services, refunds |
| `bookings` | Pricing / ML domain (separate from room booking CRUD) | `PricingHistory`, `price_predictor.py`, pricing APIs |
| `inventory` | Central availability & overbooking | `RoomAvailability`, sync logs |
| `payments` | Payments, invoices, tax | Stripe settings, `mydata_service.py` |
| `contracts` | Agency contracts & commissions | `Contract` |
| `channels` | OTA channel config & channel bookings | `Channel`, sync tasks |
| `notifications` | In-app / email / preferences | `Notification`, Celery send |
| `analytics` | BI, custom reports, forecasting | Dashboards, ETL tasks, web + API |
| `hotel` | Legacy ops (events, bills, storage, …) | Classic views; no dedicated `urls.py` include |

Cross-cutting API implementation also lives in `nephele/config/api_viewsets.py`, `auth_api.py`, and `dashboard_api.py`.

### Domain relationships (simplified)

```
Property ──┬── Room ──── Booking (room app)
           ├── RoomAvailability (inventory)
           ├── Contract ←→ TravelAgency
           ├── Channel mapping
           └── Analytics / PricingHistory

User ──┬── Guest profile
       ├── Employee profile
       └── Groups (admin|manager|receptionist|staff|guest)

Booking ── Payment ── Invoice ──(optional)── MyData submission
```

## 4. API design

- Versioned under `/api/v1/`
- Primary style: DRF `ModelViewSet` + `DefaultRouter`
- Auth: `JWTAuthentication` + `SessionAuthentication`
- Schema: drf-spectacular → `/api/v1/schema/`, Swagger UI → `/api/v1/docs/swagger/`
- Supplemental includes (not only router CRUD):
  - `bookings.urls` — dynamic price, recommendations, pricing predict/history/scenario
  - Channel ViewSet registered on `/api/v1/channels/` (no separate `channels.urls`)
  - `inventory.urls` — availability, overbook, sync log
  - `analytics.urls` — reporting & forecasting surface

JWT login (`NepheleTokenObtainPairView`) embeds `role`, `username`, and `email` claims. Role resolution: superuser → `admin`, else first Django Group name, else `guest`.

## 5. AuthZ model

1. **Groups** — primary runtime role for SPA and many checks  
2. **`accounts.permissions`** — `ROLE_PERMISSIONS` map + decorators for function views  
3. **DRF** — viewset-level `permission_classes` (typically `IsAuthenticated`; no global default in settings)  
4. **`accounts.Role`** — JSON permission metadata (complementary; not the sole enforcer)

`RoleBasedAccessMiddleware` exists in code but is **not** registered in `MIDDLEWARE`.

## 6. Key feature architectures

### 6.1 Dynamic pricing

```
PricingHistory / bookings data
        │
        ▼
price_predictor.py  ←── dynamic_pricing_model.pkl
        │
        ▼
REST /api/v1/bookings/pricing/*  +  Celery auto-price / retrain tasks
        │
        ▼
Frontend admin pricing pages
```

Related: `BI_ML_INTEGRATION_ARCHITECTURE.md` (deeper ML notes; verify against `bookings/` code).

### 6.2 Inventory / channels

Central `RoomAvailability` is the availability source of truth for overbooking controls. Channel sync Celery tasks push/pull OTA state; channel bookings can trigger notification tasks.

### 6.3 Payments & MyData

Payment and invoice models live in `payments`. MyData submission is encapsulated in `mydata_service.py` with settings-driven sandbox/auto-transmit flags. Legacy HTML MyData actions remain under `/payments/…`.

### 6.4 GDPR

API under `/api/v1/gdpr/*` orchestrates async export (Celery) and deletion requests. Guest SPA page: `frontend/src/pages/guest/GDPRPage.jsx`. Tests: `nephele/accounts/tests_gdpr.py` (`make test-gdpr`).

## 7. Deployment topologies

### 7.1 Local / development (`docker-compose.yml`)

Services: `postgres`, `redis`, `django`, `frontend`, `celery`, `celery-beat`, `prometheus`, `grafana`, `alertmanager`, exporters.

Typical ports: Django `8000`, SPA `3000`, Postgres host `5433`, Redis host `6380`, Grafana `3001`, Prometheus `9090`.

`make setup` starts the stack, migrates, and bootstraps metadata.

### 7.2 Production Compose (`docker-compose.prod.yml`)

Services: `postgres`, `redis`, `django` (`Dockerfile.prod`, `DEBUG=False`), `celery`, `celery-beat`, `nginx` (`80`/`443`). Uses `.env.prod`. Monitoring and Vite SPA are not part of this file (serve built frontend via nginx or a separate host).

### 7.3 Cloud / cluster

| Path | Role |
|------|------|
| `terraform/` | AWS IaC (compute, database, environments) |
| `k8s/` | Kubernetes manifests + `deploy.sh` |
| `deployment/` | nginx + `.env.prod.example` (runbooks in `docs/deployment/`) |
| `ml/` | pricing/forecast training (`algorithms/`) and experiment CSVs (`data/`) |
| `scripts/` | Backup, restore, health, certbot helpers |

## 8. Testing architecture

```
nephele/tests/          # primary pyramid (unit / integration / e2e / performance)
nephele/accounts/tests_gdpr.py
monitoring/test_monitoring.py
nephele/pytest.ini      # DJANGO_SETTINGS_MODULE=config.test_settings
```

- In-memory SQLite for tests; Celery eager in test settings as configured
- Factories via factory-boy
- Coverage target ~82%+ (`make test-cov`)

## 9. Security notes (architecture-level)

- Secrets via environment (never commit `.env` / `.env.prod`)
- JWT access ~1h, refresh ~30d with rotation; logout blacklists refresh tokens when blacklist app is enabled
- Prod compose enables secure cookie flags when `DEBUG=False`
- CORS via `django-cors-headers` for the SPA origin
- Prometheus scrapes metrics without business auth by default — restrict at network layer in production
- MyData and Stripe credentials are optional and sandbox-first for local work

## 10. Evolution notes

The codebase still contains **dual UI surfaces** (Django templates + React) and some **split booking ownership** (`room` models vs `bookings` pricing app). New features should:

1. Prefer REST under `/api/v1/` + SPA pages  
2. Keep availability mutations going through `inventory`  
3. Put async side effects in Celery task modules, not request threads  
4. Extend OpenAPI annotations (`@extend_schema`) for public endpoints  

For operational guides (deploy, backup, MyData, monitoring), see [docs/guides/](docs/guides/) and [docs/README.md](docs/README.md). Historical deliverables are under [docs/archive/](docs/archive/).
