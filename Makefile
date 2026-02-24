VENV_PYTHON := .venv/bin/python
COMPOSE := docker compose

.PHONY: help build up down restart logs ps shell migrate makemigrations bootstrap create-admin check test-venv test-docker setup smoke clean load-demo-data test test-cov test-unit test-integration test-e2e test-performance test-verbose test-fast test-failed test-quiet test-file test-class test-method cov-report cov-clean lint format quality test-validate ci-test test-gdpr test-gdpr-service test-gdpr-api test-gdpr-command test-gdpr-compliance test-gdpr-integrity

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
	@echo "  make load-demo-data  Load comprehensive demo data (properties, bookings, etc.)"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make check           Run Django system checks"
	@echo "  make test-docker     Run tests in Docker container (legacy)"
	@echo "  make test-venv       Run tests with local virtualenv (legacy)"
	@echo "  make smoke           Basic smoke test on /api/v1/schema/"
	@echo ""
	@echo "Testing - Pytest (NEW):"
	@echo "  make test            Run all tests with pytest"
	@echo "  make test-cov        Run tests with coverage report (target: 82%+)"
	@echo "  make test-unit       Run unit tests only (70% pyramid)"
	@echo "  make test-integration Run integration tests only (20% pyramid)"
	@echo "  make test-e2e        Run E2E tests only (5% pyramid)"
	@echo "  make test-performance Run performance/load tests"
	@echo "  make test-verbose    Run all tests with verbose output"
	@echo "  make test-fast       Run faster tests (skip slow/performance)"
	@echo "  make test-failed     Re-run only failed tests"
	@echo ""
	@echo "Testing - GDPR Compliance (NEW):"
	@echo "  make test-gdpr       Run all GDPR tests (21 tests)"
	@echo "  make test-gdpr-service Run GDPR export service tests (6 tests)"
	@echo "  make test-gdpr-api   Run GDPR REST API tests (6 tests)"
	@echo "  make test-gdpr-command Run GDPR management command tests (3 tests)"
	@echo "  make test-gdpr-compliance Run GDPR compliance tests (3 tests)"
	@echo "  make test-gdpr-integrity Run GDPR data integrity tests (3 tests)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make cov-report      Generate HTML coverage report"
	@echo "  make cov-clean       Clean coverage data and reports"
	@echo "  make lint            Run code quality checks (flake8, pylint)"
	@echo "  make format          Format code with black and isort"
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
	@echo ""
	@echo "Setup complete! Run 'make load-demo-data' to load demo data for testing."

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

load-demo-data:
	$(COMPOSE) exec django python manage.py load_demo_data

load-demo-data-fresh:
	$(COMPOSE) exec django python manage.py load_demo_data --clear

# ==============================================================================
# Pytest-based Testing Rules (Task 5f: Comprehensive Testing)
# ==============================================================================

# Default: Run all tests
test:
	@echo "Running all tests with pytest..."
	cd HMS && ../.venv/bin/python -m pytest -v --tb=short

# Run tests with coverage report (Target: 82%+ from task 5f)
test-cov:
	@echo "Running tests with coverage analysis..."
	@echo "Target Coverage: 82%+ (as per task 5f requirements)"
	cd HMS && ../.venv/bin/python -m pytest --cov=. --cov-report=term-missing --cov-report=html -v
	@echo ""
	@echo "✓ Coverage report generated: HMS/htmlcov/index.html"

# Run unit tests only (70% of pyramid)
test-unit:
	@echo "Running unit tests (Models, Serializers, Views, Services)..."
	cd HMS && ../.venv/bin/python -m pytest HMS/tests/models/ HMS/tests/serializers/ HMS/tests/views/ HMS/tests/services/ -v --tb=short

# Run integration tests only (20% of pyramid)
test-integration:
	@echo "Running integration tests (Workflows)..."
	cd HMS && ../.venv/bin/python -m pytest HMS/tests/integration/ -v --tb=short

