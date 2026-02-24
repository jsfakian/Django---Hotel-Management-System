# Monitoring Stack - Administrator Configuration Guide

**Date**: February 24, 2026  
**Version**: 1.0

---

## Table of Contents

1. [Prometheus Configuration](#prometheus-configuration)
2. [Alertmanager Configuration](#alertmanager-configuration)
3. [Grafana Administration](#grafana-administration)
4. [Exporter Configuration](#exporter-configuration)
5. [Advanced Topics](#advanced-topics)
6. [Troubleshooting](#troubleshooting)

---

## Prometheus Configuration

### Configuration File Location
```
monitoring/prometheus.yml
```

### Global Settings

```yaml
global:
  scrape_interval: 15s          # Default scrape interval
  evaluation_interval: 15s      # How often to evaluate rules
  external_labels:              # Labels added to all metrics
    monitor: 'hms-monitoring'
    environment: 'development'
```

**Tuning Guidelines**:
- **Scrape Interval**: 15s (default) → 5s (high priority), 1m (low priority)
- **Smaller intervals** = more storage, more CPU, fresher data
- **Larger intervals** = less storage, less CPU, delayed alerts
- **Recommended**: 15s for critical services, 1m for non-critical

### Adding Scrape Targets

```yaml
scrape_configs:
  - job_name: 'my-service'
    scrape_interval: 10s        # Override global interval
    scrape_timeout: 5s          # Max time to wait for response
    static_configs:
      - targets: ['service:8000']
        labels:                 # Add custom labels
          service: 'my-service'
          instance: 'prod-1'
    metrics_path: '/metrics/'   # Non-default path
    scheme: 'https'             # Use HTTPS
    basic_auth:                 # Basic authentication
      username: 'prometheus'
      password: 'secret'
```

### External Labels

Labels added to **all time series** from Prometheus:

```yaml
global:
  external_labels:
    monitor: 'hms-monitoring'
    environment: 'production'
    region: 'us-east-1'
    team: 'platform'
```

These help filter and aggregate metrics across multiple Prometheus servers.

### Alert Rules Configuration

```yaml
rule_files:
  - 'alerts.yml'
  - 'custom-alerts.yml'         # Add more rule files

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
    - static_configs:           # Multiple alertmanagers for HA
        - targets: ['alertmanager2:9093']
```

### Storage Configuration (Docker Compose)

```yaml
prometheus:
  command:
    - '--storage.tsdb.path=/prometheus'
    - '--storage.tsdb.retention.time=30d'     # Keep 30 days
    - '--storage.tsdb.retention.size=20GB'    # Or up to 20GB
    - '--web.enable-lifecycle'                # Allow runtime config reload
    - '--query.max-samples=10000000'          # Limit query size
```

### Runtime Configuration Reload

Without restarting:

```bash
# Enable with --web.enable-lifecycle flag

# Reload configuration
curl -X POST http://localhost:9090/-/reload

# Reload rules
curl -X POST http://localhost:9090/-/reload
```

---

## Alertmanager Configuration

### Configuration File Location
```
monitoring/alertmanager.yml
```

### Global Settings

```yaml
global:
  resolve_timeout: 5m                    # Auto-resolve alerts after 5m of silence
  slack_api_url: '$SLACK_WEBHOOK_URL'   # Default Slack webhook
  pagerduty_url: 'https://...'          # PagerDuty endpoint
  opsgenie_api_key: '$OPSGENIE_KEY'     # OpsGenie integration
```

### Alert Routing

Alerts matched against routes in order; first match wins:

```yaml
route:
  receiver: 'default'           # Default receiver if no match
  group_by: ['job', 'severity'] # Group alerts by these labels
  group_wait: 30s               # Wait 30s before first notification
  group_interval: 5m            # Wait 5m before next notification
  repeat_interval: 4h           # Repeat every 4 hours
  
  routes:
    # Critical alerts - immediate notification
    - match:
        severity: critical
      receiver: 'critical'
      group_wait: 10s            # Immediate
      repeat_interval: 1h        # Remind hourly
      
    # Warning alerts - delayed notification
    - match:
        severity: warning
      receiver: 'warning'
      group_wait: 30s
      repeat_interval: 4h
```

### Receiver Configuration

```yaml
receivers:
  # Slack receiver
  - name: 'slack-critical'
    slack_configs:
      - api_url: '$SLACK_WEBHOOK_URL'
        channel: '#alerts-critical'
        title: 'CRITICAL: {{ .GroupLabels.alertname }}'
        text: |
          Service: {{ .GroupLabels.job }}
          {{ range .Alerts }}
            Summary: {{ .Annotations.summary }}
            {{ .Annotations.description }}
          {{ end }}
        color: 'danger'                # Red
        send_resolved: true            # Send resolution notification
        
  # PagerDuty receiver
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '$PAGERDUTY_KEY'
        description: '{{ .GroupLabels.alertname }}'
        details:
          severity: '{{ .GroupLabels.severity }}'
          service: '{{ .GroupLabels.job }}'
          
  # Webhook receiver (custom)
  - name: 'webhook-ops'
    webhook_configs:
      - url: 'https://ops-system.company.com/alerts'
        send_resolved: true
```

### Inhibit Rules

Suppress certain alerts if others already firing:

```yaml
inhibit_rules:
  # Suppress warning if critical exists
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['job']              # Only if same job
    
  # Suppress info if warning exists
  - source_match:
      severity: 'warning'
    target_match:
      severity: 'info'
    equal: ['job']
    
  # Suppress all if node is down
  - source_match:
      alertname: 'NodeDown'
    target_match_re:
      alertname: '.+'
    equal: ['instance']
```

### Silence Management

Mute alerts via API:

```bash
# Create 1-hour silence for all critical alerts
curl -X POST http://localhost:9093/api/v1/silences \
  -d '{
    "matchers": [
      {"name": "severity", "value": "critical", "isRegex": false}
    ],
    "comment": "Scheduled maintenance",
    "duration": "1h"
  }'
```

---

## Grafana Administration

### Access & Authentication

**Default Credentials**:
```
Username: admin
Password: admin123 (or GRAFANA_ADMIN_PASSWORD from .env)
```

**Change Admin Password** (Required):
1. Log in as admin
2. Click avatar → Settings
3. Click "Change password"
4. Set strong password (16+ chars with symbols)

### User Management

**Create New User**:
1. Administration → Users → New user
2. Set username, email, password
3. Assign role:
   - **Admin**: All permissions
   - **Editor**: Can create/edit dashboards
   - **Viewer**: Read-only access

**Assign to Organizations**:
1. Administration → Organizations → [Org name]
2. Add members and assign roles

### Organization Setup

Each org has separate users/dashboards:

```
Settings → Organizations → New Organization
- Name
- Default org
- Add members
```

### Datasource Management

**Add Prometheus Datasource**:
1. Settings → Datasources → Add datasource
2. Select Prometheus
3. Configure:
   - Name: Prometheus
   - URL: http://prometheus:9090
   - Basic Auth: if required
   - Scrape Interval: 15s
   - HTTP Method: POST
4. Click "Save & test"

**Test Datasource**:
```
Settings → Datasources → [Prometheus]
Click "Save & test" button
Expected: "Data source is working"
```

### Dashboard Management

**Import Pre-built Dashboards**:
1. Dashboards → Import
2. Enter dashboard ID from Grafana site
3. Select Prometheus datasource
4. Click "Import"

**Export Dashboard**:
1. Open dashboard
2. Click menu (⋮) → Export
3. Save JSON file

**Provision Dashboards (Auto-load)**:

Files in `monitoring/grafana-provisioning/dashboards/` auto-load.

### Alerting Configuration

**Add Alert Channel**:
1. Alerting → Notification channels → New channel
2. Select type (Email, Slack, PagerDuty, etc.)
3. Configure credentials/webhook
4. Test notification
5. Save

**Dashboard Alerts**:
1. Open dashboard
2. Edit panel
3. Alert tab → Create alert
4. Set condition (e.g., `value > 80`)
5. Set notification channel
6. Save

### Plugins

**Install Plugin**:
```bash
docker-compose exec grafana grafana-cli plugins install [plugin-id]
docker-compose restart grafana
```

**Installed Plugins**:
Current setup includes: `grafana-piechart-panel`

### Security Settings

**LDAP Integration** (Enterprise):
```
Settings → Organization → LDAP
- Configure LDAP server
- Map LDAP groups to Grafana roles
```

**OAuth2** (Google, GitHub, etc.):
```
docker-compose.yml → grafana environment:
GF_AUTH_GOOGLE_ENABLED=true
GF_AUTH_GOOGLE_CLIENT_ID=your_client_id
GF_AUTH_GOOGLE_CLIENT_SECRET=your_secret
```

### Session Timeout

Configure in `docker-compose.yml`:
```
GF_SESSION_MAX_LIFE_TIME=1800  # 30 minutes
GF_LOGIN_REMEMBER_DAYS=7
```

---

## Exporter Configuration

### PostgreSQL Exporter

**Connection String**:
```
DATA_SOURCE_NAME=postgresql://user:password@host:port/database?sslmode=disable
```

**Metrics Disabled by Default** (Enable if needed):
```yaml
# docker-compose.yml environment:
QUERIES=
  "SELECT ... AS value" # Custom SQL queries
```

**Performance Tuning**:
```
PGVERSION=15  # Set correct PostgreSQL version
```

### Redis Exporter

**Connection Options**:
```
REDIS_ADDR=redis://[:password]@localhost:6379/0
REDIS_SKIP_TLS_VERIFY=false
REDIS_SKIP_CHECK_CLI=false
```

**Custom Namespace**:
```
REDIS_NAMESPACE=custom_  # Prefix all metrics
```

**Filter Metrics**:
```
REDIS_CAPTURE_CLIENT_LIST=true
REDIS_CHECK_KEY_PATTERNS=foo,bar*
```

### Node Exporter

**Collectors** (Enable/disable):
```bash
# Disable specific collectors:
--no-collector.rapl          # Power usage
--no-collector.wifi          # WiFi metrics
--no-collector.selinux       # SELinux
```

**Mount Points** (Already configured):
```
-v /proc:/host/proc:ro
-v /sys:/host/sys:ro
-v /:/rootfs:ro
--path.procfs=/host/proc
--path.sysfs=/host/sys
```

---

## Advanced Topics

### Custom Metrics

**Instrument Application Code**:

```python
from prometheus_client import Counter, Histogram, Gauge

# Counter (always increases)
request_counter = Counter(
    'hms_custom_requests_total',
    'Total custom requests',
    ['method', 'endpoint']
)

# Histogram (measure latency)
request_latency = Histogram(
    'hms_custom_request_duration_seconds',
    'Request latency',
    buckets=[0.1, 0.5, 1.0, 5.0]
)

# Gauge (can go up/down)
active_connections = Gauge(
    'hms_custom_active_connections',
    'Current active connections'
)

# Usage in view:
@request_counter.labels(method='GET', endpoint='/api/bookings/').inc()
@request_latency.time()
def get_bookings(request):
    return Response({...})
```

### Alert Rule Development

**PromQL Expression Testing**:

1. Go to Prometheus UI
2. Graph tab → Enter expression
3. Click Execute
4. Refine expression until satisfied

**Common Patterns**:

```promql
# Rate of increase
rate(metric_total[5m])

# Percentage
(metric_a / metric_b) * 100

# Average over time window
avg_over_time(metric[5m])

# Top N values
topk(10, metric)

# Filter by label
metric{job="django", severity="critical"}

# Absent metric alert
absent(metric) == 1
```

### High Availability Setup

**Multiple Prometheus Instances** (Optional):

```yaml
# Prometheus 1 (Leader)
prometheus-1:
  volumes:
    - prometheus_data_1:/prometheus
  command:
    - --web.enable-admin-api  # Enable admin API
    
# Prometheus 2 (Standby)
prometheus-2:
  volumes:
    - prometheus_data_2:/prometheus
  command:
    - --web.enable-admin-api
```

**Alertmanager HA**:
```yaml
# Multiple Alertmanager instances
alertmanager-1:
  command:
    - --cluster.peer=alertmanager-2:9094
    
alertmanager-2:
  command:
    - --cluster.peer=alertmanager-1:9094
```

### Remote Storage

Write metrics to external storage (optional):

```yaml
# In prometheus.yml:
remote_write:
  - url: "http://remote-storage:9009/api/v1/push"
    write_relabel_configs:
      # Send only critical metrics
      - source_labels: [severity]
        regex: critical
        action: keep
```

### Custom Dashboards via API

Create dashboard programmatically:

```bash
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Authorization: Bearer $TOKEN" \
  -d @dashboard.json
```

---

## Troubleshooting

### Prometheus Issues

**Problem**: High memory usage
```bash
# Reduce retention:
# In docker-compose.yml, change:
--storage.tsdb.retention.time=7d  # From 30d

docker-compose up -d prometheus
```

**Problem**: Scraping too slow
```bash
# Check scrape duration:
# Prometheus UI → Targets → Check "Last Scrape Duration"
# If > 30s, increase scrape_timeout or add more resources
```

**Problem**: Rules not evaluating
```bash
# Check rule syntax:
curl http://localhost:9090/api/v1/rules | jq .

# Reload rules:
curl -X POST http://localhost:9090/-/reload
```

### Alertmanager Issues

**Problem**: Alerts not routing to Slack
```bash
# Check webhook URL:
curl $SLACK_WEBHOOK_URL

# Verify in alertmanager.yml:
# SLACK_WEBHOOK_URL must match config

# Restart:
docker-compose restart alertmanager
```

**Problem**: Alert storm (too many alerts)
```bash
# Add inhibit rules to alertmanager.yml
# Adjust alert severity thresholds
# Increase evaluation_interval
```

### Grafana Issues

**Problem**: Can't login
```bash
# Reset admin password:
docker-compose exec grafana \
  grafana-server admin reset-admin-password newpass

# Or restart to reset:
docker-compose down grafana
docker-compose up -d grafana
```

**Problem**: Dashboard blank
```bash
# Check datasource:
# Settings → Datasources → Prometheus → Test

# Check metrics exist:
# Prometheus UI → Graph → type metric name

# Refresh dashboard: Ctrl+R
```

---

## Database Backups

### Backup Prometheus Data

```bash
# Create backup
docker-compose exec prometheus \
  tar czf /tmp/prometheus-backup.tar.gz /prometheus

# Copy to host
docker cp \
  hms-prometheus:/tmp/prometheus-backup.tar.gz \
  ./backups/prometheus-$(date +%Y%m%d).tar.gz
```

### Backup Grafana Dashboards

```bash
# Export all dashboards
for id in {1..100}; do
  curl -s http://localhost:3000/api/dashboards/id/$id \
    -H "Authorization: Bearer $TOKEN" | \
    jq '.dashboard' > dashboard-$id.json
done
```

### Automated Backup (Cron)

```bash
# Create backup script: backup.sh
#!/bin/bash
BACKUP_DIR="/backups/monitoring"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup Prometheus
docker-compose exec -T prometheus \
  tar czf /tmp/prom-$DATE.tar.gz /prometheus
docker cp hms-prometheus:/tmp/prom-$DATE.tar.gz \
  $BACKUP_DIR/prometheus-$DATE.tar.gz

# Keep last 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

# Add to crontab:
# 0 2 * * * /path/to/backup.sh
```

---

## Performance Optimization

### Query Optimization

```promql
# Bad: High cardinality regex
metric{label=~".*"}

# Good: Specific matcher
metric{label="value"}

# Bad: Complex aggregation
sum(rate(metric[5m]))

# Good: Pre-aggregate in rules
- record: 'metric:rate5m'
  expr: rate(metric_total[5m])
```

### Storage Optimization

```yaml
# Reduce cardinality:
- Drop unnecessary labels:
  metric_relabeling:
    - source_labels: [unnecessary_label]
      action: drop

# Compress old data:
# Prometheus automatically compresses data older than 2 hours
```

---

## Conclusion

This guide covers administrative configuration for the monitoring stack. For more details on specific components, refer to official documentation:

- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [Grafana Admin Guide](https://grafana.com/docs/grafana/latest/administration/)

---

**Last Updated**: February 24, 2026  
**Version**: 1.0
