# Monitoring System - Automated Testing Guide

**Date**: February 24, 2026  
**Version**: 1.0  
**Status**: Ready for Production

---

## Overview

This guide explains how to automatically test that the Prometheus + Grafana + Alertmanager monitoring system is operational and collecting metrics correctly.

**Two test methods are provided:**
1. **Python Test Suite** (`test_monitoring.py`) - Comprehensive with detailed reporting
2. **Bash Script** (`test_monitoring.sh`) - Lightweight, requires only curl

---

## Quick Start

### Method 1: Python Test Suite (Recommended)

```bash
# Run basic tests
python monitoring/test_monitoring.py

# Run with verbose output
python monitoring/test_monitoring.py --verbose

# Run in production mode (stricter checks)
python monitoring/test_monitoring.py --production
```

### Method 2: Bash Script

```bash
# Make executable
chmod +x monitoring/test_monitoring.sh

# Run tests
bash monitoring/test_monitoring.sh
# Or:
./monitoring/test_monitoring.sh
```

---

## Test Coverage

### Service Availability Tests
- ✅ Prometheus responding (port 9090)
- ✅ Alertmanager responding (port 9093)
- ✅ Grafana responding (port 3000)
- ✅ Django metrics endpoint (port 8000/metrics/)

### Prometheus Configuration Tests
- ✅ Prometheus health check
- ✅ Scrape targets status (all should be UP)
- ✅ Expected exporters connected
- ✅ No configuration errors

### Alert Rules Tests
- ✅ Alert rules are loaded (32 rules)
- ✅ All rules have valid syntax
- ✅ Rules grouped correctly
- ✅ Evaluation is working

### Metrics Collection Tests
- ✅ Django HTTP metrics present
- ✅ Database metrics present
- ✅ System metrics present
- ✅ Cache metrics present

### Alertmanager Tests
- ✅ Alertmanager health check
- ✅ Compatible with Prometheus
- ✅ Alert routing configured
- ✅ No configuration errors

### Grafana Tests
- ✅ Grafana responding
- ✅ 4+ dashboards loaded
- ✅ Dashboards have data
- ✅ Datasource connected

### Exporter Tests
- ✅ PostgreSQL Exporter responding
- ✅ Redis Exporter responding
- ✅ Node Exporter responding
- ✅ All metrics exposed correctly

### Docker Tests
- ✅ All containers running
- ✅ Health checks passing
- ✅ Networks connected
- ✅ No crashed containers

---

## Expected Test Output

### Success (All Tests Pass)

```
================================================================
NEPHELE MONITORING SYSTEM - AUTOMATED TEST SUITE
================================================================

Test started: 2026-02-24 10:30:45
Environment: Development

================================================================
1. SERVICE AVAILABILITY
================================================================

✅ Service: Prometheus Available - HTTP 200
✅ Service: Alertmanager Available - HTTP 200
✅ Service: Grafana Available - HTTP 200
✅ Service: Django Metrics Available - HTTP 200

================================================================
2. PROMETHEUS CONFIGURATION
================================================================

✅ Prometheus Health - OK
✅ Scrape Targets Healthy - 6/6 targets UP

================================================================
3. ALERT RULES
================================================================

✅ Alert Rules Loaded - 32 rules loaded

================================================================
4. METRICS COLLECTION
================================================================

✅ Django HTTP rate - 5 metrics found
✅ Database queries - 8 metrics found
✅ Redis metrics - 12 metrics found
✅ System metrics - 15 metrics found

================================================================
5. ALERTMANAGER
================================================================

✅ Alertmanager Health - OK
✅ Alertmanager Responsive - 0 active alerts

================================================================
6. GRAFANA DASHBOARDS
================================================================

✅ Grafana Dashboards - 4 dashboards found
  ✅ System Overview
  ✅ Django Application
  ✅ Database Performance
  ✅ Celery Task

================================================================
7. DJANGO METRICS
================================================================

✅ Django HTTP requests - Found
✅ Django Database queries - Found
✅ Django Model operations - Found

================================================================
8. DATA FRESHNESS
================================================================

✅ Metric Data Freshness - Data is 3.2s old

================================================================
9. EXPORTER COMPONENTS
================================================================

✅ PostgreSQL Exporter - HTTP 200
✅ Redis Exporter - HTTP 200
✅ Node Exporter - HTTP 200

================================================================
10. DOCKER CONTAINER STATUS
================================================================

✅ Container: prometheus - Running
✅ Container: alertmanager - Running
✅ Container: grafana - Running
✅ Container: postgres-exporter - Running
✅ Container: redis-exporter - Running
✅ Container: node-exporter - Running
✅ Container: django - Running

================================================================
Test Summary:
  Passed: 40/40
  Failed: 0/40
  Pass Rate: 100.0%
================================================================

✅ All monitoring services operational!
```

