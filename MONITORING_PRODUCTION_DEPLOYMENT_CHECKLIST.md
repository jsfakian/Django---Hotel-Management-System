# Monitoring & Alerting Production Deployment Checklist

**Date**: February 24, 2026  
**Project**: NEPHELE HMS Monitoring Stack  
**Environment**: Production

---

## Pre-Deployment Phase

### Infrastructure Requirements
- [ ] Verify Docker and Docker Compose installed
- [ ] Check disk space for Prometheus (minimum 20GB for historical data)
- [ ] Verify network connectivity between services
- [ ] Confirm firewall rules allow service communication
- [ ] Plan IP addresses/hostnames for all services
- [ ] Allocate resources: 2+ CPU cores, 4GB+ RAM minimum

### Environment Configuration
- [ ] Create `.env` file with production values
- [ ] Set `GRAFANA_ADMIN_PASSWORD` to strong password (>16 chars)
- [ ] Set `GRAFANA_URL` to production domain
- [ ] Set `ENVIRONMENT=production` in environment variables
- [ ] Configure `SLACK_WEBHOOK_URL` for alert channel
- [ ] Configure `PAGERDUTY_SERVICE_KEY` if applicable
- [ ] Document all credentials in secure location (vault/1Password)

### Backup Strategy
- [ ] Set up automated Prometheus data backup (daily)
- [ ] Document backup location and retention policy (3 months minimum)
- [ ] Test backup restoration procedure
- [ ] Set up automated Grafana dashboard backups
- [ ] Store backup credentials securely

---

## Deployment Phase

### Service Startup
- [ ] Pull latest images: `docker-compose pull`
- [ ] Build application: `docker-compose build`
- [ ] Start services: `docker-compose up -d`
- [ ] Wait 30 seconds for initialization
- [ ] Verify all containers running: `docker-compose ps`
- [ ] Verify no errors in container logs

### Health Verification
- [ ] Check Prometheus: `curl http://prometheus:9090/-/healthy`
- [ ] Check Alertmanager: `curl http://alertmanager:9093/-/healthy`
- [ ] Check Grafana: `curl http://grafana:3000/api/health`
- [ ] Check all exporters responding:
  - [ ] PostgreSQL: `http://postgres-exporter:9187/metrics`
  - [ ] Redis: `http://redis-exporter:9121/metrics`
  - [ ] Node: `http://node-exporter:9100/metrics`
  - [ ] Django: `http://django:8000/metrics/`

### Target Verification
- [ ] Prometheus UI: Check all targets are "UP"
  - [ ] Django (green)
  - [ ] PostgreSQL Exporter (green)
  - [ ] Redis Exporter (green)
  - [ ] Node Exporter (green)
  - [ ] Grafana (green)
- [ ] No targets showing "DOWN" status
- [ ] All scrape errors are 0

### Alert Rules Verification
- [ ] Prometheus UI: Verify all 32 alert rules loaded
- [ ] No syntax errors in alert definitions
- [ ] Alert rules grouped correctly by service
- [ ] Severity labels correctly applied

### Grafana Verification
- [ ] Login with admin credentials
- [ ] Verify 4 dashboards visible
- [ ] Verify all dashboard panels loading data
- [ ] Verify no missing panels or errors
- [ ] Verify Prometheus datasource connected
- [ ] Change admin password immediately
- [ ] Create additional admin/viewer accounts as needed

### Metric Collection
- [ ] Verify metrics collected (Prometheus → Graph → `up`)
- [ ] Check metric freshness (<30s old)
- [ ] Verify all target types collecting data:
  - [ ] Application metrics
  - [ ] Database metrics
  - [ ] System metrics
  - [ ] Cache metrics

---

## Configuration Phase

### Alert Configuration
- [ ] Review all 32 alert rules
- [ ] Adjust thresholds based on baseline data (if available)
- [ ] Document reasoning for threshold values
- [ ] Test each alert category:
  - [ ] Critical severity alerts
  - [ ] Warning severity alerts
  - [ ] Info severity alerts

### Notification Setup
- [ ] Test Slack webhook connectivity
  - [ ] Send test message: `curl -X POST -d '{"text":"Test"}' $SLACK_WEBHOOK_URL`
- [ ] Verify message format in Slack channel
- [ ] Verify all 6 alert channels created/exist:
  - [ ] #alerts-critical
  - [ ] #alerts-warning
  - [ ] #alerts-info
  - [ ] #team-backend
  - [ ] #team-database
  - [ ] #team-infrastructure
- [ ] Configure Slack notification frequency (avoid spam)
- [ ] If using PagerDuty:
  - [ ] Verify service key configured
  - [ ] Test alert escalation workflow
  - [ ] Verify on-call schedule matches

### Dashboard Customization
- [ ] Create company-branded Grafana instance
- [ ] Customize dashboard titles/descriptions
- [ ] Set appropriate auto-refresh intervals
- [ ] Configure dashboard permissions:
  - [ ] Admin: Full access
  - [ ] Viewers: Read-only access
  - [ ] Editors: Can edit dashboards
