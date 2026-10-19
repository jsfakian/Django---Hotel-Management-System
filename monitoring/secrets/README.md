# Alertmanager secrets

Alertmanager does not expand `${ENV}` variables in `monitoring/alertmanager.yml`, so its secrets are
read from files in this directory, mounted read-only at `/etc/alertmanager/secrets`:

| File | Used by |
| --- | --- |
| `slack_webhook_url` | `global.slack_api_url_file` (every `slack_configs` receiver) |
| `pagerduty_service_key` | the `critical` receiver's `pagerduty_configs` |

Each file holds the bare value on one line. Everything here except this README and `.gitignore` is
gitignored.

Without a file the config still loads and alerts still show in the Alertmanager UI (`:9093`); only
that notification fails, and Alertmanager logs it. After adding or changing a file:

```bash
chmod 600 monitoring/secrets/*
docker compose -p hms-prod -f docker-compose.yml -f docker-compose.override.yml restart alertmanager
```
