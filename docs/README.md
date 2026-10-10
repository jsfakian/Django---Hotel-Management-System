# Documentation

| Document | Audience |
|----------|----------|
| [../README.md](../README.md) | Setup, ports, API overview |
| [../ARCHITECTURE.md](../ARCHITECTURE.md) | System design |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Development workflow |
| [../CLAUDE.md](../CLAUDE.md) | AI-assisted conventions |
| [manuals/README.md](manuals/README.md) | End-user role manuals |
| [guides/](guides/) | Operational & domain guides |
| [deployment/](deployment/) | Deploy / backup runbooks |
| [archive/](archive/) | Historical deliverables (not runbooks) |
| [../ml/README.md](../ml/README.md) | ML training package layout |

## Guides (`docs/guides/`)

| Guide | Topic |
|-------|--------|
| [MYDATA_INTEGRATION_GUIDE.md](guides/MYDATA_INTEGRATION_GUIDE.md) | Greek AADE MyData |
| [MYDATA_API_REFERENCE.md](guides/MYDATA_API_REFERENCE.md) | MyData API reference |
| [CHANNEL_INTEGRATION_GUIDE.md](guides/CHANNEL_INTEGRATION_GUIDE.md) | OTA channels |
| [GDPR_DATA_EXPORT_GUIDE.md](guides/GDPR_DATA_EXPORT_GUIDE.md) | GDPR export / deletion |
| [MONITORING_GUIDE.md](guides/MONITORING_GUIDE.md) | Prometheus / Grafana |
| [MONITORING_QUICK_START.md](guides/MONITORING_QUICK_START.md) | Monitoring quick start |
| [CELERY_REDIS_SETUP.md](guides/CELERY_REDIS_SETUP.md) | Celery + Redis |
| [DOCKER_DEPLOYMENT_GUIDE.md](guides/DOCKER_DEPLOYMENT_GUIDE.md) | Docker deployment |
| [TERRAFORM_GUIDE.md](guides/TERRAFORM_GUIDE.md) | AWS Terraform |
| [BACKUP_QUICK_REF.md](guides/BACKUP_QUICK_REF.md) | Backup quick reference |
| [SECURITY_GUIDE.md](guides/SECURITY_GUIDE.md) | Security practices |
| [DISASTER_RECOVERY_GUIDE.md](guides/DISASTER_RECOVERY_GUIDE.md) | DR overview |
| [ANALYTICS_API_REFERENCE.md](guides/ANALYTICS_API_REFERENCE.md) | Analytics API |
| [FORECASTING_IMPLEMENTATION_GUIDE.md](guides/FORECASTING_IMPLEMENTATION_GUIDE.md) | Forecasting |
| [BI_ML_INTEGRATION_ARCHITECTURE.md](guides/BI_ML_INTEGRATION_ARCHITECTURE.md) | BI + ML pricing notes |
| [DEMO_DATA_SETUP.md](guides/DEMO_DATA_SETUP.md) | Demo data |
| [API_QUICK_REFERENCE.md](guides/API_QUICK_REFERENCE.md) | API cheat sheet (prefer live Swagger) |

Also under `guides/`: logging, performance, load balancing, auto-scaling, troubleshooting.

Live OpenAPI: http://localhost:8000/api/v1/docs/swagger/

Production configs (nginx, env template): [../deployment/](../deployment/).  
Deploy runbooks: [deployment/](deployment/).

## Archive (`docs/archive/`)

Historical grant deliverables, phase/gap summaries, research PDFs, old planning trees, and session notes. **Do not use as day-to-day runbooks** — verify against code, `Makefile`, and compose files.

| Folder | Contents |
|--------|----------|
| `deliverables/` | `DELIVERABLES-Task*.md` |
| `phase-gap/` | GAP/PHASE/infrastructure program docs |
| `session-notes/` | Completion summaries, quick refs, implementation logs |
| `research/` | PDFs, DOCX, design SQL, old swagger dump, `Documents/` |
| `planning/` | Former `tasks/` tree |
| `screenshots/` | Legacy UI screenshots |
| `legacy-scripts/` | One-off verify/test scripts from repo root |
| `misc/` | Extra task3 narrative docs |