- [ ] Create business metrics dashboard if applicable
- [ ] Add runbooks/documentation links to dashboards

---

## Data & Persistence Phase

### Volume Management
- [ ] Verify Prometheus volume mounted correctly
- [ ] Verify AlertManager volume mounted correctly
- [ ] Verify Grafana volume mounted correctly
- [ ] Confirm volumes are on persistent storage
- [ ] Set up automatic volume backups

### Data Retention
- [ ] Configure Prometheus retention:
  - [ ] By time: `--storage.tsdb.retention.time=30d`
  - [ ] By size: `--storage.tsdb.retention.size=20GB`
- [ ] Document data retention policy
- [ ] Plan for long-term archival if needed

### Database Configuration
- [ ] Verify PostgreSQL metrics accessible
- [ ] Verify Redis metrics accessible
- [ ] Configure slow query threshold for alerts
- [ ] Set up query log rotation if enabled

---

## Security Phase

### Access Control
- [ ] Change Grafana admin password (strong: 16+ chars, mixed case, symbols)
- [ ] Set up HTTPS/TLS certificates for production domains
- [ ] Configure network policies:
  - [ ] Prometheus not exposed publicly
  - [ ] Alertmanager not exposed publicly
  - [ ] Grafana behind reverse proxy with auth
- [ ] Set up firewall rules:
  - [ ] Port 3000 (Grafana) accessible to internal network
  - [ ] Ports 9090, 9093 (Prometheus/Alertmanager) internal only
  - [ ] Exporter ports internal only
- [ ] Configure VPN/SSH access for remote monitoring

### Data Security
- [ ] Ensure metrics don't contain sensitive data (API keys, passwords)
- [ ] Relabel metrics if needed to remove sensitive labels
- [ ] Configure encryption for stored Prometheus data (if required)
- [ ] Set up audit logging for Grafana access
- [ ] Enable Grafana session timeout (30 min recommended)

### Secrets Management
- [ ] Never commit `.env` to version control
- [ ] Store credentials in secure vault (Vault, 1Password, etc.)
- [ ] Rotate credentials regularly (quarterly minimum)
- [ ] Document credential rotation procedure
- [ ] Set up alerts for credential expiration

---

## Monitoring Configuration Phase

### Baseline Establishment
- [ ] Let system run for 24 hours to establish baseline
- [ ] Review actual values vs alert thresholds
- [ ] Adjust thresholds to eliminate false positives
- [ ] Document baseline values for future reference
- [ ] Create comparison benchmarks

### Alert Testing
- [ ] Test each alert rule manually:
  ```bash
  # Stop a service to trigger alert
  docker-compose stop django
  
  # Verify alert fires within configured time
  # Check Prometheus Alerts page
  # Check Alertmanager shows alert
  # Check Slack notification received
  
  # Restart service
  docker-compose start django
  ```
- [ ] Verify all alert channels receive notifications
- [ ] Document alert response procedures
- [ ] Test alert resolution (service comes back online)

### Performance Baseline
- [ ] Document baseline CPU usage percentage
- [ ] Document baseline memory usage percentage
- [ ] Document baseline disk I/O patterns
- [ ] Document baseline network traffic
- [ ] Document baseline request latency
- [ ] Document baseline error rate

---

## Integration Phase

### External Integrations
- [ ] Verify Slack webhook authentication
- [ ] Test alert delivery to Slack
- [ ] Verify message formatting in Slack
- [ ] Configure alert notification threads
- [ ] If PagerDuty:
  - [ ] Test incident creation
  - [ ] Verify escalation policies
  - [ ] Test resolution workflow
- [ ] If Webhooks:
  - [ ] Configure external webhook URLs
  - [ ] Test payload format
  - [ ] Verify receipt at external system

### Logging Integration
- [ ] Configure log aggregation if applicable
- [ ] Link Prometheus alerts to centralized logging
- [ ] Set up alert log retention policy
- [ ] Create alert audit trail

---

## Documentation Phase

### Operational Documentation
- [ ] Create runbooks for top 10 alerts
  - [ ] Alert description
  - [ ] Potential causes
  - [ ] Resolution steps
  - [ ] Escalation path
- [ ] Document service URLs and access methods
- [ ] Document credential storage location
- [ ] Create troubleshooting guide
- [ ] Document manual metric queries for common issues

### Team Training
- [ ] Train team on alert interpretation
- [ ] Train team on dashboard usage
- [ ] Train team on Grafana navigation
- [ ] Train team on alert response procedures
- [ ] Train team on metric exploration (PromQL basics)
- [ ] Document on-call rotation procedures

### Maintenance Documentation
- [ ] Create daily checklist (reviewed by on-call)
- [ ] Create weekly maintenance tasks
- [ ] Create monthly review procedures
- [ ] Create quarterly capacity planning checklist
- [ ] Document backup/restore procedures