---

## Failure Diagnosis

### Prometheus Not Responding

```bash
# Check status
docker-compose ps | grep prometheus

# View logs
docker-compose logs prometheus

# Restart service
docker-compose restart prometheus

# Wait and retest
sleep 30
python monitoring/test_monitoring.py
```

### Scrape Targets DOWN

```bash
# Check Prometheus UI
# http://localhost:9090/targets

# Common issues:
# - Service not running: docker-compose restart [service]
# - Network issue: docker network inspect

# Verify exporters responding directly:
curl http://localhost:9187/metrics   # PostgreSQL
curl http://localhost:9121/metrics   # Redis
curl http://localhost:9100/metrics   # Node
curl http://localhost:8000/metrics/  # Django
```

### Alert Rules Not Loaded

```bash
# Check alert file syntax
docker-compose exec prometheus promtool check rules /etc/prometheus/alerts.yml

# Reload rules
curl -X POST http://localhost:9090/-/reload

# View in Prometheus UI
# http://localhost:9090/alerts
```

### Grafana Dashboards Empty

1. Check datasource:
   - Grafana UI → Settings → Data Sources → Prometheus
   - Click "Test" button

2. Check metrics exist:
   - Prometheus UI → Graph → Enter metric name → Execute

3. Try refreshing dashboard: Ctrl+R

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Monitor Health Check

on:
  schedule:
    # Run every hour
    - cron: '0 * * * *'
  workflow_dispatch:

jobs:
  monitoring-tests:
    runs-on: ubuntu-latest
    services:
      docker:
        image: docker:latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Start monitoring stack
        run: docker-compose up -d
      
      - name: Wait for services
        run: sleep 30
      
      - name: Run monitoring tests
        run: python monitoring/test_monitoring.py --production
      
      - name: Report results
        if: always()
        run: |
          echo "Monitoring test completed"
          # Send notifications if needed
```

### GitLab CI Example

```yaml
monitoring_health:
  stage: monitor
  script:
    - docker-compose up -d
    - sleep 30
    - python monitoring/test_monitoring.py --production
  only:
    - schedules
```

### Jenkins Example

```groovy
pipeline {
    agent any
    
    triggers {
        cron('H * * * *')  // Every hour
    }
    
    stages {
        stage('Start Services') {
            steps {
                sh 'docker-compose up -d'
                sh 'sleep 30'
            }
        }
        
        stage('Test Monitoring') {
            steps {
                sh 'python monitoring/test_monitoring.py --production'
            }
        }
    }
    
    post {
        always {
            sh 'docker-compose logs > monitoring-logs.txt'
            archiveArtifacts 'monitoring-logs.txt'
        }
        failure {
            // Send alerts
            sh 'curl -X POST $SLACK_WEBHOOK -d "Monitoring tests failed"'
        }
    }
}
```

---

## Monitoring Test Schedule

### Daily Tests
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/hms && python monitoring/test_monitoring.py

# Add to crontab:
# crontab -e
# Paste above line
```

### Weekly Verification
```bash
# Run weekly on Mondays at 10 AM
0 10 * * 1 cd /path/to/hms && python monitoring/test_monitoring.py --verbose
```

