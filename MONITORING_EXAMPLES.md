# Advanced Monitoring Real-World Examples

**Gap #6: Practical Monitoring Scenarios**

**Version:** 1.0.0  
**Last Updated:** February 2026

---

## Table of Contents

1. [Example 1: Black Friday Traffic Spike](#example-1-black-friday-traffic-spike)
2. [Example 2: Memory Leak Detection](#example-2-memory-leak-detection)
3. [Example 3: Database Performance Degradation](#example-3-database-performance-degradation)
4. [Example 4: Cascading Failure Detection](#example-4-cascading-failure-detection)
5. [Example 5: Cost Anomaly Detection](#example-5-cost-anomaly-detection)
6. [Example 6: Security Incident Monitoring](#example-6-security-incident-monitoring)
7. [Example 7: Canary Deployment Validation](#example-7-canary-deployment-validation)

---

## Example 1: Black Friday Traffic Spike

### Scenario

Black Friday starts at 12 AM. Your hotel booking system expects 10x normal traffic.

### Pre-Event Setup

```hcl
# terraform/environments/prod.tfvars
# Black Friday configuration

# Lower thresholds to alert earlier
alarm_5xx_threshold = 5           # Alert at 5 instead of 10
alarm_response_time_threshold = 1.0  # Alert at 1 second
enable_xray = true
xray_sample_rate = 0.2            # Increase from 0.1 to 0.2

# Increase auto-scaling limits
ecs_max_capacity = 50             # Increased from 15
ecs_peak_max_capacity = 50

# More aggressive scaling
ecs_scale_out_cooldown = 30       # React quickly
ecs_disable_scale_in = true       # Don't scale down during surge

# Scheduled boost at peak hours
ecs_peak_min_capacity = 10        # Keep 10 always running
```

### Monitoring Strategy

```
Pre-Event (Hour -1):
├─ Dashboard: System Overview
├─ Watch: All metrics normal
├─ Alert: Ready (verify notification)
└─ Logs: Clean (no errors)

Event Start (12:00 AM):
├─ Task count: 10 → 20 → 30 → 50 (auto-scaling)
├─ CPU: 30% → 70% → 85% (controlled)
├─ Response time: 200ms → 400ms → 800ms
├─ Requests: 100/sec → 300/sec → 1000/sec
└─ 5XX errors: 0 (under control)

During Surge (12:00 - 2:00):
├─ Continuous monitoring every 2 minutes
├─ Task count stable at max (50)
├─ CPU stays ~75% (intentionally high)
├─ Response time ~800-1000ms (acceptable)
├─ No 5XX errors (healthy)
└─ Booking success rate: 99.5%

Post-Surge (2:00 - 6:00):
├─ Traffic gradually reduces
├─ Task count scales down to 35 → 20 → 15
├─ Response time returns to <400ms
├─ Re-enable scale-in at 6 AM
└─ Normal operation resumed
```

### CloudWatch Logs Query

```sql
-- Monitor transaction success during surge
fields @timestamp, transaction_id, @duration, status
| filter transaction_type = "booking"
| stats count() as total_bookings,
        sum(status = "success") as successful,
        avg(@duration) as avg_time,
        max(@duration) as max_time
  by bin(5m)

-- Expected output during 12-1 AM:
-- Time          Total   Success  AvgTime  MaxTime
-- 12:00-12:05   500     499      450ms    2100ms
-- 12:05-12:10   1200    1195     650ms    3200ms
-- 12:10-12:15   2000    1985     800ms    4500ms
```

### Alert Configuration

```bash
# Create temporary alert for Black Friday
aws cloudwatch put-metric-alarm \
  --alarm-name "black-friday-surge-complete" \
  --metric-name RequestCount \
  --namespace AWS/ApplicationELB \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 2 \
  --period 300 \
  --statistic Sum \
  --threshold 2000 \
  --alarm-actions arn:aws:sns:us-east-1:123456:blackfriday-alerts

# Delete after event
aws cloudwatch delete-alarms --alarm-names "black-friday-surge-complete"
```

### Success Criteria

- ✅ Response time stays <1.5 seconds
- ✅ Success rate stays >99%
- ✅ No 5XX errors (or <1% rate)
- ✅ Auto-scaling responds within 2 minutes
- ✅ Database maintains performance
- ✅ Cost stays within budget ($500 max)

---

## Example 2: Memory Leak Detection

### Scenario

Memory utilization gradually increases over 2 weeks:
- Week 1: 50-60% (normal)
- Week 2: 65-75% (increasing)
- Day 14: 85-90% (concerning)
- Day 15: 95%+ (critical)

### Detection Strategy

```bash
# CloudWatch Logs Query: Memory Trend
fields @timestamp, memory_usage_percent
| stats avg(memory_usage_percent) as avg_memory by bin(1h)
| sort @timestamp desc

# Expected output showing trend:
# 2024-02-25 05:00 - 94%
# 2024-02-25 04:00 - 92%
# 2024-02-25 03:00 - 90%
# 2024-02-24 23:00 - 88%
# ...
# 2024-02-10 10:00 - 52%
```

### Diagnosis Steps

```bash
# Step 1: Confirm memory leak
aws cloudwatch get-metric-statistics \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --start-time 2024-02-10T00:00:00Z \
  --end-time 2024-02-25T06:00:00Z \
  --period 3600 \
  --statistics Average \
  --output text

# Step 2: Check which process uses memory
make shell
ps aux | sort -k4 -rn | head -5

# Expected: Python/Django using 85%+

# Step 3: Find memory-heavy code
python -m memory_profiler manage.py check_bookings
```

### Root Cause Examples

```python
# Problem 1: Unbounded list accumulation
bookings = []
while True:
    bookings.extend(fetch_from_api())  # Memory grows
    
# Solution:
bookings = []
for page in range(total_pages):
    batch = fetch_from_api(page)
    process(batch)  # Don't accumulate

# Problem 2: Cache without eviction
cache = {}
def memoize(f):
    def wrapper(*args):
        if args not in cache:
            cache[args] = f(*args)  # Unbounded growth
        return cache[args]
    return wrapper

# Solution: Use LRU cache
from functools import lru_cache
@lru_cache(maxsize=1000)  # Bounded
def expensive_function(...):
    pass

# Problem 3: Connection pool not closing
connections = []
while True:
    conn = database.connect()
    connections.append(conn)  # Never closed
    
# Solution:
with database.connect() as conn:
    result = conn.execute(query)  # Auto-closes
```

### Alerting & Auto-Remediation

```bash
# Alert on memory trend
aws cloudwatch put-metric-alarm \
  --alarm-name "memory-increasing-trend" \
  --metric-name MemoryUtilization \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 10 \
  --period 3600 \
  --statistic Average \
  --threshold 85 \
  --alarm-actions arn:aws:sns:us-east-1:123456:devops

# Auto-remediation: Restart service if memory > 95%
aws cloudwatch put-metric-alarm \
  --alarm-name "memory-critical-restart" \
  --metric-name MemoryUtilization \
  --comparison-operator GreaterThanThreshold \
  --threshold 95 \
  --alarm-actions arn:aws:lambda:us-east-1:123456:restart-service
```

---

## Example 3: Database Performance Degradation

### Scenario

Database response time slowly increases over time:
- Normal: 45ms avg, p95 200ms
- Week 1: 65ms avg, p95 300ms
- Week 2: 120ms avg, p95 600ms (Noticeable)
- Week 3: 250ms avg, p95 1200ms (Crisis)

### Detection

```bash
# Query slow database operations
fields @timestamp, query, @duration
| filter @message like /SELECT|UPDATE|DELETE/
| stats count() as query_count,
        avg(@duration) as avg_time,
        pct(@duration, 95) as p95_time,
        pct(@duration, 99) as p99_time
  by query
| filter avg_time > 100
| sort avg_time desc

# Expected output:
# Query: SELECT * FROM bookings WHERE...
# Count: 5000, Avg: 250ms, p95: 800ms, p99: 1500ms  ← Problem!
```

### Root Causes

```sql
-- Problem 1: Missing Index
-- Query: SELECT * FROM bookings WHERE status = 'pending'
-- Issue: Table scan on 1M rows, takes 500ms
-- Solution:
CREATE INDEX idx_bookings_status ON bookings(status);
-- Now: 2ms with index ✅

-- Problem 2: Inefficient JOIN
SELECT b.id, b.guest_id, g.name
FROM bookings b
INNER JOIN guests g ON b.guest_id = g.id
WHERE b.created_at > '2024-02-01';
-- Issue: Cartesian product if join not optimized
-- Solution:
SELECT b.id, b.guest_id, g.name
FROM bookings b
INNER JOIN guests g ON b.guest_id = g.id AND g.is_active = true
WHERE b.created_at > '2024-02-01';
-- Add: CREATE INDEX idx_guests_active ON guests(is_active, id);

-- Problem 3: Full Table Scan
SELECT COUNT(*) FROM bookings;
-- Issue: Counts all 10M rows every time
-- Solution:
-- Use cached count or:
SELECT COUNT(*) FROM bookings WHERE created_at > now() - '1 day'::interval;
```

### Monitoring Queries

```bash
# RDS Performance Metrics
aws cloudwatch get-metric-statistics \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --dimensions Name=DBInstanceIdentifier,Value=nephele-hms-db \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S)Z \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S)Z \
  --period 3600 \
  --statistics Average,Maximum

# Monitor slow query log
aws rds describe-db-log-files \
  --db-instance-identifier nephele-hms-db \
  --filename-contains "slow-query"

# Query slow logs
aws rds download-db-log-file-portion \
  --db-instance-identifier nephele-hms-db \
  --log-file-name "slow-query-log"
```

---

## Example 4: Cascading Failure Detection

### Scenario

One service fails, triggering failures across the stack:

```
1. Auth Service Timeout
   ↓
2. API Requests Queue Up (hitting auth, timing out)
   ↓
3. Memory Fills (pending requests)
   ↓
4. Task OOMKills (out of memory kill)
   ↓
5. Task Restarts, Repeat
   (Cascading failure loop)
```

### Detection Pattern

```
Normal State:
├─ Auth response time: 50ms
├─ API response time: 200ms
├─ Error rate: 0.1%
├─ Task count: 5
└─ Memory: 60%

Failure State:
├─ Auth response time: 5000ms (50→5000!)
├─ API response time: 10000ms (timeout)
├─ Error rate: 45% (0.1%→45%!)
├─ Task count: 5→10 (auto-scaling)
├─ Memory: 60%→95% (rapid)
└─ Pattern: Auth fails, API waits, memory fills
```

### Detection Query

```bash
# Multi-metric correlation query
fields @timestamp, service, @duration, status_code
| filter service in ["auth", "api", "booking"]
| stats count() as request_count,
        avg(@duration) as avg_time,
        pct(@duration, 95) as p95,
        sum(status_code >= 500) as errors
  by service, bin(1m)
| filter errors > 10 and avg_time > 1000

# If auth fails with errors, others will follow
```

### Automatic Isolation

```hcl
# Circuit breaker pattern
# Don't call failing service, fail fast instead

resource "aws_cloudwatch_metric_alarm" "auth_failure_cascade" {
  alarm_name           = "auth-service-failure-circuit-breaker"
  metric_name          = "HTTPCode_Target_5XX_Count"
  namespace            = "AWS/ApplicationELB"
  comparison_operator  = "GreaterThanThreshold"
  evaluation_periods   = 2
  period               = 60
  statistic            = "Sum"
  threshold            = 20    # More than 20 5xx in 1 minute
  alarm_actions        = [aws_lambda_function.circuit_breaker.arn]

  # Lambda will:
  # 1. Disable auth-requiring endpoints
  # 2. Return 503 Service Unavailable (don't wait)
  # 3. Prevent cascade
  # 4. Auto-resolve when auth recovers
}
```

---

## Example 5: Cost Anomaly Detection

### Scenario

Your AWS bill is usually $500/month. Last month: $1200/month.

### Root Causes

```
Possible Issues:
├─ Auto-scaling went to max capacity unnecessarily (40%)
├─ Under-utilized Elasticsearch cluster running 24/7 (20%)
├─ Data transfer costs from log export to S3 (15%)
├─ Database running larger instance than needed (10%)
├─ Unused NAT Gateway charges (10%)
└─ Other (5%)

Example Spending:
├─ ECS compute: $300 (should be $100) ← Problem!
├─ RDS: $200 (should be $150)
├─ Data Transfer: $150 (new!)
├─ ALB: $50 (stable)
└─ Other: $500 (stable)
```

### Detection Query

```bash
# AWS Cost Explorer analysis
aws ce get-cost-and-usage \
  --time-period Start=2024-02-01,End=2024-02-28 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --filter file://filter.json

# filter.json:
{
  "Dimensions": {
    "Key": "SERVICE",
    "Values": ["Amazon Elastic Container Service", "Amazon Relational Database Service"]
  }
}

# Expected output showing spike on Feb 15
# Date           ECS         RDS         Total
# 2024-02-01    $3.00      $5.00      $8.00
# ...
# 2024-02-15   $15.00     $5.00     $20.00  ← Spike!
# 2024-02-16   $18.00     $5.00     $23.00  ← Continues!
```

### Root Cause Analysis

```bash
# Check if auto-scaling caused it
aws application-autoscaling describe-scaling-activities \
  --service-namespace ecs \
  --query 'ScalingActivities[?StartTime > `2024-02-15`]'

# Expected output:
# Scale-out triggered multiple times on Feb 15

# Check actual task count
aws cloudwatch get-metric-statistics \
  --metric-name DesiredTaskCount \
  --namespace ECS/ContainerInsights \
  --dimensions Name=ClusterName,Value=prod-cluster \
  --start-time 2024-02-13T00:00:00Z \
  --end-time 2024-02-17T00:00:00Z \
  --period 1440 \
  --statistics Average

# Expected timeline:
# Date      Avg Tasks   Cost/Day
# Feb 13      5        $15
# Feb 14      5        $15
# Feb 15     10        $30   ← Doubled!
# Feb 16     15        $45   ← Kept scaling
```

### Cost Anomaly Alert

```hcl
resource "aws_ce_anomaly_monitor" "ecs_spending" {
  name               = "ECS Cost Anomaly"
  monitor_type       = "DIMENSIONAL"
  monitor_dimension  = "SERVICE"
  
  monitor_specification = jsonencode({
    Dimensions = {
      Key    = "SERVICE"
      Values = ["Amazon Elastic Container Service"]
    }
  })
  
  # Alert if 20% spike
  threshold = 20
}

resource "aws_ce_anomaly_subscription" "ecs_spending_alert" {
  name      = "ECS Anomaly Alert"
  frequency = "DAILY"
  
  monitor_arn_list = [aws_ce_anomaly_monitor.ecs_spending.arn]
  
  sns_topic_arn = aws_sns_topic.cost_alerts.arn
}
```

---

## Example 6: Security Incident Monitoring

### Scenario

Someone tries to brute force your API:
- Normal: ~100 failed logins/day
- Attack: 10,000 failed logins in 1 hour

### Detection

```bash
# Query failed authentication attempts
fields @timestamp, username, status_code
| filter @message like /login|auth/ and status_code = 401
| stats count() as failed_attempts by username, bin(5m)
| filter failed_attempts > 20  # >20 in 5 min is suspicious

# Expected during attack:
# Time          Username      Count
# 12:00-12:05   attacker      150  ← Spike!
# 12:05-12:10   attacker      200  ← Spike!
# 12:10-12:15   attacker      180
# ...

# Identify attack IP
fields @timestamp, source_ip, username, status_code
| filter @message like /login/ and status_code = 401
| stats count() as attempts by source_ip
| filter attempts > 50  # >50 failed from same IP
```

### Automatic Response

```python
# Django middleware - auto-block suspicious IPs
from django.utils.deprecation import MiddlewareMixin
from django_ratelimit.decorators import ratelimit

class SecurityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = request.META.get('REMOTE_ADDR')
        
        # Block if >100 failed attempts in 1 hour
        failed_attempts = get_failed_attempts_ip(ip)
        if failed_attempts > 100:
            block_ip(ip, duration=3600)  # 1 hour block
            return HttpResponse("Access Denied", status=403)
        
        return None
```

### Alert Configuration

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "high-login-failure-rate" \
  --metric-name FailedLoginCount \
  --namespace CustomApp \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --period 300 \
  --statistic Sum \
  --threshold 50 \
  --alarm-actions arn:aws:sns:us-east-1:123456:security-alerts
```

---

## Example 7: Canary Deployment Validation

### Scenario

Deploying new version with 10% traffic. Need to validate it's working correctly.

### Monitoring Strategy

```
Pre-Deployment:
├─ Establish baseline metrics
│  ├─ Response time: 350ms avg
│  ├─ Error rate: 0.1%
│  └─ Success rate: 99.9%
└─ Create comparison dashboard

During Canary (10% traffic):
├─ Compare canary vs stable
│  ├─ Response time: Canary 350ms, Stable 340ms ✓
│  ├─ Error rate: Canary 0.15%, Stable 0.08% (watch)
│  └─ Success rate: Canary 99.85%, Stable 99.95%
├─ Monitor for 30 minutes
└─ Decision: Continue or rollback

Key Metrics to Compare:
├─ Response time distribution (p95, p99)
├─ Error rates by endpoint
├─ Database query performance
├─ Specific feature success rates
└─ Resource utilization
```

### Canary Monitoring Query

```bash
# Compare canary vs stable
fields @timestamp, version, @duration, status_code
| filter version in ["v1.0-stable", "v1.1-canary"]
| stats count() as request_count,
        avg(@duration) as avg_time,
        pct(@duration, 95) as p95_time,
        sum(status_code >= 500) as errors
  by version, bin(5m)

# Expected safe deployment:
# Time      Version        Count  AvgTime  p95    Errors
# 12:00-05  v1.0-stable   9000   345ms    1100ms    8
# 12:00-05  v1.1-canary   1000   380ms    1500ms   2  ← Slightly slower but acceptable
# 12:05-10  v1.0-stable   9000   348ms    1120ms    9
# 12:05-10  v1.1-canary   1000   370ms    1400ms   1  ← Improving!
```

### Auto-Rollback Logic

```python
# Compare metrics between stable and canary
def should_rollback():
    canary_metrics = get_metrics("canary")
    stable_metrics = get_metrics("stable")
    
    # Rollback if canary is significantly worse
    checks = {
        "response_time": canary_metrics.p95 > stable_metrics.p95 * 1.5,  # >50% slower
        "error_rate": canary_metrics.error_rate > stable_metrics.error_rate * 5,  # >5x errors
        "cpu_usage": canary_metrics.cpu > 95,  # Using too much CPU
        "memory_usage": canary_metrics.memory > 95,  # Using too much memory
    }
    
    # Rollback if any critical check fails
    failures = sum(1 for v in checks.values() if v)
    if failures >= 2:
        logger.error("Canary deployment failing checks, rolling back")
        return True
    
    return False

# If rollback needed
if should_rollback():
    deployment.rollback()
    sns_topic.publish("Canary deployment rolled back - manual review required")
```

---

## Summary

These 7 examples cover the most common monitoring scenarios:

1. **Capacity Planning** - Handle predictable spikes
2. **Performance** - Detect memory leaks and slowness  
3. **Infrastructure** - Database issues
4. **Reliability** - Cascading failures
5. **Cost** - Unexpected spending
6. **Security** - Attack detection
7. **Quality** - Deployment validation

Each has:
- ✅ Detection mechanism
- ✅ Root cause analysis
- ✅ Monitoring queries
- ✅ Automated response
- ✅ Alert configuration

---

Use these as templates for your own monitoring scenarios!