---

## Monitoring the Monitors Phase

### Self-Monitoring
- [ ] Set up alerts for Prometheus down
- [ ] Set up alerts for Alertmanager down
- [ ] Set up alerts for Grafana down
- [ ] Monitor Prometheus disk usage
- [ ] Monitor Prometheus memory usage
- [ ] Monitor data retention vs available disk
- [ ] Alert on high cardinality (too many metrics)

### Capacity Planning
- [ ] Monitor metric cardinality growth
- [ ] Plan disk space growth (project 3-6 months)
- [ ] Monitor resource consumption trends
- [ ] Plan for scaling if growth detected
- [ ] Set up capacity alerts (80% threshold)

---

## Validation Phase

### Functionality Validation
- [ ] All dashboards load without errors
- [ ] All metrics visible and recent (< 1 min old)
- [ ] All alert rules configured and active
- [ ] Alert notifications test successful
- [ ] Query examples from documentation work

### Performance Validation
- [ ] Prometheus response latency < 500ms
- [ ] Alertmanager processing < 1s
- [ ] Grafana dashboard load time < 3s
- [ ] No memory leaks detected
- [ ] CPU usage stable and predictable

### Data Quality Validation
- [ ] No gaps in metric data
- [ ] All expected labels present
- [ ] Metric values reasonable (no outliers)
- [ ] Time synchronization correct across services
- [ ] Historical data complete

---

## Production Go-Live Phase

### Final Approval
- [ ] [ ] Security review completed and approved
- [ ] [ ] Performance review completed and approved
- [ ] [ ] Operations team sign-off
- [ ] [ ] Management approval received
- [ ] [ ] Stakeholder notification sent

### Cutover
- [ ] [ ] Notify team of monitoring deployment
- [ ] [ ] Document known issues or limitations
- [ ] [ ] Set up on-call rotation
- [ ] [ ] Configure alert paging/escalation
- [ ] [ ] Brief on-call team on alerts

### Post-Go Live Monitoring
- [ ] [ ] First 24 hours: continuous monitoring
- [ ] [ ] Watch for false positive alerts
- [ ] [ ] Monitor resource consumption
- [ ] [ ] Capture any issues/improvements
- [ ] [ ] Document gaps for future phases

---

## Post-Deployment (First Week)

### Daily Tasks
- [ ] Review alert logs for false positives
- [ ] Verify all services healthy
- [ ] Check Prometheus data freshness
- [ ] Verify backup jobs completed
- [ ] Monitor system resource usage

### Action Items
- [ ] Adjust alert thresholds if too noisy
- [ ] Create any missing dashboards
- [ ] Document any issues discovered
- [ ] Follow up on training gaps
- [ ] Update runbooks with real-world learnings

### Sign-Off
- [ ] Production monitoring operational ✅
- [ ] Team trained and confident ✅
- [ ] Documentation complete ✅
- [ ] Performance acceptable ✅
- [ ] Alerting working reliably ✅

---

## Rollback Plan (If Needed)

If significant issues discovered:
1. Stop monitoring containers: `docker-compose stop prometheus alertmanager grafana`
2. Keep exporter services running (lower risk)
3. Manual monitoring via logs/CLI until fixed
4. Restart services after fixes: `docker-compose up -d`
5. Re-test: `docker-compose ps` and verify health

---

## Maintenance Checklist (Recurring)

### Daily (By On-Call)
- [ ] Review active alerts
- [ ] Check system status dashboard
- [ ] Verify no service outages

### Weekly
- [ ] Test Slack alert channel
- [ ] Review alert accuracy
- [ ] Check backup completion

### Monthly
- [ ] Audit alert rule effectiveness
- [ ] Review metric cardinality growth
- [ ] Update runbook documentation
- [ ] Test disaster recovery procedure

### Quarterly
- [ ] Comprehensive review of all alerts
- [ ] Capacity planning review
- [ ] Security review of credentials/access
- [ ] Performance optimization review

---

## Escalation Contacts

| Role | Name | Phone | Slack |
|------|------|-------|-------|
| Monitoring Lead | [Name] | [Phone] | @[user] |
| On-Call | [Rotation] | [Phone] | @[channel] |
| CTO | [Name] | [Phone] | @[user] |
| DevOps | [Name] | [Phone] | @[user] |

---

## Success Criteria

✅ All containers running with health status "healthy"  
✅ All Prometheus targets status "UP"  
✅ All 32 alert rules loaded and active  
✅ All 4 dashboards displaying real-time data  
✅ Alert notifications delivered to Slack  
✅ No errors in container logs  
✅ Team trained and confident  
✅ On-call rotation established  
✅ Backup procedures verified  
✅ Documentation complete and accessible  

---

**Implementation Date**: February 24, 2026  
**Version**: 1.0  
**Status**: Ready for Production Deployment
