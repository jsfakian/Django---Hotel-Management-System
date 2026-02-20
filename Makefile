VENV_PYTHON := .venv/bin/python
COMPOSE := docker compose

.PHONY: build up down restart logs ps shell migrate bootstrap create-admin check test-venv test-docker setup smoke clean

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

setup: up
	$(COMPOSE) exec django python manage.py migrate --noinput
	$(COMPOSE) exec django python manage.py bootstrap_metadata

down:
	$(COMPOSE) down

restart: down up

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec django bash

migrate:
	$(COMPOSE) exec django python manage.py migrate --noinput

bootstrap:
	$(COMPOSE) exec django python manage.py bootstrap_metadata

create-admin:
	$(COMPOSE) exec django bash -c "python manage.py shell <<'PY'\nimport os\nfrom django.contrib.auth import get_user_model\nUser=get_user_model()\nusername=os.getenv('DJANGO_SUPERUSER_USERNAME')\nemail=os.getenv('DJANGO_SUPERUSER_EMAIL')\npassword=os.getenv('DJANGO_SUPERUSER_PASSWORD')\nif not (username and email and password):\n    raise SystemExit('DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD must be set')\nuser, created = User.objects.get_or_create(username=username, defaults={'email': email, 'is_staff': True, 'is_superuser': True, 'is_active': True})\nuser.email = email\nuser.is_staff = True\nuser.is_superuser = True\nuser.is_active = True\nuser.set_password(password)\nuser.save()\nprint(f'Admin ready: {username} (created={created})')\nPY"

check:
	$(COMPOSE) exec django python manage.py check

test-venv:
	cd HMS && ../$(VENV_PYTHON) manage.py test

test-docker:
	$(COMPOSE) exec django python manage.py test --noinput

smoke:
	curl -fsS http://localhost:8000/api/v1/schema/ > /dev/null
	@echo "Smoke check passed: /api/v1/schema/ reachable"

clean:
	$(COMPOSE) down -v
