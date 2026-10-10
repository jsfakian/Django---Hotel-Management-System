# Nephele — deploy, backup, and cron targets
# Usage:  make -f deploy.mk deploy
#         make deploy          (via include from Makefile)
#
# Overrides:
#   ENV_FILE=.env COMPOSE_FILE=docker-compose.yml make -f deploy.mk deploy
#   CRON_SCHEDULE="0 3 * * *" make backup-cron-install

COMPOSE       ?= docker compose
COMPOSE_FILE  ?= docker-compose.prod.yml
ENV_FILE      ?= .env.prod
PROJECT_NAME  ?= nephele
BACKUP_SCRIPT := scripts/backup-database.sh
DAILY_SCRIPT  := scripts/backup-daily.sh
CRON_SCRIPT   := scripts/install-backup-cron.sh

.PHONY: deploy deploy-check deploy-build deploy-up deploy-migrate deploy-static \
	deploy-health deploy-down deploy-logs deploy-ps \
	backup backup-daily backup-list db-restore \
	backup-cron-install backup-cron-remove backup-cron-status

# ── Deploy ──────────────────────────────────────────────────────────────────

deploy-check:
	@test -f "$(ENV_FILE)" || (echo "Missing $(ENV_FILE). Copy .env.prod.example and configure it."; exit 1)
	@command -v docker >/dev/null || (echo "docker is required"; exit 1)
	@$(COMPOSE) version >/dev/null 2>&1 || (echo "docker compose is required"; exit 1)

deploy-build: deploy-check
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) -p $(PROJECT_NAME) build

deploy-up: deploy-check
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) -p $(PROJECT_NAME) up -d
	@echo "Waiting for postgres…"
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) -p $(PROJECT_NAME) \
			exec -T postgres pg_isready -U $${POSTGRES_USER:-hms} >/dev/null 2>&1 && break; \
		sleep 3; \
	done

deploy-migrate: deploy-check
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) -p $(PROJECT_NAME) \
		exec -T django python manage.py migrate --noinput

deploy-static: deploy-check
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) -p $(PROJECT_NAME) \
		exec -T django python manage.py collectstatic --noinput

deploy-health: deploy-check
	@echo "Service status:"
	@$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) -p $(PROJECT_NAME) ps
	@echo ""
	@curl -sf http://localhost:$${DJANGO_HOST_PORT:-8000}/api/v1/docs/swagger/ >/dev/null \
		&& echo "API docs: OK" \
		|| echo "API docs: not reachable yet (check logs with make deploy-logs)"

deploy: deploy-build deploy-up deploy-migrate deploy-static deploy-health
	@echo ""
	@echo "Deploy complete."
	@echo "  API:      http://localhost:$${DJANGO_HOST_PORT:-8000}"
	@echo "  Swagger:  http://localhost:$${DJANGO_HOST_PORT:-8000}/api/v1/docs/swagger/"
	@echo "  Frontend: http://localhost:$${FRONTEND_HOST_PORT:-3000}"

deploy-down:
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) -p $(PROJECT_NAME) down

deploy-logs:
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) -p $(PROJECT_NAME) logs -f --tail=100

deploy-ps:
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) -p $(PROJECT_NAME) ps

# ── Backup ──────────────────────────────────────────────────────────────────

backup:
	@chmod +x $(BACKUP_SCRIPT) $(DAILY_SCRIPT)
	ENV_FILE=$(ENV_FILE) COMPOSE_FILE=$(COMPOSE_FILE) ./$(BACKUP_SCRIPT)

backup-daily:
	@chmod +x $(BACKUP_SCRIPT) $(DAILY_SCRIPT)
	ENV_FILE=$(ENV_FILE) COMPOSE_FILE=$(COMPOSE_FILE) ./$(DAILY_SCRIPT)

backup-list:
	@echo "=== Daily ===" && ls -lht backup/daily/nephele_full_*.sql* 2>/dev/null | head -10 || echo "(none)"
	@echo "=== Root   ===" && ls -lht backup/nephele_full_*.sql* 2>/dev/null | head -10 || echo "(none)"

db-restore:
	@test -n "$(FILE)" || (echo "Usage: make db-restore FILE=backup/daily/nephele_full_YYYYMMDD_HHMMSS.sql.gz"; exit 1)
	@chmod +x scripts/restore-database.sh
	ENV_FILE=$(ENV_FILE) COMPOSE_FILE=$(COMPOSE_FILE) ./scripts/restore-database.sh "$(FILE)"

# ── Cron (daily backup) ─────────────────────────────────────────────────────

backup-cron-install:
	@chmod +x $(CRON_SCRIPT) $(DAILY_SCRIPT) $(BACKUP_SCRIPT)
	ENV_FILE="$(abspath $(ENV_FILE))" COMPOSE_FILE="$(COMPOSE_FILE)" \
		CRON_SCHEDULE="$${CRON_SCHEDULE:-0 2 * * *}" \
		./$(CRON_SCRIPT) install

backup-cron-remove:
	@chmod +x $(CRON_SCRIPT)
	./$(CRON_SCRIPT) remove

backup-cron-status:
	@chmod +x $(CRON_SCRIPT)
	./$(CRON_SCRIPT) status
