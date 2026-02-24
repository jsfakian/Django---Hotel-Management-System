# Advanced ECS Auto-Scaling Real-World Examples

**Gap #5: Practical Implementation Scenarios**

**Version:** 1.0.0  
**Last Updated:** February 2026

---

## Table of Contents

1. [Example 1: Hotel Management System Peak Load](#example-1-hotel-management-system-peak-load)
2. [Example 2: Microservice Scaling by Component](#example-2-microservice-scaling-by-component)
3. [Example 3: Festival/Special Event Scaling](#example-3-festivalspecial-event-scaling)
4. [Example 4: Gradual Traffic Migration](#example-4-gradual-traffic-migration)
5. [Example 5: Memory-Intensive Operations](#example-5-memory-intensive-operations)
6. [Example 6: Scaling with Cost Constraints](#example-6-scaling-with-cost-constraints)
7. [Example 7: Cross-Region Failover Scaling](#example-7-cross-region-failover-scaling)

---

## Example 1: Hotel Management System Peak Load

### Scenario

Your Django hotel management system experiences predictable load patterns:
- **8 AM - Noon:** Check-ins start (high load)
- **Noon - 3 PM:** Lunch period (medium load)
- **3 PM - 6 PM:** Check-outs + advance bookings (high load)
- **6 PM - 8 AM:** Night shift, minimal operations

### Configuration

```hcl
# terraform/environments/prod.tfvars

# Base scaling
enable_ecs_autoscaling = true
ecs_min_capacity = 2        # Never less than 2 for HA
ecs_max_capacity = 12       # Handle 3x normal load

# Target tracking for stable performance
enable_cpu_scaling = true
ecs_target_cpu_percentage = 70   # Keep moderate

enable_memory_scaling = true
ecs_target_memory_percentage = 75

enable_alb_request_scaling = true
ecs_target_requests_per_minute = 1200

# Rapid response to spikes
enable_step_scaling = true
ecs_cpu_alarm_threshold = 80
ecs_step_scaling_cooldown = 60   # Quick response

# Scheduled scaling for predictable patterns
enable_scheduled_scaling = true
timezone = "America/Chicago"     # Hotel timezone

# Peak: 8 AM - 6 PM weekdays (check-in/check-out times)
ecs_peak_min_capacity = 4        # Min 4 during peak
ecs_peak_max_capacity = 12       # Scale up to 12

# Off-peak: 6 PM - 8 AM (maintenance staff only)
ecs_offpeak_min_capacity = 2     # Min 2 for HA
ecs_offpeak_max_capacity = 6     # Cap at 6

# Weekend: Slightly less predictable
ecs_weekend_min_capacity = 3     # Could be busy or quiet
ecs_weekend_max_capacity = 10
```

### Scaling Plan

```
MONDAY - FRIDAY SCHEDULE:
├─ 8:00 AM (cron: 0 8 ? * MON-FRI *)
│  └─ Scale UP for check-ins
│     ├─ Min capacity: 4
│     ├─ Max capacity: 12
│     └─ Combined with CPU scaling

├─ 6:00 PM (cron: 0 18 ? * MON-FRI *)
│  └─ Scale DOWN after busy hours
│     ├─ Min capacity: 2
│     ├─ Max capacity: 6
│     └─ Maintain HA for emergencies

SATURDAY - SUNDAY:
├─ Saturday 8:00 AM
│  └─ Weekend capacity set
│     ├─ Min: 3
│     ├─ Max: 10

DYNAMIC SCALING:
└─ Within bounds, CPU/memory/request scaling
   ├─ If CPU hits 80% → Scale up 1-3 tasks (step scaling)
   ├─ If CPU < 30% → Scale down after 5 min cooldown
   └─ Combined strategy for best results
```

### Monitoring Commands

```bash
# Check current configuration
make asg-info

# Expected output:
# Auto-Scaling Information
# ========================
# Min Capacity: 2
# Max Capacity: 12
# Target CPU: 70%
# Policies Active: CPU, Memory, ALB Request Count
# Scheduled Actions: Peak, Off-Peak, Weekend

# Monitor during peak hours
make asg-metrics

# Expected: 
# Task Count: 6-8 (increased from 2)
# CPU Util: ~65-75%
# Memory Util: ~70-75%
# Request/task: ~1000-1200
```

### Expected Behavior

```
Scenario: Friday 8 AM (peak starts)
Time    Tasks   CPU    Memory   Status
----    -----   ---    ------   ------
7:50 AM   2     25%    45%      Off-peak minimum
8:00 AM   4     35%    50%      Scheduled scale-up
8:05 AM   5     55%    60%      Dynamic scaling (traffic arriving)
8:10 AM   6     68%    72%      Approaching target
8:15 AM   6     70%    73%      Stable at target
8:30 AM   6     72%    74%      Maintaining load
9:00 AM   7     78%    75%      Step scaling triggered (80% alarm)
9:05 AM   8     65%    70%      Load distributed, CPU normalized
10:00 AM  8     64%    69%      Stable


Scenario: Friday 6 PM (peak ends)
Time     Tasks  CPU    Memory   Status
----     -----  ---    ------   ------
5:55 PM    8    62%    71%      Still busy
6:00 PM    8    62%    71%      Scheduled scale-down initiated
6:05 PM    7    58%    67%      Step 1 of scale-down
6:15 PM    6    52%    64%      Further reduction
6:30 PM    5    48%    60%      Approaching off-peak
7:00 PM    4    42%    55%      Off-peak minimum reached
```

### Cost Impact

```
DAILY COSTS (2 x t3.small tasks, $0.026/hour):

Peak hours (8 AM - 6 PM, 10 hours):
├─ Average: 6.5 tasks
├─ Cost: 6.5 × $0.026 × 10 = $1.69/day

Off-peak hours (6 PM - 8 AM, 14 hours):
├─ Average: 3 tasks
├─ Cost: 3 × $0.026 × 14 = $1.09/day

Daily total: $2.78
Monthly: ~$83 for compute

vs. Always-on 6 tasks:
├─ Cost: 6 × $0.026 × 24 × 30 = $112/month
└─ Savings with auto-scaling: $29/month (26% reduction)
```

---

## Example 2: Microservice Scaling by Component

### Scenario

You have separate services for:
- **Bookings Service:** High request volume, variable CPU
- **Payments Service:** Strict uptime, steady traffic
- **Analytics Service:** Batch processing, spiky CPU

### Configuration Strategy

```hcl
# Create separate auto-scaling policies per service

# SERVICE 1: Bookings (variable traffic, scale aggressively)
enable_ecs_autoscaling = true
ecs_min_capacity = 2          # Always available
ecs_max_capacity = 20         # Aggressive ceiling
ecs_target_cpu_percentage = 75 # Higher threshold (can handle more)
ecs_scale_out_cooldown = 30   # React quickly to spikes
ecs_scale_in_cooldown = 600   # Conservative scale-down


# SERVICE 2: Payments (strict requirements, conservative scaling)
enable_ecs_autoscaling = true
ecs_min_capacity = 3          # Always high capacity
ecs_max_capacity = 10         # Limited scaling
ecs_target_cpu_percentage = 60 # Lower threshold (safety margin)
ecs_scale_out_cooldown = 30
ecs_scale_in_cooldown = 1200  # Very conservative (20 minutes)


# SERVICE 3: Analytics (batch, spiky)
enable_ecs_autoscaling = true
ecs_min_capacity = 1          # Can start small
ecs_max_capacity = 30         # Extreme spike tolerance
ecs_target_cpu_percentage = 85 # Can run hot
enable_step_scaling = true
ecs_cpu_alarm_threshold = 75  # Alert earlier
ecs_step_scaling_cooldown = 30 # Quick response to spikes
```

### Terraform Configuration

```hcl
# Create multiple ASG targets (one per service)

resource "aws_appautoscaling_target" "bookings_service" {
  max_capacity       = 20
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/bookings-service"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_target" "payments_service" {
  max_capacity       = 10
  min_capacity       = 3
  resource_id        = "service/${aws_ecs_cluster.main.name}/payments-service"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_target" "analytics_service" {
  max_capacity       = 30
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/analytics-service"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}
```

### Monitoring Strategy

```bash
# Monitor each service independently
aws application-autoscaling describe-scalable-targets \
  --service-namespace ecs \
  --query 'ScalableTargets[*].[ResourceId,MinCapacity,MaxCapacity]'

# Expected output:
# service/main-cluster/bookings-service      2   20
# service/main-cluster/payments-service      3   10
# service/main-cluster/analytics-service     1   30

# Monitor resource consumption per service
for service in bookings payments analytics; do
  echo "=== $service-service ==="
  aws cloudwatch get-metric-statistics \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --dimensions Name=ServiceName,Value=$service-service \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)Z \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S)Z \
    --period 300 \
    --statistics Average
done
```

### Cost Optimization

```
MONTHLY COSTS (t3.small tasks, $0.026/hour):

Bookings (variable traffic):
├─ Average: 8 tasks
├─ Cost: 8 × $0.026 × 730 hours = $151.84

Payments (steady state):
├─ Average: 4 tasks
├─ Cost: 4 × $0.026 × 730 hours = $75.92

Analytics (spiky):
├─ Average: 4 tasks (often scales to 12+ during runs)
├─ Cost: 4 × $0.026 × 730 hours = $75.92

Total: ~$304/month
```

---

## Example 3: Festival/Special Event Scaling

### Scenario

Your hotel management system handles a major festival:
- **Normal week:** 100 bookings/day
- **Festival week:** 500 bookings/day (5x increase)
- **Need massive scaling for 7-day period**

### Pre-Event Preparation

```bash
# 1 week before event
terraform apply -var="enable_ecs_autoscaling=false"
# → Disables auto-scaling temporarily

# 3 days before
terraform apply \
  -var="enable_ecs_autoscaling=true" \
  -var="ecs_min_capacity=10" \
  -var="ecs_max_capacity=30" \
  -var="enable_scheduled_scaling=false"
# → Sets up heavy capacity

# 1 day before: Test with simulated load
make asg-test-scaling
```

### Event Schedule Configuration

```hcl
# terraform/environments/prod-event.tfvars

# FESTIVAL PERIOD: July 10-16, 2024

# For the 7-day period, use elevated capacity
enable_ecs_autoscaling = true
ecs_min_capacity = 10        # Keep 10 always running
ecs_max_capacity = 50        # Allow scaling to 50 (extreme)

# CPU target lower to ensure responsibility
ecs_target_cpu_percentage = 60

# Aggressive scaling for demand spikes
enable_step_scaling = true
ecs_cpu_alarm_threshold = 70 # Alert at lower threshold

# No scheduled scaling (continuous high load)
enable_scheduled_scaling = false

# Cooldown periods shorter (respond to spikes)
ecs_scale_out_cooldown = 30  # Quick scale-up
ecs_scale_in_cooldown = 900  # Very conservative scale-down (15 min)
```

### Monitoring During Event

```bash
# Real-time monitoring (check every 15 minutes)
watch -n 900 'make asg-metrics'

# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name festival-scaling \
  --dashboard-body file://festival-dashboard.json

# Alert configuration
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:123456789:scaling-alerts \
  --message "Festival scaling active: Current task count = 25"
```

### Post-Event Cleanup

```bash
# After festival ends (July 17)

# Step 1: Verify festival surge is over
make asg-metrics

# Step 2: Gradually reduce capacity
terraform apply \
  -var="ecs_min_capacity=5" \
  -var="ecs_max_capacity=25"
# → Monitor for 2-3 hours

# Step 3: Return to normal
terraform apply \
  -var="ecs_min_capacity=2" \
  -var="ecs_max_capacity=12" \
  -var="enable_scheduled_scaling=true"

# Step 4: Analyze metrics
aws cloudwatch get-metric-statistics \
  --metric-name TaskCount \
  --namespace AWS/ECS \
  --start-time 2024-07-10T00:00:00Z \
  --end-time 2024-07-17T00:00:00Z \
  --period 43200 \
  --statistics Average,Maximum
```

---

## Example 4: Gradual Traffic Migration

### Scenario

You're migrating users from old system to new system (Lift & Shift).

**Phase 1 (Week 1):** 10% traffic on new system  
**Phase 2 (Week 2):** 25% traffic on new system  
**Phase 3 (Week 3):** 50% traffic on new system  
**Phase 4 (Week 4):** 100% traffic on new system

### Auto-Scaling Strategy

```
PHASE 1: 10% traffic
├─ New system: min=1, max=2 (minimal load)
├─ Old system: min=5, max=10 (90% of traffic)
└─ Parallel monitoring for issues

PHASE 2: 25% traffic
├─ New system: min=2, max=5 (25% load)
├─ Old system: min=4, max=8 (75% of traffic)
└─ Monitor for bottlenecks

PHASE 3: 50% traffic
├─ New system: min=4, max=10 (50% load)
├─ Old system: min=3, max=6 (50% of traffic)
└─ Both systems at equal load

PHASE 4: 100% traffic migration
├─ New system: min=2, max=12 (100% load)
├─ Old system: min=1, max=2 (emergency backup only)
└─ Full production cutover
```

### Configuration Example (Phase 2)

```hcl
# NEW SYSTEM (Nephele HMS v2.0)
# terraform/environments/prod-nephele-v2.tfvars

enable_ecs_autoscaling = true
ecs_min_capacity = 2          # At least 2 for HA
ecs_max_capacity = 5          # Limited to 25% of total capacity

enable_cpu_scaling = true
ecs_target_cpu_percentage = 70

# Careful monitoring thresholds
enable_step_scaling = true
ecs_cpu_alarm_threshold = 75

# No scheduled scaling during migration
enable_scheduled_scaling = false


# OLD SYSTEM (Current system)
# terraform/environments/prod-nephele-v1.tfvars

enable_ecs_autoscaling = true
ecs_min_capacity = 4          # Carry 75% of load
ecs_max_capacity = 8

enable_cpu_scaling = true
ecs_target_cpu_percentage = 72  # Monitor closely for stability
```

### Rollback Plan

If Phase 2 shows issues:

```bash
# Rollback: Return to Phase 1
terraform apply \
  -var="new_system_min_capacity=1" \
  -var="new_system_max_capacity=2" \
  -var="old_system_min_capacity=5" \
  -var="old_system_max_capacity=10"

# Investigate issue
make asg-metrics
aws logs tail /ecs/nephele-v2 --follow

# Fix and re-attempt Phase 2
# Wait 2-3 hours before retry
```

---

## Example 5: Memory-Intensive Operations

### Scenario

Your Django application includes:
- **Typical requests:** 256 MB RAM per task
- **Report generation:** 512 MB per task
- **Batch processing:** 1 GB per task

### Configuration

```hcl
# Monitor memory closely
enable_memory_scaling = true
ecs_target_memory_percentage = 75

# Large task definition (for memory-intensive work)
ecs_task_cpu = 512           # More CPU
ecs_task_memory = 1024       # 1 GB per task

# Aggressive memory scaling
step_adjustment {
  metric_interval_lower_bound = 15  # Above 75% + 15%
  metric_interval_upper_bound = 25
  adjustment = 2  # Add 2 tasks for memory issues
}
```

### Memory Monitoring

```bash
# Track memory utilization
aws cloudwatch get-metric-statistics \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S)Z \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S)Z \
  --period 300 \
  --statistics Average,Maximum

# Look for patterns:
# - Report generation causes spikes?
# - Memory leaks (steadily increasing)?
# - Batch jobs clearing memory?
```

### Optimization Steps

```
1. Profile application memory usage
   - Identify memory-hungry endpoints
   - Check for leaks in background tasks

2. Adjust task size based on findings
   - Too large: Wasting money on extra memory
   - Too small: Frequent scaling, poor performance

3. Optimize code
   - Cache inefficiencies
   - Close database connections properly
   - Use context managers for resource cleanup

4. Consider separate services
   - Memory-intensive reports in isolated service
   - Allows separate scaling strategy
```

---

## Example 6: Scaling with Cost Constraints

### Scenario

You have a $200/month budget for compute and must scale within it.

**Requirement:** Scale from 2 to 8 tasks, max $200/month

### Cost Analysis

```
Task size: t3.small ($0.026/hour)

SCENARIO 1: Fixed 8 tasks
├─ Cost: 8 × $0.026 × 730 = $151.84
├─ Budget remaining: $48.16
└─ Good for peak but expensive all day

SCENARIO 2: Auto-scaling 2-8
├─ Average: 4 tasks (estimated based on traffic)
├─ Cost: 4 × $0.026 × 730 = $75.92
├─ Budget remaining: $124.08
└─ Much better, allows for spikes

SCENARIO 3: Scheduled + auto-scaling
├─ Peak hours: 6 threads
├─ Off-peak hours: 2 throttle
├─ Average: 35 hours × 6 + 65 hours × 2 = 340 task-hours/day
├─ Cost: 340 × $0.026 / 24 = $0.37/day = $11.10/month
└─ BEST OPTION: $11.10/month (leaves $188.90 for other services!)
```

### Recommended Configuration

```hcl
enable_ecs_autoscaling = true
ecs_min_capacity = 2          # Minimum within budget
ecs_max_capacity = 8          # Tight ceiling

enable_scheduled_scaling = true

# Peak hours: 2-6 tasks
ecs_peak_min_capacity = 2
ecs_peak_max_capacity = 6

# Off-peak: Minimal
ecs_offpeak_min_capacity = 2
ecs_offpeak_max_capacity = 4

# Weekend: Reduce slightly
ecs_weekend_min_capacity = 2
ecs_weekend_max_capacity = 5

# Conservative thresholds (scale only when necessary)
ecs_target_cpu_percentage = 80     # Allow higher load
enable_memory_scaling = false       # Skip for cost
enable_alb_request_scaling = false  # Skip for cost
```

### Monitoring Budget

```bash
# Monthly cost estimate
aws ce get-cost-and-usage \
  --time-period Start=2024-02-01,End=2024-02-29 \
  --granularity MONTHLY \
  --metrics BlendedCost

# Example output:
# ECS Tasks: $75.92
# Data Transfer: $5.00
# CloudWatch: $2.00
# Total: $82.92 (well under budget!)
```

---

## Example 7: Cross-Region Failover Scaling

### Scenario

You have:
- **Primary Region (us-east-1):** Main system, normal scaling
- **DR Region (us-west-2):** Minimal capacity, ready to scale up if needed

### Configuration

```hcl
# PRIMARY REGION: us-east-1
# terraform/environments/prod-us-east.tfvars

enable_ecs_autoscaling = true
ecs_min_capacity = 2
ecs_max_capacity = 12
enable_scheduled_scaling = true
# ... normal configuration


# DR REGION: us-west-2
# terraform/environments/prod-us-west-dr.tfvars

enable_ecs_autoscaling = true
ecs_min_capacity = 1          # Minimal (no one using it)
ecs_max_capacity = 15         # But can scale aggressively if needed
enable_cpu_scaling = true
ecs_target_cpu_percentage = 60 # Lower threshold (safety)
enable_scheduled_scaling = false  # Always minimal, never scheduled

# CRITICAL: Disable scale-down in DR
ecs_scale_in_cooldown = 7200    # Don't scale down accidentally (2 hours)
```

### Failover Procedure

```bash
# FAILOVER TRIGGERED (Primary region down)

# Step 1: Update Route53 to point to DR
aws route53 change-resource-record-sets \
  --hosted-zone-id Z... \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.yourdomain.com",
        "Type": "CNAME",
        "TTL": 60,
        "ResourceRecords": [{"Value": "dr-alb.region.elb.amazonaws.com"}]
      }
    }]
  }'

# Step 2: Manually scale DR region (auto-scaling might be too slow)
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id "service/dr-cluster/app-service" \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 5 \
  --max-capacity 15

# Alternative: Update via Terraform in DR region
terraform apply -var="ecs_min_capacity=5"

# Step 3: Monitor DR scaling
watch -n 30 'aws cloudwatch get-metric-statistics \
  --metric-name DesiredTaskCount \
  --namespace ECS/ContainerInsights \
  --region us-west-2'

# Step 4: Once primary region recovered
# Route53 automatically/manually routes back
# DR region scales back down when traffic gone
```

---

## Summary of All Examples

| Example | Scenario | Min Tasks | Max Tasks | Policies | Best For |
|---------|----------|-----------|-----------|----------|----------|
| #1 | Hotel Peak/Off-Peak | 2 | 12 | Target+Scheduled | Predictable patterns |
| #2 | Multi-Service | 1-3 | 10-30 | Multiple targets | Microservices |
| #3 | Festival/Event | 10 | 50 | Manual override | Special events |
| #4 | Traffic Migration | 1-4 | 2-12 | Phase-based | Gradual rollout |
| #5 | Memory-Intensive | 1 | 8 | Memory focus | Processing tasks |
| #6 | Budget Constrained | 2 | 8 | Scheduled only | Limited budget |
| #7 | DR Failover | 1-5 | 15 | Conservative | Disaster recovery |

---

## Testing Your Configuration

```bash
# Load test to trigger auto-scaling
make asg-test-scaling

# Or use Apache Bench
ab -n 10000 -c 100 https://yourdomain/api/health/

# Monitor scaling activity
watch -n 5 'make asg-metrics'

# Expected behavior:
# 1. Task count increases
# 2. CPU stays near target (70%)
# 3. Under sustained load, reaches max capacity
```

---

## Troubleshooting Examples

**Tasks don't scale up:**  
→ Check health checks are passing  
→ Verify IAM permissions  
→ Increase target CPU percentage  

**Tasks scale down too fast:**  
→ Increase scale-in cooldown  
→ Increase minimum capacity  

**Costs higher than expected:**  
→ Use scheduled scaling more aggressively  
→ Lower maximum capacity  
→ Optimize task size  

---

Each example is ready to deploy. Choose the one that matches your use case and customize as needed!

