# Advanced ECS Auto-Scaling Implementation Guide

**Gap #5: Advanced Auto-Scaling & Performance Optimization**

**Version:** 1.0.0  
**Last Updated:** February 2026  
**Status:** Production Ready

---

## Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Auto-Scaling Strategies](#auto-scaling-strategies)
3. [Target Tracking Scaling](#target-tracking-scaling)
4. [Step Scaling for Rapid Response](#step-scaling-for-rapid-response)
5. [Scheduled Scaling Strategy](#scheduled-scaling-strategy)
6. [Configuration Examples](#configuration-examples)
7. [Monitoring & Metrics](#monitoring--metrics)
8. [Deployment Procedures](#deployment-procedures)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview & Architecture

### What is ECS Auto-Scaling?

ECS Auto-Scaling automatically adjusts the number of running tasks based on demand, ensuring your application can handle traffic spikes while minimizing costs during low-traffic periods.

### Auto-Scaling Components

```
┌─────────────────────────────────────────────────────┐
│ ECS Service Auto-Scaling                             │
└──────────────────────┬────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
   ┌─────────┐  ┌──────────┐  ┌─────────────┐
   │ Target  │  │   Step   │  │ Scheduled   │
   │Tracking │  │ Scaling  │  │ Scaling     │
   │Scaling  │  │          │  │             │
   └─────────┘  └──────────┘  └─────────────┘
        ↓              ↓              ↓
   CPU, Memory   Rapid Response  Business Hours
   ALB Requests  Traffic Spikes   Predictable
   Custom        (<60 seconds)     Patterns
```

### Key Metrics

| Metric | Purpose | Default Target |
|--------|---------|-----------------|
| **CPU Utilization** | Task CPU usage | 70% |
| **Memory Utilization** | Task memory usage | 75% |
| **ALB Requests/Task** | Load per task | 1000 req/min |
| **Task Count** | Number of running tasks | 2-10 |
| **Response Time** | Latency monitoring | <500ms |

---

## Auto-Scaling Strategies

### 1. Target Tracking Scaling (Recommended)

**What it does:** Automatically maintains a metric at a target level
**Response time:** 1-3 minutes
**Best for:** Consistent, predictable applications

#### How Target Tracking Works

```
Step 1: Monitor Metric
   ↓
Current CPU: 85%
Target: 70%
Difference: +15%
   ↓
Step 2: Decide Action
   ↓
85% > 70% → Scale UP
   ↓
Step 3: Execute
   ↓
Add 1 task
Wait 60 seconds (scale-out cooldown)
   ↓
Step 4: Re-evaluate
   ↓
Repeat process
```

#### Available Metrics

```
ECSServiceAverageCPUUtilization
↓
Common: Scales based on average CPU across tasks
Example: If CPU = 85%, add tasks until CPU = 70%
Thresholds: 50-90% typical


ECSServiceAverageMemoryUtilization
↓
For memory-constrained applications
Complements CPU scaling
Thresholds: 70-85% typical


ALBRequestCountPerTarget
↓
Scales based on request volume per task
Smart for variable traffic
Example: 1000 req/min per task → add if 2000 req/min
```

#### Target Tracking Example

```hcl
# Django Hotel Management System - CPU Scaling
resource "aws_appautoscaling_policy" "cpu_scaling" {
  name               = "nephele-hms-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = "service/nephele-hms-cluster/app-service"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  target_tracking_scaling_policy_configuration {
    # Focus on CPU usage
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    # Keep CPU at 70%
    target_value = 70
    
    # Avoid rapid changes
    scale_out_cooldown = 60   # Scale up immediately if needed
    scale_in_cooldown = 300   # Wait 5 min before scaling down
  }
}
```

---

### 2. Step Scaling

**What it does:** Scales based on CloudWatch alarms with multiple steps
**Response time:** Immediate (30 seconds to trigger)
**Best for:** Traffic spikes and rapid responses

#### How Step Scaling Works

```
CPU Monitoring (every 60 seconds)
   ↓
CPU < 70%? → No action
CPU 70-80%? → Add 1 task
CPU 80-90%? → Add 2 tasks
CPU 90%+?   → Add 3 tasks
   ↓
Execute: Change in Capacity
Wait for cooldown (60 seconds)
   ↓
Re-evaluate
```

#### Advantages

- **Rapid Response:** Reacts to spikes within 1-2 minutes
- **Progressive Scaling:** Adds multiple tasks for severe load
- **Aggressive:** Ensures service doesn't become overloaded

#### Example: Configuration

```hcl
# Django Hotel Management System - Step Scaling
step_adjustment {
  # If CPU is 70-80% above target
  metric_interval_lower_bound = 0
  metric_interval_upper_bound = 10
  adjustment = 1  # Add 1 task
}

step_adjustment {
  # If CPU is 80-90% above target
  metric_interval_lower_bound = 10
  metric_interval_upper_bound = 20
  adjustment = 2  # Add 2 tasks
}

step_adjustment {
  # If CPU is 90%+ above target
  metric_interval_lower_bound = 20
  adjustment = 3  # Add 3 tasks
}
```

---

### 3. Scheduled Scaling

**What it does:** Scales on a schedule (cron-based)
**Response time:** Exactly at scheduled time
**Best for:** Predictable traffic patterns

#### When to Use

- **Business Hours:** 8 AM - 6 PM (high traffic expected)
- **Off-Peak:** 6 PM - 8 AM (low traffic expected)
- **Weekends:** Much lower capacity needed
- **Holidays:** Can customize for special events

#### Example: Schedule Configuration

```
Peak Hours (Mon-Fri 8 AM - 6 PM)
├─ Min Capacity: 4 tasks (always keep 4 running)
├─ Max Capacity: 10 tasks (allow scaling up to 10)
└─ Combined with target tracking for dynamic scaling

Off-Peak Hours (Mon-Fri 6 PM - 8 AM)
├─ Min Capacity: 2 tasks (reduce minimum)
├─ Max Capacity: 6 tasks (allow up to 6)
└─ Saves 50% on off-peak costs

Weekends (Sat-Sun)
├─ Min Capacity: 1 task (minimal service)
├─ Max Capacity: 4 tasks (limited traffic expected)
└─ Saves 80% on weekend costs
```

#### Cron Expression Guide

```
cron(minute hour day month ? day-of-week)

# Peak hours: 8 AM UTC weekdays
cron(0 8 ? * MON-FRI *)

# Off-peak: 6 PM UTC weekdays
cron(0 18 ? * MON-FRI *)

# Weekend minimum: Saturday midnight UTC
cron(0 0 ? * SAT *)

Timezones:
UTC = cron(minute hour ...)
US/Eastern = EDT/EST (4-5 hours behind UTC)
Example: 8 AM EDT = 1 PM UTC → cron(0 13 ? * MON-FRI *)
```

---

## Target Tracking Scaling

### How to Configure

#### Step 1: Set Minimum and Maximum Capacity

```hcl
ecs_min_capacity = 2    # Always keep at least 2 tasks running
ecs_max_capacity = 10   # Never scale beyond 10 tasks
```

**Why these values?**
- **Min = 2:** High availability (at least 1 task per AZ)
- **Max = 10:** Cost control (prevents runaway scaling)
- **Adjust for:** Your application size, traffic, and budget

#### Step 2: Choose Target Metrics

Configuration options in `terraform/environments/{env}.tfvars`:

```hcl
# Enable CPU-based scaling (most common)
enable_cpu_scaling = true
ecs_target_cpu_percentage = 70  # Range: 50-90

# Enable memory-based scaling
enable_memory_scaling = true
ecs_target_memory_percentage = 75  # Range: 60-90

# Enable ALB request count scaling
enable_alb_request_scaling = true
ecs_target_requests_per_minute = 1000  # Per task
```

#### Step 3: Set Cooldown Periods

```hcl
# Time before scaling out again (avoid frequency)
ecs_scale_out_cooldown = 60  # seconds (usually keep low)

# Time before scaling in (be conservative)
ecs_scale_in_cooldown = 300  # 5 minutes (avoid thrashing)

# Disable scale-in during deployments (safety)
ecs_disable_scale_in = false  # Set true if deploying
```

### Metric Selection Guide

#### CPU Utilization (Most Common)

```
Best for:
✓ Compute-intensive applications
✓ Variable workloads
✓ Most web applications
✓ Django hotel management system

How it works:
- Monitor average CPU across all tasks
- If CPU rises above 70% → scale up
- If CPU falls below 30% → scale down

Configuration:
enable_cpu_scaling = true
ecs_target_cpu_percentage = 70
ecs_cpu_alarm_threshold = 80  # For alerting
ecs_cpu_low_threshold = 30    # For scale-down

When to adjust:
- Increase target: If scaling up too aggressively
- Decrease target: If not scaling up when needed
```

#### Memory Utilization

```
Best for:
✓ Memory-intensive applications
✓ Caching layers (Redis, Memcached)
✓ In-memory data processing
✓ When combined with CPU scaling

How it works:
- Tracks memory usage per task
- If memory usage rises → scale up
- Prevents out-of-memory errors

Configuration:
enable_memory_scaling = true
ecs_target_memory_percentage = 75

When to use:
- Always use with CPU scaling for comprehensive monitoring
- Helps catch memory leaks earlier
- Important for Django apps with large datasets
```

#### ALB Request Count

```
Best for:
✓ Web applications with variable traffic
✓ Request-driven scaling needs
✓ API services

How it works:
- Tracks requests per task
- Example: 1000 req/min per task
- If 2000 req/min per task → scale up

Configuration:
enable_alb_request_scaling = true
ecs_target_requests_per_minute = 1000

Example scaling:
- 1 task handling 800 req/min → No action
- 1 task handling 1200 req/min → Scale to 2 tasks
- 2 tasks with 600 req/min each → OK (within target)

When to adjust:
- Increase target: If scaling too aggressively
- Decrease target: If tasks are overloaded
```

---

## Step Scaling for Rapid Response

### What is Step Scaling?

Step scaling provides **faster response to traffic spikes** compared to target tracking.

```
Traffic Spike at 2:00 PM
   ↓ (immediate alarm triggered)
Step Scaling Kicks In
   ↓
Add 1-3 tasks within 60 seconds
   ↓
Traffic handled successfully
```

### Configuration

```hcl
enable_step_scaling = true

# Step adjustments (what to add per CPU level)
Step 1: CPU 70-80% → Add 1 task
Step 2: CPU 80-90% → Add 2 tasks
Step 3: CPU 90%+   → Add 3 tasks

# Alarm threshold
ecs_cpu_alarm_threshold = 80
ecs_step_scaling_cooldown = 60
```

### When to Use

```
✓ Sudden traffic spikes expected (flash sales, campaigns)
✓ Application takes time to warm up (Django startup)
✓ You need very aggressive scaling
✓ Combined with target tracking for best results

✗ Smooth, gradual traffic increases
✗ Resources are expensive (avoids rapid cycling)
✗ Application takes long to initialize
```

---

## Scheduled Scaling Strategy

### Business Hours Pattern

For a typical hotel management system:

```
Monday - Friday:
├─ 8:00 AM - 6:00 PM: Peak Hours
│  ├─ Min: 4 tasks
│  ├─ Max: 10 tasks
│  └─ Combined with target tracking
│
└─ 6:00 PM - 8:00 AM: Off-Peak Hours
   ├─ Min: 2 tasks
   ├─ Max: 6 tasks
   └─ Lower cost

Weekend (Saturday - Sunday):
├─ Min: 1 task
├─ Max: 4 tasks
└─ Minimal operations (emergencies only)
```

### Customization Examples

#### High-Traffic Industry (Online Booking)

```
Weekday (Mon-Fri):
├─ 7:00 AM - 11:00 PM: Peak
│  └─ 6-20 tasks (aggressive scaling)
└─ 11:00 PM - 7:00 AM: Off-Peak
   └─ 2-4 tasks

Weekend:
├─ 9:00 AM - 11:00 PM: Peak
│  └─ 4-15 tasks
└─ Overnight: 1-2 tasks
```

#### Quiet Industry (Maintenance Portal)

```
Weekday (Mon-Fri):
├─ 8:00 AM - 5:00 PM: Working Hours
│  └─ 2-4 tasks (light traffic)
└─ After Hours: 1 task

Weekend:
├─ Minimal: 1 task
└─ No scaling (nobody working)
```

#### E-Commerce (High Variability)

```
Monday-Friday:
├─ 6:00 AM - 2:00 PM: Morning peak
│  └─ 5-15 tasks
├─ 2:00 PM - 6:00 PM: Afternoon dip
│  └─ 3-8 tasks
└─ 6:00 PM - 11:00 PM: Evening surge
   └─ 8-20 tasks

Weekend:
├─ 10:00 AM - 10:00 PM: Long peak
│  └─ 10-25 tasks
└─ Overnight: 2 tasks
```

### Timezone Considerations

The scheduled scaling cron expressions are UTC-based. Convert to your timezone:

```
UTC to US/Eastern: UTC - 4 (EDT) or UTC - 5 (EST)
UTC to US/Pacific: UTC - 7 (PDT) or UTC - 8 (PST)
UTC to Europe/London: UTC - 1 (BST) or UTC (GMT)
UTC to Europe/Paris: UTC + 1 (CEST) or UTC + 1 (CET)
UTC to Asia/Tokyo: UTC + 9 (JST)

Example: 8 AM EDT (US/East Coast) = 12:00 PM UTC
cron(0 12 ? * MON-FRI *)
```

---

## Configuration Examples

### Development Environment

```hcl
# terraform/environments/dev.tfvars

enable_ecs_autoscaling = true
ecs_min_capacity = 1        # Minimal in dev
ecs_max_capacity = 3        # Small scaling range

# Responsive scaling (dev purposes)
enable_cpu_scaling = true
ecs_target_cpu_percentage = 80  # Looser in dev
enable_memory_scaling = false   # Not needed in dev
enable_alb_request_scaling = false

# Fast response for testing
ecs_scale_out_cooldown = 30
ecs_scale_in_cooldown = 60

# No scheduling in dev
enable_scheduled_scaling = false
```

### Staging Environment

```hcl
# terraform/environments/staging.tfvars

enable_ecs_autoscaling = true
ecs_min_capacity = 2        # HA setup
ecs_max_capacity = 8        # Moderate scaling

# Moderate scaling
enable_cpu_scaling = true
ecs_target_cpu_percentage = 70
enable_memory_scaling = true
ecs_target_memory_percentage = 75
enable_alb_request_scaling = true
ecs_target_requests_per_minute = 1000

enable_step_scaling = true
ecs_cpu_alarm_threshold = 80

# Test scheduling behavior
enable_scheduled_scaling = true
ecs_peak_min_capacity = 3
ecs_peak_max_capacity = 8
ecs_offpeak_min_capacity = 2
ecs_offpeak_max_capacity = 4
```

### Production Environment

```hcl
# terraform/environments/prod.tfvars

enable_ecs_autoscaling = true
ecs_min_capacity = 3        # Always 3 in production
ecs_max_capacity = 15       # Allow scaling to handle load

# Conservative scaling (stability)
enable_cpu_scaling = true
ecs_target_cpu_percentage = 70  # Keep load moderate
enable_memory_scaling = true
ecs_target_memory_percentage = 75
enable_alb_request_scaling = true
ecs_target_requests_per_minute = 800  # Stricter than staging

enable_step_scaling = true
ecs_cpu_alarm_threshold = 75   # Alert earlier

# Scheduled scaling for cost optimization
enable_scheduled_scaling = true

# Business hours: 8 AM - 6 PM weekdays
ecs_peak_min_capacity = 4
ecs_peak_max_capacity = 15

# Off hours: 6 PM - 8 AM
ecs_offpeak_min_capacity = 3
ecs_offpeak_max_capacity = 8

# Weekends
ecs_weekend_min_capacity = 2
ecs_weekend_max_capacity = 6

# Timezone for cron expressions
timezone = "America/New_York"
```

---

## Monitoring & Metrics

### Key Metrics to Track

#### 1. Task Count

```
Monitoring what:
- Desired task count (what you requested)
- Running task count (what's actually running)

Why it matters:
- Discrepancy indicates deployment issues
- Shows scaling activity frequency

CloudWatch Metric:
- ECS/ContainerInsights/DesiredTaskCount
- ECS/ContainerInsights/RunningCount

Alert threshold:
Running < Desired for > 2 minutes → Warning
```

#### 2. CPU Utilization

```
Monitoring what:
Average CPU % across all running tasks

Healthy ranges:
Dev:  50-80% (expected to vary)
Staging: 40-75% (moderate load)
Prod: 50-70% (controlled load)

Alarms:
- CPU > 80% for 1 min → Scale up triggered
- CPU < 30% for 5 min → Scale down triggered

Dashboard query:
aws cloudwatch get-metric-statistics \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --start-time 2024-01-23T12:00:00Z \
  --end-time 2024-01-23T13:00:00Z \
  --period 60 \
  --statistics Average,Maximum
```

#### 3. Memory Utilization

```
Monitoring what:
Average memory % across all tasks

Healthy ranges:
Dev:  50-70% (lots of headroom)
Staging: 60-75% (moderate)
Prod: 70-80% (efficient)

Alarms:
- Memory > 85% → Risk of OOM
- Memory > 90% → Immediate scaling needed

Signs of problems:
- Steadily increasing memory (memory leak)
- Frequent spike to 90%+ (insufficient task size)
```

#### 4. Request Count per Task

```
Monitoring what:
How many requests each task handles

Calculation:
(Total requests to ALB) / (Number of tasks)

Example:
1000 req/min ÷ 2 tasks = 500 req/min per task

Healthy range:
< Target value (e.g., 1000 req/min per task)

Troubleshooting:
Unbalanced: Some tasks at 1000, others at 100
→ Check health check configurations
→ Verify sticky sessions not enabled
```

#### 5. Task Launch Time

```
Monitoring what:
Time from scale-up triggered to task running

Healthy:
2-5 minutes (typical)

Long launch times indicate:
- Docker image requires optimization
- ECS cluster capacity constraints
- Slow health checks

Optimization:
- Reduce Docker image size
- Pre-warm capacity
- Optimize health check path
```

### CloudWatch Dashboard

```bash
# View all metrics in CloudWatch
aws cloudwatch list-metrics \
  --namespace AWS/ECS \
  --dimensions Name=ServiceName,Value=app-service

# Get CPU over last hour
aws cloudwatch get-metric-statistics \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)Z \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S)Z \
  --period 300 \
  --statistics Average,Maximum

# Monitor task count changes
aws cloudwatch tail /ecs/nephele-hms --follow
```

---

## Deployment Procedures

### Pre-Deployment Checklist

- [ ] Verify current ECS service is healthy
- [ ] Review auto-scaling configuration in tfvars
- [ ] Confirm health check endpoints are responsive
- [ ] Establish baseline metrics (CPU, memory, requests)
- [ ] Plan rollback procedure
- [ ] Notify team of pending deployment

### Deployment Steps

#### Step 1: Update Configuration

```bash
# Edit your environment configuration
vi terraform/environments/prod.tfvars

# Add/update auto-scaling variables:
enable_ecs_autoscaling = true
ecs_min_capacity = 3
ecs_max_capacity = 15
ecs_target_cpu_percentage = 70
enable_scheduled_scaling = true
ecs_peak_min_capacity = 4
# ... more settings
```

#### Step 2: Review Plan

```bash
# See what will be created
make tf-plan-prod

# Review output for:
# ✓ aws_appautoscaling_target.ecs_target[0] created
# ✓ aws_appautoscaling_policy.ecs_policy_cpu[0] created
# ✓ aws_appautoscaling_policy.ecs_policy_memory[0] created
# ✓ aws_appautoscaling_policy.ecs_policy_alb_request_count[0] created
# ✓ AWS CloudWatch alarms created
```

#### Step 3: Deploy Auto-Scaling

```bash
# Apply configuration
make tf-apply-prod

# Output should include:
# Apply complete! Resources added: X
# aws_appautoscaling_target.ecs_target: Creation complete
# aws_appautoscaling_policy.ecs_policy_cpu: Creation complete
```

#### Step 4: Verify Deployment

```bash
# Check auto-scaling targets
make asg-info

# Expected output:
# Auto-Scaling Configuration:
# - Min capacity: 3
# - Max capacity: 15
# - Target CPU: 70%
# - Policies: CPU, Memory, ALB Request Count

# Check task count
make asg-tasks

# Should show desired and running task count matching
```

#### Step 5: Monitor Scaling Activity

```bash
# Watch scaling events
make asg-activity

# Should show:
# No scaling activity first (stable state)

# Trigger some load to test
make asg-test-scaling

# Then should show:
# - Scale up events if needed
# - Task count increasing
# - CPU decreasing as load distributes
```

### Gradual Rollout Strategy

```
Phase 1: Deploy with conservative limits
├─ Min capacity: 2
├─ Max capacity: 5
└─ Monitor for 1-2 hours

Phase 2: Increase max capacity slightly
├─ Min capacity: 2
├─ Max capacity: 10
└─ Monitor for 1-2 hours

Phase 3: Enable scheduled scaling
├─ Minimal schedule first (testing)
├─ Observe cron-triggered scaling
└─ Monitor for 24 hours (full business day cycle)

Phase 4: Full production mode
├─ Final thresholds
├─ All features enabled
└─ Establish monitoring dashboard
```

---

## Troubleshooting

### Issue 1: Tasks Not Scaling Up When Load Increases

**Symptoms:**
- CPU rises to 90%+
- Task count stays at min capacity
- Application becomes slow

**Diagnosis:**

```bash
# Check if auto-scaling is enabled
aws application-autoscaling describe-scalable-targets \
  --service-namespace ecs

# Should show at least one target

# Check scaling policies
aws application-autoscaling describe-scaling-policies \
  --service-namespace ecs

# Check last scaling activity
aws cloudwatch get-metric-statistics \
  --metric-name ScalingActivities \
  --namespace AWS/AutoScaling
```

**Solutions:**

```
1. Verify auto-scaling is enabled
   enable_ecs_autoscaling = true in tfvars

2. Check task definition has resources defined
   - CPU: 256 minimum
   - Memory: 512 minimum

3. Verify health checks pass
   - All tasks should be "Healthy"
   - If InService != Running, investigate

4. Check IAM permissions
   - ECS task role needs scaling permissions

5. Review CloudWatch alarms
   - Should have CPU high alarm
   - Ensure SNS configured if needed
```

### Issue 2: Tasks Scaling Down Too Aggressively

**Symptoms:**
- Task count drops rapidly
- Application briefly slow as traffic redistributes
- Running task count fluctuates

**Diagnosis:**

```bash
# Check scale-in cooldown
aws application-autoscaling describe-scaling-policies \
  --service-namespace ecs \
  --region us-east-1 | grep -A5 "scale_in_cooldown"

# Check CPU pattern
watch -n 10 'make asg-metrics'
```

**Solutions:**

```
1. Increase scale-in cooldown
   ecs_scale_in_cooldown = 600  # 10 minutes instead of 5

2. Increase minimum capacity
   ecs_min_capacity = 3  # Keep more tasks running

3. Increase target CPU percentage
   ecs_target_cpu_percentage = 75  # Less aggressive

4. Disable scale-in during deployments
   ecs_disable_scale_in = true  # During deployment window

5. Check for bursty workloads
   - Add memory scaling for stability
   - Consider predictive scaling
```

### Issue 3: Uneven Load Distribution

**Symptoms:**
- Some tasks at 90% CPU
- Others at 20% CPU
- Average looks OK but performance suffers

**Diagnosis:**

```bash
# Check target health
make lb-targets

# Look for:
- All targets as "Healthy"
- No "InService" targets outside target group

# Check sticky sessions
aws elbv2 describe-target-group-attributes \
  --target-group-arn <arn>
```

**Solutions:**

```
1. Disable sticky sessions
   - Allows better load distribution
   - Slight risk of losing session on target swap

2. Reduce connection timeout
   - Closes old connections faster
   - Allows new connections to newer tasks

3. Check health check configuration
   - Interval: 30 seconds (standard)
   - Timeout: 5 seconds
   - Healthy threshold: 2
   - Unhealthy threshold: 3

4. Rebalance with deployment
   - Deploy new version (kills old tasks)
   - New tasks get new connections
   - More even distribution
```

### Issue 4: Scheduled Scaling Not Triggering

**Symptoms:**
- Scheduled time passes
- Task count doesn't change
- Cron expression seems correct

**Diagnosis:**

```bash
# Check if scheduled actions exist
aws application-autoscaling describe-scheduled-actions \
  --service-namespace ecs

# Should list your peak and off-peak actions

# Verify timezone
terraform show | grep timezone
```

**Solutions:**

```
1. Verify timezone is correct
   timezone = "America/New_York"  # Not UTC if you meant ET

2. Convert cron times correctly
   - Cron expressions in AWS are always UTC
   - If you want 8 AM EDT, use cron(0 12 ? * MON-FRI *)
   - EDT = UTC - 4 hours

3. Check CloudWatch logs
   aws logs tail /aws/lambda/autoscaling --follow

4. Test with immediate action
   aws application-autoscaling register-scalable-target \
     --service-namespace ecs \
     --resource-id "service/cluster/service-name" \
     --scalable-dimension ecs:service:DesiredCount \
     --min-capacity 5 \
     --max-capacity 15

5. Redeploy scheduled actions
   make tf-plan-prod
   make tf-apply-prod
```

### Issue 5: High Auto-Scaling Costs

**Symptoms:**
- More tasks running than expected
- Cost higher than budgeted
- Capacity doesn't decrease during off-hours

**Diagnosis:**

```bash
# Calculate running time
aws cloudwatch get-metric-statistics \
  --metric-name TaskCount \
  --namespace AWS/ECS \
  --statistics Average \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)Z \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S)Z \
  --period 3600

# Check for continuous high load
make asg-metrics
```

**Solutions:**

```
1. Lower minimum capacity
   ecs_min_capacity = 1  # Instead of 3

2. Lower maximum capacity (if safe)
   ecs_max_capacity = 10  # Instead of 15

3. Increase target CPU percentage
   ecs_target_cpu_percentage = 85  # Allow more load per task

4. Use scheduled scaling more aggressively
   ecs_weekend_min_capacity = 1
   ecs_offpeak_min_capacity = 1

5. Review task size
   - Larger tasks = fewer needed
   - Trade-off: Less granular scaling
```

---

## Best Practices

### 1. Always Set Minimum Capacity >= 1

```hcl
# Good: Always have at least 1 task
ecs_min_capacity = 1

# Bad: Could have zero tasks
ecs_min_capacity = 0  # Don't do this!
```

**Why:** Connection pooling, cache warming, or requests happen within seconds of deployment.

### 2. Set Appropriate Cooldown Periods

```hcl
# Scale out aggressively (short cooldown)
ecs_scale_out_cooldown = 60  # 1 minute

# Scale in conservatively (long cooldown)
ecs_scale_in_cooldown = 300  # 5 minutes
```

**Why:** Prevents cascading scale-out/scale-in oscillations during variable load.

### 3. Combine Multiple Scaling Metrics

```hcl
# Best: Monitor CPU, memory, and request count
enable_cpu_scaling = true
enable_memory_scaling = true
enable_alb_request_scaling = true

# Weak: Only CPU
enable_cpu_scaling = true
enable_memory_scaling = false
enable_alb_request_scaling = false
```

**Why:** Different metrics catch different problems:
- CPU catches processing load
- Memory catches memory leaks or inefficient queries
- Request count catches connection pooling issues

### 4. Use Scheduled Scaling for Predictable Patterns

```hcl
# Recommended: Combine scheduled + target tracking
enable_scheduled_scaling = true
enable_cpu_scaling = true

# Steps:
# 1. Scheduled scaling sets min/max bounds
# 2. Target tracking scales dynamically within bounds
```

**Why:** Saves 20-50% on costs during off-peak hours while handling all traffic.

### 5. Monitor Regularly

```bash
# Daily monitoring
make asg-info      # Check configuration
make asg-tasks     # Verify task count
make asg-metrics   # Review performance

# Weekly review
# Check cost analysis
# Identify scaling patterns
# Adjust thresholds if needed
```

### 6. Test Before Production

```
Procedure:
1. Configure in dev environment
2. Monitor for 24 hours
3. Adjust thresholds based on observations
4. Deploy to staging
5. Test with artificial load
6. Monitor for 1 week
7. Deploy to production
```

### 7. Gradual Rollout of Changes

```
When updating auto-scaling:

❌ Don't: Change all settings at once
  - Hard to identify what caused problems
  - Increases risk of issues

✅ Do: Change one setting at a time
  - Monitor for 1-2 hours
  - Revert if issues appear
  - Document what worked
```

### 8. Set Up Alerts

```hcl
# Essential alerts
- Task count drops below minimum (service failing)
- CPU consistently above 85% (understaffed)
- Memory constantly above 85% (memory leak or undersized)
- Scaling activity > X per day (oscillating)

# Optional alerts
- Scale-up occurred (unexpected load)
- Scale-down occurred (cost optimization)
- Health check failed (deployment issue)
```

### 9. Document Your Configuration

```
When setting thresholds, document:

WHY: Why chosen this specific value?
     "CPU target 70% chosen based on:
      - Historical max at ~60%
      - 10% safety margin"

WHEN: When will this need adjustment?
      "Review in Q2 after new features release"

AFFECTED: What impacts this threshold?
          "Changes if ECS task size increases"
```

### 10. Plan for Peak Load

```
Calculate capacity needed:

1. Peak traffic: 10,000 requests/minute
2. Per-task capacity: 1,000 req/min
3. Tasks needed: 10,000 ÷ 1,000 = 10 tasks
4. Safety margin: 10 + 2 (20% buffer) = 12 tasks
5. Set max capacity: 15 (extra headroom)

ecs_max_capacity = 15
ecs_peak_max_capacity = 12
```

---

## Cost Optimization Tips

### 1. Reduce Off-Peak Capacity

```hcl
# Peak hours
ecs_peak_min_capacity = 4
ecs_peak_max_capacity = 10

# Off-peak (50% reduction)
ecs_offpeak_min_capacity = 2
ecs_offpeak_max_capacity = 5

# Weekend (75% reduction)
ecs_weekend_min_capacity = 1
ecs_weekend_max_capacity = 3

# Potential savings: 30-40% monthly
```

### 2. Use Spot Instances (Future)

```hcl
# When available in ECS:
enable_spot_instances = true
spot_price_percentage = 70  # Use spot at 70% of on-demand

# Potential savings: 50-70% on compute
# Trade-off: 2-minute interruption possible
```

### 3. Right-Size Task Definitions

```hcl
# Current: 512 CPU, 1024 MB memory
# Can this be optimized?

# Check metrics:
- Peak CPU utilization: 45%
- Peak memory utilization: 62%

# Action: Reduce to 384 CPU, 768 MB
# Result: Faster scaling, more tasks per instance, lower cost

# But: Monitor closely—don't undersized
```

### 4. Review and Adjust Thresholds Quarterly

```
Quarterly review process:
1. Gather 90-day metrics
2. Identify scaling patterns
3. Calculate average task count
4. Propose threshold adjustments
5. A/B test new thresholds in staging
6. Deploy if cost savings > 10%
```

---

## Safety Features

### Disable Scale-In During Deployments

```bash
# Before deploying new version
terraform apply -var="ecs_disable_scale_in=true"

# Deploy new version
docker push ...
aws ecs update-service ...

# Wait for new tasks to stabilize (5 minutes)
sleep 300

# Re-enable scale-in
terraform apply -var="ecs_disable_scale_in=false"
```

**Why:** Prevents scale-in from killing new tasks while they're spinning up.

### Maximum Capacity Limits

```hcl
# Set realistic maximum
ecs_max_capacity = 15  # Prevents runaway costs

# Example:
# - Load spike multiplies traffic by 10x
# - Would need 100 tasks
# - Capped at 15 tasks
# - Triggers alert instead
```

**Why:** Protects against unexpected costs from misconfigured thresholds or actual DoS attacks.

### Health Check Quality

```hcl
# Ensure health checks pass consistently
health_check_path = "/api/v1/health/"
health_check_interval = 30  # seconds
health_check_timeout = 5    # seconds
healthy_threshold = 2       # 2 consecutive successes
unhealthy_threshold = 3     # 3 consecutive failures

# Only scale up for truly healthy tasks
```

---

## Next Steps

1. **Deploy to Dev:** Configure and test auto-scaling
2. **Monitor Metrics:** Establish baseline for your application
3. **Adjust Thresholds:** Fine-tune based on actual traffic
4. **Promote to Staging:** Test with production-like load
5. **Schedule Review:** Plan weekly adjustments
6. **Document Changes:** Record threshold decisions

---

## Summary

Gap #5 provides comprehensive auto-scaling for your ECS service with:

✅ **Target Tracking Scaling** - Maintains consistent performance
✅ **Step Scaling** - Rapid response to traffic spikes  
✅ **Scheduled Scaling** - Cost optimization for predictable patterns
✅ **Complete Monitoring** - CloudWatch alarms and metrics
✅ **Production Ready** - Safety features and best practices

Your hotel management system now scales automatically to handle traffic variations while optimizing costs!