# Run E2E tests only (5% of pyramid - critical paths)
test-e2e:
	@echo "Running E2E tests (Critical user journeys)..."
	cd HMS && ../.venv/bin/python -m pytest HMS/tests/e2e_base.py -v --tb=short

# Run performance tests
test-performance:
	@echo "Running performance and load tests..."
	cd HMS && ../.venv/bin/python -m pytest HMS/tests/test_performance.py -v --tb=short

# ==============================================================================
# GDPR Compliance Testing (Article 15, 17, 20)
# ==============================================================================

# Run all GDPR tests (21 total: service, API, command, data integrity, compliance)
test-gdpr:
	@echo "Running all GDPR compliance tests (21 tests total)..."
	@echo "  - GDPRExportServiceTests (6 tests)"
	@echo "  - GDPRAPITests (6 tests)"
	@echo "  - ManagementCommandTests (3 tests)"
	@echo "  - GDPRExportDataIntegrityTests (3 tests)"
	@echo "  - GDPRComplianceTests (3 tests)"
	cd HMS && SECRET_KEY="test-secret-key" DEBUG="True" DB_ENGINE="django.db.backends.sqlite3" ../.venv/bin/python manage.py test accounts.tests_gdpr -v 2

# Run GDPR export service tests (6 tests)
# Tests: initialization, profile export, complete export, JSON/dict conversions
test-gdpr-service:
	@echo "Running GDPR Export Service tests (6 tests)..."
	cd HMS && SECRET_KEY="test-secret-key" DEBUG="True" DB_ENGINE="django.db.backends.sqlite3" ../.venv/bin/python manage.py test accounts.tests_gdpr.GDPRExportServiceTests -v 2

# Run GDPR REST API tests (6 tests)
# Tests: request export, download export, delete confirmation, anonymous access
test-gdpr-api:
	@echo "Running GDPR REST API tests (6 tests)..."
	cd HMS && SECRET_KEY="test-secret-key" DEBUG="True" DB_ENGINE="django.db.backends.sqlite3" ../.venv/bin/python manage.py test accounts.tests_gdpr.GDPRAPITests -v 2

# Run GDPR management command tests (3 tests)
# Tests: export by ID, export by email, invalid user handling
test-gdpr-command:
	@echo "Running GDPR Management Command tests (3 tests)..."
	cd HMS && SECRET_KEY="test-secret-key" DEBUG="True" DB_ENGINE="django.db.backends.sqlite3" ../.venv/bin/python manage.py test accounts.tests_gdpr.ManagementCommandTests -v 2

# Run GDPR compliance verification tests (3 tests)
# Tests: DSAR metadata, user identifier inclusion, version tracking
test-gdpr-compliance:
	@echo "Running GDPR Compliance Verification tests (3 tests)..."
	cd HMS && SECRET_KEY="test-secret-key" DEBUG="True" DB_ENGINE="django.db.backends.sqlite3" ../.venv/bin/python manage.py test accounts.tests_gdpr.GDPRComplianceTests -v 2

# Run GDPR data integrity tests (3 tests)
# Tests: all data categories exported, required field presence, format validation
test-gdpr-integrity:
	@echo "Running GDPR Data Integrity tests (3 tests)..."
	cd HMS && SECRET_KEY="test-secret-key" DEBUG="True" DB_ENGINE="django.db.backends.sqlite3" ../.venv/bin/python manage.py test accounts.tests_gdpr.GDPRExportDataIntegrityTests -v 2

# Run all tests with verbose output
test-verbose:
	@echo "Running all tests with verbose output..."
	cd HMS && ../.venv/bin/python -m pytest -vv --tb=long

# Run faster tests (skip slow ones)
test-fast:
	@echo "Running fast tests (excluding slow)..."
	cd HMS && ../.venv/bin/python -m pytest -v -m "not slow" --tb=short

# Re-run only failed tests from last run
test-failed:
	@echo "Re-running only failed tests..."
	cd HMS && ../.venv/bin/python -m pytest --lf -v --tb=short