### Production Deployment
Run full tests before each deployment:
```bash
docker-compose up -d
sleep 30
python monitoring/test_monitoring.py --production --verbose

# Only proceed with deployment if tests pass (exit code 0)
if [ $? -eq 0 ]; then
    # Deploy application
    echo "✅ Monitoring OK, proceeding with deployment"
else
    # Stop deployment
    echo "❌ Monitoring tests failed, aborting deployment"
    exit 1
fi
```

---

## Test Customization

### Python Test Suite

Modify `monitoring/test_monitoring.py` to customize:

```python
# Change timeouts
CONNECT_TIMEOUT = 5  # Connection timeout in seconds
READ_TIMEOUT = 10    # Read timeout in seconds

# Change URLs
PROMETHEUS_URL = "http://prometheus.prod.example.com:9090"
GRAFANA_URL = "http://grafana.prod.example.com:3000"

# Add custom queries
test_queries = [
    ("custom_metric", "My Custom Metric"),
]

# Skip certain tests
if self.production:
    # Only run critical tests
    pass
```

### Bash Script

Modify `monitoring/test_monitoring.sh` to customize:

```bash
# Change URLs
PROMETHEUS_URL="http://prometheus.prod.example.com:9090"

# Change thresholds
RULES=20  # Expect at least 20 rules instead of 10

# Add email notifications
EMAIL="ops@example.com"
if [ "$FAILED" -gt 0 ]; then
    mail -s "Monitoring test failed" "$EMAIL" < test_output.txt
fi
```

---

## Alerting on Test Failures

### Slack Notification

```bash
#!/bin/bash
# Run tests and notify Slack on failure

python monitoring/test_monitoring.py > test_results.txt 2>&1
RESULT=$?

if [ $RESULT -ne 0 ]; then
    curl -X POST $SLACK_WEBHOOK \
      -H 'Content-type: application/json' \
      -d '{
        "text": "❌ Monitoring tests failed",
        "attachments": [{
          "color": "danger",
          "fields": [
            {"title": "Status", "value": "Failed", "short": true},
            {"title": "Time", "value": "'$(date)'", "short": true}
          ]
        }]
      }'
fi
```

### Email Notification

```bash
#!/bin/bash
# Email results

python monitoring/test_monitoring.py > test_results.txt 2>&1
mail -s "HMS Monitoring Test Results" ops@example.com < test_results.txt
```

---

## Performance Baselines

Target metrics from monitoring tests:

| Metric | Target | Acceptable | Warning |
|--------|--------|-----------|---------|
| Response Time (Prometheus) | <100ms | <500ms | >500ms |
| Response Time (Grafana) | <200ms | <1000ms | >1000ms |
| Scrape Latency | <5s | <10s | >10s |
| Metric Freshness | <5s | <30s | >30s |
| Alert Latency | <30s | <1m | >1m |
| Exporter Uptime | 99.99% | 99% | <99% |

---

## Troubleshooting Checklist

- [ ] All containers running (`docker-compose ps`)
- [ ] DNS resolution working (`curl http://localhost:9090`)
- [ ] Network connectivity (`ping docker-bridge`)
- [ ] Port availability (`lsof -i :9090`)
- [ ] Disk space adequate (`df -h`)
- [ ] Memory available (`free -h`)
- [ ] CPU not maxed (`top`)
- [ ] No file descriptor limit issues (`ulimit -n`)
- [ ] Firewall rules allow traffic
- [ ] SSL certificates valid (if using HTTPS)

---

## Support

For issues with monitoring tests:

1. Check logs: `docker-compose logs [service]`
2. Review guides: [MONITORING_AND_ALERTING_GUIDE.md](MONITORING_AND_ALERTING_GUIDE.md)
3. Check configuration: `docker-compose.yml`
4. Test manually: `curl http://localhost:9090`

---

## Next Steps

After verifying monitoring is working:

1. ✅ Adjust alert thresholds based on actual baselines
2. ✅ Configure Slack webhook for alerts
3. ✅ Set up backup of Prometheus data
4. ✅ Schedule weekly test runs
5. ✅ Create runbooks for each alert
6. ✅ Train team on dashboard usage

---

**Last Updated**: February 24, 2026  
**Version**: 1.0
