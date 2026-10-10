# Contributing to NEPHELE HMS

## Development workflow

1. Copy env and start the stack:

   ```bash
   cp .env.example .env
   make setup
   ```

2. SPA (included in compose on `:3000`) talks to `http://localhost:8000/api/v1`.

3. Prefer `make` targets over ad-hoc `docker compose` / `manage.py` calls so paths and env stay consistent. Run `make help` for the full list.

### Useful commands

```bash
make shell              # bash in django container
make makemigrations
make migrate
make load-demo-data
make logs
make format             # black + isort
make lint               # flake8 + pylint
make test
make test-cov
make test-unit
make test-integration
make test-e2e
make test-gdpr
make ci-test
```

Local Django without Docker (optional):

```bash
cd HMS
python manage.py <command>
```

Use the project virtualenv (`.venv`) when running pytest on the host; the Makefile expects `.venv/bin/python`.

## Code conventions

| Area | Convention |
|------|------------|
| Formatter | `black` (line length 88) |
| Imports | `isort` (django profile) |
| Linters | `flake8`, `pylint` |
| Types | `mypy` for new code where practical |
| API | DRF `ModelSerializer` / `ModelViewSet`; document with drf-spectacular |
| Models | Docstrings only when the name is not enough |
| Tests | pytest + pytest-django; factory-boy factories; mark with `@pytest.mark.unit` etc. |

Django project root for imports and `manage.py` is **`HMS/`**.

## App boundaries

- Put availability changes in `inventory`, not ad-hoc room flags.
- Booking **pricing / ML** lives in `bookings/`; core booking records are in `room/`.
- Side effects (email, OTA sync, GDPR export, retrain) → Celery tasks in the owning app’s `tasks.py`.
- Prefer new UI in `frontend/`; avoid growing legacy template portals unless required for admin/ops.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the component map.

## Pull requests

- Keep PRs focused; match existing style in the touched app.
- Include or update tests for behavior changes (unit for logic, integration for DB/API).
- Do not commit `.env`, credentials, or large binary artifacts unrelated to the change.
- Update [README.md](README.md) / [ARCHITECTURE.md](ARCHITECTURE.md) only when the public interface or topology changes.

## Documentation

- Day-to-day: [README.md](README.md), [ARCHITECTURE.md](ARCHITECTURE.md), [docs/guides/](docs/guides/).
- Historical deliverables live under [docs/archive/](docs/archive/) — audit only, not runbooks.
