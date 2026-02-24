# Monitoring & Alerting Implementation Guide
## Prometheus + Grafana for HMS

**Date**: February 24, 2026  
**Status**: Complete & Ready for Deployment

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Quick Start](#quick-start)
5. [Configuration](#configuration)
6. [Dashboards](#dashboards)
7. [Alerting](#alerting)
8. [Accessing Services](#accessing-services)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

This document outlines the comprehensive monitoring and alerting system implemented for the NEPHELE Hotel Management System using **Prometheus** (metrics collection) and **Grafana** (visualization & dashboards).

### Key Features

✅ **Real-time Metrics Collection** - Prometheus scrapes metrics from all HMS services  
✅ **Application Monitoring** - Django application metrics via django-prometheus  
✅ **Infrastructure Metrics** - CPU, memory, disk, network via Node Exporter  
✅ **Database Monitoring** - PostgreSQL metrics via postgres_exporter  
✅ **Cache Monitoring** - Redis metrics via redis_exporter  
✅ **Task Queue Monitoring** - Celery task metrics  
✅ **Alert Management** - Automated alerts via Alertmanager  
✅ **Rich Dashboards** - Pre-configured Grafana dashboards  
✅ **Slack Integration Ready** - Alert notifications to Slack channels  
✅ **PagerDuty Integration Ready** - On-call escalation support

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Monitoring Stack                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Services (Metrics Exporters)                                   │
│  ├─ Django (django-prometheus)      :8000/metrics/              │
│  ├─ PostgreSQL (postgres_exporter)  :9187/metrics               │
│  ├─ Redis (redis_exporter)          :9121/metrics               │
│  ├─ Node (node_exporter)            :9100/metrics               │
│  └─ Grafana (grafana)               :3000/metrics               │
│                                                                 │
│  ┌──────────────────┐                                           │
│  │  Prometheus      │ (scrapes all metrics)                     │
│  │  :9090           │                                           │
│  └────────┬─────────┘                                           │
│           │                                                     │
│           ├──→ stores TSDB                                      │
│           ├──→ evaluates alert rules                            │
│           └──→ sends alerts to Alertmanager                     │
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │  Alertmanager    │────│  Slack/PagerDuty │                  │
│  │  :9093           │    │  Notifications   │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                 │
│  ┌──────────────────────────────────────┐                       │
│  │      Grafana Dashboards              │                       │
│  │  :3000 (reads from Prometheus)       │                       │
│  │  ├─ System Overview                  │                       │
│  │  ├─ Django Application Metrics       │                       │
│  │  ├─ Database Performance             │                       │
│  │  └─ Celery Task Queue                │                       │
│  └──────────────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Prometheus Server (`prometheus:9090`)

**Purpose**: Time-series database that scrapes and stores metrics

**Key Features**:
- 30-day metric retention
- Real-time scraping (15s interval)
- Alert rule evaluation
- PromQL query language

**Configuration**: `monitoring/prometheus.yml`

**Scrape Targets**:
- Django: `http://django:8000/metrics/` (5s interval)
- PostgreSQL: `http://postgres-exporter:9187/metrics`
- Redis: `http://redis-exporter:9121/metrics`
- Node: `http://node-exporter:9100/metrics`
- Grafana: `http://grafana:3000/metrics`

### 2. Alertmanager (`alertmanager:9093`)

**Purpose**: Manages alerts and sends notifications

**Key Features**:
- Alert deduplication and grouping
- Slack integration
- PagerDuty integration
- Inhibition rules (reduce alert noise)

**Configuration**: `monitoring/alertmanager.yml`

**Alert Routes**:
- Critical → immediate notification via Slack #alerts-critical
- Warning → Slack #alerts-warning
- Info → Slack #alerts-info
- Service-specific routes (Django, Database, etc.)

### 3. Grafana (`grafana:3000`)

**Purpose**: Visualization and dashboard creation

**Credentials**:
- Default User: `admin`
- Default Password: `admin123` (set via `GRAFANA_ADMIN_PASSWORD` env var)

**Pre-configured Dashboards**:
1. **System Overview** - Core system metrics at a glance
2. **Django Application Metrics** - Request rates, latency, errors
3. **Database Performance** - Transactions, connections, cache hit ratio
4. **Celery Task Queue** - Task success/failure, queue length, worker status

**Datasource**: Prometheus (auto-configured)

### 4. Exporters

#### PostgreSQL Exporter (`postgres-exporter:9187`)
- Metrics: Transaction rates, connection count, cache hit ratio, table size, lock wait times
- Configuration: Auto-configured via `DATA_SOURCE_NAME` env var

#### Redis Exporter (`redis-exporter:9121`)
- Metrics: Memory usage, connected clients, evictions, replication lag
- Configuration: `REDIS_ADDR` environment variable

#### Node Exporter (`node-exporter:9100`)
- Metrics: CPU, memory, disk space, I/O wait, network
- Configuration: Mounts /proc, /sys, / for system metrics

### 5. Django Prometheus Integration

**Package**: `django-prometheus==2.3.0`

**Metrics Collected**:
- HTTP request count by status code
- HTTP request latency (histogram)
- Database query execution count
- Model insert/update/delete counts
- Cache hit/miss rates
- Exception rates
- ORM query timing

**Endpoint**: `/metrics/` (auto-configured via URL pattern)

---

## Quick Start

### 1. Start Monitoring Stack

```bash
# Build and start all services including monitoring
docker-compose up -d

# Or if already running, just start monitoring services
docker-compose up -d prometheus alertmanager grafana postgres-exporter redis-exporter node-exporter
```

### 2. Verify Services are Running

```bash
# Check container status
docker-compose ps

# Expected output:
# hms-prometheus        Running  :9090
# hms-alertmanager      Running  :9093
# hms-grafana           Running  :3000
# hms-postgres-exporter Running  :9187
# hms-redis-exporter    Running  :9121
# hms-node-exporter     Running  :9100
```

### 3. Access Services

- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **Grafana**: http://localhost:3000 (login: admin/admin123)

### 4. Verify Metric Collection

```bash
# Check Prometheus is scraping targets
curl http://localhost:9090/api/v1/targets

# Check Django metrics endpoint
curl http://localhost:8000/metrics/

# Check if alerts are loaded
curl http://localhost:9090/api/v1/rules
```

---

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# Grafana Configuration
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password
GRAFANA_URL=http://localhost:3000

# Alerting Integration (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
PAGERDUTY_SERVICE_KEY=your_pagerduty_service_key

# Monitoring Environment
ENVIRONMENT=development  # or production
```

### Prometheus Configuration

Edit `monitoring/prometheus.yml` to customize:

**Scrape Interval**:
```yaml
global:
  scrape_interval: 15s  # How often to scrape
  evaluation_interval: 15s  # How often to evaluate rules
```

**Add Custom Targets**:
```yaml
scrape_configs:
  - job_name: 'my-service'
    static_configs:
      - targets: ['my-service:8000']
```

### Alertmanager Configuration

Edit `monitoring/alertmanager.yml` to customize:

**Add Slack Channel**:
```yaml
receivers:
  - name: 'my-channel'
    slack_configs:
      - channel: '#my-alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

### Alert Rules

Edit `monitoring/alerts.yml` to customize:

**Create New Alert Rule**:
```yaml
groups:
  - name: My Alerts
    rules:
      - alert: MyCustomAlert
        expr: my_metric > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "My custom alert"
          description: "Alert value: {{ $value }}"
```

---

## Dashboards

### Available Dashboards

All dashboards are auto-provisioned in `/monitoring/grafana-provisioning/dashboards/`

#### 1. System Overview
- **Purpose**: High-level system health
- **Metrics**:
  - Service status (up/down)
  - Django requests/minute
  - HTTP error rate (5xx)
  - Average response time
  - CPU usage
  - Memory usage
  - Database connections
  - Redis memory usage

#### 2. Django Application Metrics
- **Purpose**: Deep dive into application performance
- **Metrics**:
  - HTTP request rate by status code
  - Request latency distribution (p95, p99)
  - Database query count
  - Model operations (INSERT/UPDATE/DELETE)
  - Cache hit rate
  - Exception rate
  - Requests by endpoint
  - Active connections

#### 3. Database Performance
- **Purpose**: PostgreSQL health and performance
- **Metrics**:
  - Transaction rate (commits/rollbacks)
  - Connection count
  - Cache hit ratio
  - Rows modified
  - Database size
  - Sequential vs Index scans
  - Long-running queries
  - Lock wait time

#### 4. Celery Task Queue
- **Purpose**: Background task processing health
- **Metrics**:
  - Task completion rate
  - Task success vs failure
  - Queue length by queue
  - Task execution time
  - Worker status
  - Task retry rate
  - Active tasks count
  - Failure reasons

### Creating Custom Dashboards

1. Go to Grafana: http://localhost:3000
2. Click "+" → "Dashboard"
3. Add panels with PromQL queries
4. Save dashboard

**Example PromQL Queries**:

```promql
# Request rate per minute
rate(django_http_requests_total[1m])

# 95th percentile response time
histogram_quantile(0.95, django_http_requests_latency_seconds_bucket)

# Memory usage percentage
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100

# Database cache hit ratio
rate(pg_stat_database_heap_blks_hit[5m]) / (rate(pg_stat_database_heap_blks_hit[5m]) + rate(pg_stat_database_heap_blks_read[5m]))
```

---

## Alerting

### Alert Rules

Alert rules are defined in `monitoring/alerts.yml` and grouped by service:

1. **Django Application Alerts**
   - HighHTTPErrorRate (>5% errors for 5m)
   - HighHTTPLatency (p95 > 1s for 5m)
   - HighDatabaseQueryCount (>100 qps)
   - HighModelOperationRate (>50 ops/s)

2. **Database Alerts**
   - PostgreSQLConnectionPoolAlmostFull (>80% connections)
   - PostgreSQLHighTransactionRate (>1000 tps)
   - PostgreSQLSlowQueries (detected)
   - PostgreSQLLowCacheHitRatio (<95%)

3. **Redis Alerts**
   - RedisMemoryUsageHigh (>80%)
   - RedisConnectedClientsHigh (>50)
   - RedisEvictionsHigh (detected)
   - RedisReplicationLagHigh (>100KB)

4. **Celery Alerts**
   - CeleryQueueLengthHigh (>1000 tasks)
   - CeleryTaskFailureRateHigh (>5%)
   - CeleryWorkerOffline (>1m)
   - CeleryHighTaskExecutionTime (>5m)

5. **System Alerts**
   - HighCPUUsage (>80%)
   - HighMemoryUsage (>85%)
   - DiskSpaceRunningOut (<10%)
   - HighIOWait (>20%)
   - NodeDown (>2m)

6. **Application Availability Alerts**
   - DjangoApplicationDown
   - HotelServiceHealthCheckFailed
   - CriticalEndpointSlowResponse (>2s)

### Alert Severity Levels

- **Critical**: Immediate action required (on-call alert)
- **Warning**: Investigation needed (team notification)
- **Info**: For awareness (logged only)

### Notification Routing

**Default Routes** (edit in `alertmanager.yml`):

```
Critical → #alerts-critical (Slack) + PagerDuty
Warning  → #alerts-warning (Slack)
Info     → #alerts-info (Slack)
Service-specific → #team-{service} (Slack)
```

### Testing Alerts

```bash
# Trigger an alert manually (stop Django service)
docker-compose stop django

# Check Alertmanager UI
# http://localhost:9093

# Restart Django
docker-compose start django
```

---

## Accessing Services

### Prometheus UI

**URL**: http://localhost:9090

**Key Sections**:
- **Graph**: Query metrics and visualize
- **Alerts**: View configured alert rules
- **Targets**: See all scraped targets and their status
- **Configuration**: View current configuration
- **Rules**: View loaded alert rules

**Example Queries** (execute in Graph tab):
```promql
up  # Check all services status
django_http_requests_total  # Total HTTP requests
rate(django_http_requests_total[5m])  # Request rate
histogram_quantile(0.95, rate(django_http_requests_latency_seconds_bucket[5m]))  # p95 latency
```

### Alertmanager UI

**URL**: http://localhost:9093

**Key Sections**:
- **Alerts**: Current active alerts
- **Silences**: Mute alerts for maintenance
- **Configuration**: View alerting configuration
- **Group By**: Group/filter alerts

### Grafana

**URL**: http://localhost:3000  
**Login**: admin / admin123

**Key Areas**:
- **Dashboards**: Explore pre-built and custom dashboards
- **Explore**: Ad-hoc metric exploration
- **Alerting**: Set up additional alert channels
- **Data Sources**: Manage datasources
- **Provisioning**: Import/export dashboards

---

## Troubleshooting

### Services Not Running

```bash
# Check service logs
docker-compose logs prometheus
docker-compose logs alertmanager
docker-compose logs grafana

# Restart services
docker-compose restart prometheus alertmanager grafana
```

### Prometheus Not Scraping Metrics

```bash
# Check targets status
curl http://localhost:9090/api/v1/targets

# Check specific service metrics endpoint
curl http://localhost:8000/metrics/  # Django
curl http://localhost:9187/metrics   # PostgreSQL exporter

# Check Prometheus logs
docker-compose logs prometheus | grep -i error
```

### Grafana Not Showing Metrics

1. Verify Prometheus datasource is working:
   - Grafana → Settings → Data Sources → Prometheus
   - Click "Test"

2. Verify metrics exist in Prometheus:
   - Prometheus UI → Graph → Enter metric name

3. Refresh Grafana dashboard (Ctrl+R)

### Alerts Not Firing

```bash
# Check alert rules are loaded
curl http://localhost:9090/api/v1/rules

# Check Alertmanager configuration
curl http://localhost:9093/api/v1/status

# View alert logs
docker-compose logs alertmanager
```

### High Memory Usage

Prometheus retention can be reduced in `docker-compose.yml`:

```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=7d'  # Reduce from 30d
```

### Port Conflicts

If ports are already in use, modify `docker-compose.yml`:

```yaml
prometheus:
  ports:
    - "19090:9090"  # Change host port
```

---

## Best Practices

### Monitoring

1. **Set Appropriate Scrape Intervals**
   - Default 15s is good for most use cases
   - Reduce to 5s for critical services
   - Increase to 1m for low-priority metrics

2. **Metric Naming Conventions**
   - `application_metric_name_unit`
   - Example: `django_http_requests_latency_seconds_bucket`

3. **Use Labels Effectively**
   - Add labels to identify services
   - Example: `django_http_requests_total{instance="hms-django"}`

4. **Monitor the Monitors**
   - Add alerts for Prometheus itself
   - Set up alerting channel redundancy

### Alerting

1. **Alert Fatigue Prevention**
   - Use `for` duration to avoid flake alerts
   - Implement alert grouping by service/severity

2. **Clear Alert Messages**
   - Provide actionable information
   - Include runbooks or escalation procedures

3. **Test Alerts Regularly**
   - Conduct monthly alert testing
   - Document response procedures

4. **Alert Channel Reliability**
   - Set up redundant notification channels
   - Test Slack/PagerDuty integration monthly

### Performance

1. **Data Retention**
   - Keep 30 days for production (configured)
   - Use `--storage.tsdb.retention.size` for disk space limits

2. **Query Optimization**
   - Use range vectors for aggregation
   - Avoid expensive regex patterns in queries

3. **Storage Management**
   - Monitor Prometheus disk usage
   - Plan capacity based on cardinality (number of time series)

### Security

1. **Access Control**
   - Set strong Grafana admin password
   - Use enterprise auth (LDAP/OAuth) for production

2. **Network Isolation**
   - Don't expose Prometheus/Alertmanager publicly
   - Use firewall rules to restrict access

3. **Sensitive Data**
   - Don't expose secrets in metrics
   - Relabel sensitive labels if needed

---

## Maintenance

### Regular Tasks

**Daily**:
- Review active alerts
- Check system resource usage

**Weekly**:
- Review alert trends
- Test alert channels
- Check dashboard accuracy

**Monthly**:
- Audit alert rules
- Review metric cardinality
- Test backup/recovery procedures
- Review alert response times

### Backup & Recovery

**Backup Prometheus Data**:
```bash
docker-compose exec prometheus tar czf /tmp/prometheus-backup.tar.gz /prometheus
docker cp hms-prometheus:/tmp/prometheus-backup.tar.gz ./backups/
```

**Backup Grafana Dashboards**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/dashboards/db/dashboard-name \
  > dashboard-backup.json
```

### Updates

**Update Monitoring Components**:
```bash
# Update images in docker-compose.yml
docker-compose pull
docker-compose up -d
```

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Guide](https://prometheus.io/docs/alerting/latest/overview/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Alert Rules Best Practices](https://prometheus.io/docs/practices/alerting/)

---

## Support & Next Steps

### For Issues
1. Check Prometheus targets: http://localhost:9090/targets
2. Review alert rules: http://localhost:9090/alerts
3. Check service logs: `docker-compose logs [service]`

### For Enhancement
- Add custom dashboards for business metrics
- Integrate with PagerDuty for on-call management
- Set up alert webhooks for custom notifications
- Implement custom exporters for application-specific metrics

### For Production Deployment
- ✅ Set strong Grafana admin password
- ✅ Configure Slack webhook for alerts
- ✅ Adjust alert thresholds based on baselines
- ✅ Set up backup strategy for Prometheus data
- ✅ Implement log shipping for audit trail
- ✅ Configure network policies and firewalls
- ✅ Test failover and recovery procedures

---

**Last Updated**: February 24, 2026  
**Version**: 1.0  
**Status**: Ready for Deployment