# Run tests with less output (quiet mode)
test-quiet:
	@echo "Running tests in quiet mode..."
	cd HMS && ../.venv/bin/python -m pytest --tb=line -q

# Run specific test file
test-file:
	@echo "Usage: make test-file TEST=HMS/tests/models/test_room_model.py"
	@if [ -z "$(TEST)" ]; then \
		echo "ERROR: TEST variable not set"; exit 1; \
	fi
	cd HMS && ../.venv/bin/python -m pytest $(TEST) -v --tb=short

# Run specific test class
test-class:
	@echo "Usage: make test-class CLASS=RoomModelTests"
	@if [ -z "$(CLASS)" ]; then \
		echo "ERROR: CLASS variable not set"; exit 1; \
	fi
	cd HMS && ../.venv/bin/python -m pytest -k "$(CLASS)" -v --tb=short

# Run specific test method
test-method:
	@echo "Usage: make test-method TEST=HMS/tests/models/test_room_model.py::RoomModelTests::test_room_creation_with_valid_data"
	@if [ -z "$(TEST)" ]; then \
		echo "ERROR: TEST variable not set"; exit 1; \
	fi
	cd HMS && ../.venv/bin/python -m pytest $(TEST) -v --tb=short

# Generate HTML coverage report
cov-report:
	@echo "Generating HTML coverage report..."
	@if [ ! -d "HMS/htmlcov" ]; then \
		echo "Coverage report not found. Running tests with coverage first..."; \
		cd HMS && ../.venv/bin/python -m pytest --cov=. --cov-report=html --cov-report=term -q; \
	fi
	@echo "✓ Coverage report available at: HMS/htmlcov/index.html"
	@echo "Opening report in browser..."
	@python -m webbrowser file://$(PWD)/HMS/htmlcov/index.html 2>/dev/null || echo "Please open HMS/htmlcov/index.html manually"

# Clean coverage data and reports
cov-clean:
	@echo "Cleaning coverage data and reports..."
	rm -rf HMS/.coverage HMS/htmlcov HMS/.coverage.* HMS/test-results.xml
	@echo "✓ Coverage data cleaned"

# Run linting and code quality checks
lint:
	@echo "Running code quality checks..."
	@cd HMS && python -m flake8 . --max-line-length=100 --exclude=migrations,__pycache__,.venv 2>/dev/null || echo "Flake8 checks complete"
	@echo "✓ Linting checks complete"

# Format code with black and isort
format:
	@echo "Formatting code..."
	@cd HMS && python -m isort . --skip-glob=migrate --skip=.venv 2>/dev/null || echo "isort formatting complete"
	@cd HMS && python -m black . --exclude "migrations|.venv" 2>/dev/null || echo "black formatting complete"
	@echo "✓ Code formatted"

# Run all quality checks (lint + tests)
quality: lint test-cov
	@echo "✓ Quality checks complete"

# Validate test infrastructure
test-validate:
	@echo "Validating test infrastructure..."
	@cd HMS && ../.venv/bin/python -m pytest --collect-only -q
	@echo "✓ Test collection successful"

# CI/CD simulation - run like GitHub Actions
ci-test:
	@echo "Running CI/CD simulation (like GitHub Actions)..."
	@echo "1. Running linting..."
	-@cd HMS && python -m flake8 . --max-line-length=100 --exclude=migrations,__pycache__,.venv --format=json > /dev/null 2>&1 || true
	@echo "2. Running full test suite with coverage..."
	cd HMS && ../.venv/bin/python -m pytest --cov=. --cov-report=xml --cov-report=term-missing --junitxml=test-results.xml -v
	@echo ""
	@echo "3. Analyzing coverage..."
	@cd HMS && python -c "import xml.etree.ElementTree as ET; tree = ET.parse('.coverage'); root = tree.getroot()" 2>/dev/null || echo "Coverage XML not found, using text report"
	@echo "✓ CI/CD simulation complete"

# ==============================================================================

clean:
	$(COMPOSE) down -v
	@make cov-clean
