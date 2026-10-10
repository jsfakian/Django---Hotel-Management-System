# Monitoring Quick Reference

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Prometheus | http://localhost:9090 | Metrics database & queryingPrometheus |
| Alertmanager | http://localhost:9093 | Alert management & notifications |
| Grafana | http://localhost:3000 | Dashboards & visualization |

---

## Enable Services

```bash
# Start all services including monitoring
docker-compose up -d

# Or start only monitoring services
docker-compose up -d prometheus alertmanager grafana postgres-exporter redis-exporter node-exporter

# View running services
docker-compose ps
```

---

## Common PromQL Queries

### Application Metrics
```promql
# HTTP request rate
rate(django_http_requests_total[5m])

# Error rate (5xx responses)
rate(django_http_requests_total{status=~"5.."}[5m])

# Response time p95
histogram_quantile(0.95, sum(rate(django_http_requests_latency_seconds_bucket[5m])) by (le))

# Database queries per second
rate(django_db_execute_total[5m])

# Cache hit ratio
rate(django_cache_get_hits_total[5m]) / (rate(django_cache_get_hits_total[5m]) + rate(django_cache_get_misses_total[5m]))
```

### Infrastructure Metrics
```promql
# CPU usage percentage
(100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))

# Memory usage percentage
((node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes) * 100

# Disk usage percentage
(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100

# Service uptime status
up
```

### Database Metrics
```promql
# Transaction rate
rate(pg_stat_database_xact_commit[5m])

# Active connections
pg_stat_activity_count

# Cache hit ratio
rate(pg_stat_database_heap_blks_hit[5m]) / (rate(pg_stat_database_heap_blks_hit[5m]) + rate(pg_stat_database_heap_blks_read[5m]))

# Rows modified
rate(pg_stat_user_tables_n_tup_ins[5m]) + rate(pg_stat_user_tables_n_tup_upd[5m]) + rate(pg_stat_user_tables_n_tup_del[5m])
```

### Redis Metrics
```promql
# Memory usage
redis_memory_used_bytes / redis_memory_max_bytes * 100

# Connected clients
redis_connected_clients

# Evictions
rate(redis_evicted_keys_total[5m])

# Hit ratio
rate(redis_hits[5m]) / (rate(redis_hits[5m]) + rate(redis_misses[5m]))
```

### Celery Metrics
```promql
# Task completion rate
rate(celery_task_total[5m])

# Task success rate
rate(celery_task_succeeded_total[5m]) / rate(celery_task_total[5m])

# Queue length
celery_queue_length

# Active tasks
celery_active_tasks
```

---

## Check Service Health

```bash
# Prometheus
curl http://localhost:9090/-/healthy

# Alertmanager
curl http://localhost:9093/-/healthy

# Django metrics endpoint
curl http://localhost:8000/metrics/

# All targets status
curl http://localhost:9090/api/v1/targets | jq .
```

---

## View Logs

```bash
# Prometheus logs
docker-compose logs -f prometheus

# Alertmanager logs
docker-compose logs -f alertmanager

# Grafana logs
docker-compose logs -f grafana

# Exporter logs
docker-compose logs -f postgres-exporter
docker-compose logs -f redis-exporter
docker-compose logs -f node-exporter
```

---

## Environment Variables (Add to .env)

```bash
# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password
GRAFANA_URL=http://localhost:3000

# Alerting (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
PAGERDUTY_SERVICE_KEY=your_pagerduty_key

# Monitoring
ENVIRONMENT=development
```

---

## Configure Slack Alerts

1. Create Slack Webhook:
   - Go to https://api.slack.com/apps
   - Create new app → "From scratch"
   - Add "Incoming Webhooks" feature
   - Create new webhook URL

2. Add to `.env`:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

3. Restart services:
   ```bash
   docker-compose restart alertmanager
   ```

---

## Common Troubleshooting

### Prometheus not collecting metrics
```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Verify service is exposing metrics
curl http://localhost:8000/metrics/
curl http://localhost:9187/metrics
curl http://localhost:9121/metrics
```

### Alerts not firing
```bash
# Check loaded rules
curl http://localhost:9090/api/v1/rules

# Check alertmanager status
curl http://localhost:9093/api/v1/status
```

### Grafana dashboard empty
1. Verify Prometheus datasource:
   - Settings → Data Sources → Prometheus → Test
2. Check metrics exist:
   - Prometheus → Graph → Type metric name
3. Refresh dashboard (Ctrl+R)

### High memory usage
```bash
# Reduce retention in docker-compose.yml:
# '--storage.tsdb.retention.time=7d'  # reduced from 30d

docker-compose up -d prometheus
```

---

## Alert Severity Levels

- **Critical**: Immediate action required → Slack #alerts-critical + PagerDuty
- **Warning**: Investigation needed → Slack #alerts-warning
- **Info**: For awareness → Slack #alerts-info

---

## Maintenance

### Monthly Tasks
- Review and test alert thresholds
- Check alert response times
- Test Slack/PagerDuty integration
- Review metric cardinality

### Backup Prometheus Data
```bash
docker-compose exec prometheus \
  tar czf /tmp/backup.tar.gz /prometheus

docker cp hms-prometheus:/tmp/backup.tar.gz ./backups/
```

### Update Components
```bash
docker-compose pull
docker-compose up -d
```

---

## Contact & Resources

- Prometheus Docs: https://prometheus.io/docs/
- Grafana Docs: https://grafana.com/docs/
- PromQL Guide: https://prometheus.io/docs/prometheus/latest/querying/
- Alert Rules: https://prometheus.io/docs/practices/alerting/
