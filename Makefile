VENV_PYTHON := .venv/bin/python
COMPOSE := docker compose

.PHONY: help build up down restart logs ps shell migrate makemigrations bootstrap create-admin check test-venv test-docker setup smoke clean

help:
	@echo "HMS (Hotel Management System) - Available Commands"
	@echo "=================================================="
	@echo ""
	@echo "Setup & Deployment:"
	@echo "  make setup           Start containers and run migrations + bootstrap"
	@echo "  make build           Build Docker images"
	@echo "  make up              Start containers in detached mode"
	@echo "  make down            Stop and remove containers"
	@echo "  make restart         Restart containers (down then up)"
	@echo "  make clean           Remove all containers and volumes"
	@echo ""
	@echo "Development:"
	@echo "  make shell           Open bash shell in django container"
	@echo "  make logs            View container logs (last 200 lines, follow)"
	@echo "  make ps              Show running containers"
	@echo ""
	@echo "Database & Initialization:"
	@echo "  make makemigrations  Create new Django migrations (from model changes)"
	@echo "  make migrate         Run Django migrations"
	@echo "  make bootstrap       Bootstrap metadata tables"
	@echo "  make create-admin    Create superuser admin account"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make check           Run Django system checks"
	@echo "  make test-docker     Run tests in Docker container"
	@echo "  make test-venv       Run tests with local virtualenv"
	@echo "  make smoke           Basic smoke test on /api/v1/schema/"
	@echo ""
	@echo "Usage:"
	@echo "  make help            Display this help message"
	@echo "  make <target>        Run the specified target"
	@echo ""

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

makemigrations:
	$(COMPOSE) exec django python manage.py makemigrations

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
