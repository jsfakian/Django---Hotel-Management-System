Create and apply Django database migrations. Usage: /migrate [action]

Actions:
- (none) → run `make migrate` to apply all pending migrations
- `make` → run `make makemigrations` to generate new migration files from model changes
- `both` → run `make makemigrations` then `make migrate`
- `check` → run `docker compose exec django python manage.py migrate --check` to report pending migrations without applying

After running, report which migrations were applied (or created). If there are conflicts or errors, show the full Django error output and suggest resolution steps.

Important: never edit migration files manually. If a migration conflict occurs, use `python manage.py migrate --merge`.
