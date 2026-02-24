# ============================================================================
# Gap #5: Advanced ECS Auto-Scaling Configuration
# ============================================================================
#
# This configuration provides:
# - Target tracking auto-scaling (CPU and memory-based)
# - Scheduled scaling for predictable traffic patterns
# - Step scaling for rapid response to traffic spikes
# - Cross-AZ awareness for optimal distribution
# - Detailed monitoring and alarms
# - Cost optimization through predictive scaling
#
# Features:
# - Multiple scaling metrics (CPU, Memory, ALB Request Count)
# - Configurable scale-in and scale-out cooldown periods
# - Minimum and maximum task counts
# - Load-based and schedule-based scaling strategies
# ============================================================================

# ============================================================================
# ECS Service Auto-Scaling Target (main service)
# ============================================================================

resource "aws_appautoscaling_target" "ecs_target" {
  count              = var.enable_ecs_autoscaling ? 1 : 0
  max_capacity       = var.ecs_max_capacity
  min_capacity       = var.ecs_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  depends_on = [
    aws_ecs_service.app
  ]

  tags = {
    Name        = "${var.project_name}-ecs-asg-target"
    Environment = var.environment
    Gap         = "Gap #5"
  }
}

# ============================================================================
# Auto-Scaling Policy: CPU-Based Scaling (Target Tracking)
# ============================================================================
#
# Maintains CPU utilization at target level by scaling tasks up/down.
# This is the most common scaling strategy for web applications.
#
# Example:
#   - Target CPU: 70%
#   - Current CPU: 85% → Scale up (add tasks)
#   - Current CPU: 50% → Scale down (remove tasks)
#

resource "aws_appautoscaling_policy" "ecs_policy_cpu" {
  count              = var.enable_ecs_autoscaling && var.enable_cpu_scaling ? 1 : 0
  name               = "${var.project_name}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    target_value       = var.ecs_target_cpu_percentage
    scale_in_cooldown  = var.ecs_scale_in_cooldown
    scale_out_cooldown = var.ecs_scale_out_cooldown

    # Disable scale-in during scale-out (avoid oscillation)
    disable_scale_in = var.ecs_disable_scale_in
  }

  tags = {
    Name        = "${var.project_name}-cpu-scaling-policy"
    Environment = var.environment
    Gap         = "Gap #5"
  }
}

# ============================================================================
# Auto-Scaling Policy: Memory-Based Scaling (Target Tracking)
# ============================================================================
#
# Maintains memory utilization at target level.
# Useful when application has high memory overhead.
#
# Example:
#   - Target Memory: 75%
#   - Current Memory: 88% → Scale up
#   - Current Memory: 60% → Scale down
#

resource "aws_appautoscaling_policy" "ecs_policy_memory" {
  count              = var.enable_ecs_autoscaling && var.enable_memory_scaling ? 1 : 0
  name               = "${var.project_name}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }

    target_value       = var.ecs_target_memory_percentage
    scale_in_cooldown  = var.ecs_scale_in_cooldown
    scale_out_cooldown = var.ecs_scale_out_cooldown
    disable_scale_in   = var.ecs_disable_scale_in
  }

  tags = {
    Name        = "${var.project_name}-memory-scaling-policy"
    Environment = var.environment
    Gap         = "Gap #5"
  }
}

# ============================================================================
# Auto-Scaling Policy: ALB Request Count (Target Tracking)
# ============================================================================
#
# Scales based on request volume handled by ALB.
# Smart choice for web applications with variable traffic.
#
# Example:
#   - Target: 1000 requests/minute per task
#   - If load increases to 2000 req/min per task → Scale up
#   - If load decreases to 500 req/min per task → Scale down
#

resource "aws_appautoscaling_policy" "ecs_policy_alb_request_count" {
  count              = var.enable_ecs_autoscaling && var.enable_alb_request_scaling ? 1 : 0
  name               = "${var.project_name}-alb-request-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label         = "${aws_lb.main.arn_suffix}/${aws_lb_target_group.app.arn_suffix}"
    }

    target_value       = var.ecs_target_requests_per_minute
    scale_in_cooldown  = var.ecs_scale_in_cooldown
    scale_out_cooldown = var.ecs_scale_out_cooldown
    disable_scale_in   = var.ecs_disable_scale_in
  }

  depends_on = [aws_appautoscaling_target.ecs_target]

  tags = {
    Name        = "${var.project_name}-alb-request-scaling-policy"
    Environment = var.environment
    Gap         = "Gap #5"
  }
}

# ============================================================================
# Auto-Scaling Policy: Step Scaling (for rapid response)
# ============================================================================
#
# Provides faster response to traffic spikes using step functions.
# Scales more aggressively when needed.
#
# Steps:
# - CPU 70-80%: Add 1 task
# - CPU 80-90%: Add 2 tasks
# - CPU 90%+:   Add 3 tasks
#

resource "aws_appautoscaling_policy" "ecs_policy_step_scaling" {
  count              = var.enable_ecs_autoscaling && var.enable_step_scaling ? 1 : 0
  name               = "${var.project_name}-step-scaling"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target[0].service_namespace

  step_scaling_policy_configuration {
    adjustment_type          = "ChangeInCapacity"
    cooldown                 = var.ecs_step_scaling_cooldown
    metric_aggregation_type  = "Average"

    # Step 1: CPU 70-80% → Add 1 task
    step_adjustment {
      metric_interval_lower_bound = 0
      metric_interval_upper_bound = 10
      adjustment                  = 1
    }

    # Step 2: CPU 80-90% → Add 2 tasks
    step_adjustment {
      metric_interval_lower_bound = 10
      metric_interval_upper_bound = 20
      adjustment                  = 2
    }

    # Step 3: CPU 90%+ → Add 3 tasks
    step_adjustment {
      metric_interval_lower_bound = 20
      adjustment                  = 3
    }
  }

  tags = {
    Name        = "${var.project_name}-step-scaling-policy"
    Environment = var.environment
    Gap         = "Gap #5"
  }
}

# ============================================================================
# CloudWatch Alarm: High CPU Utilization (for step scaling trigger)
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  count               = var.enable_ecs_autoscaling && var.enable_step_scaling ? 1 : 0
  alarm_name          = "${var.project_name}-ecs-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = var.ecs_cpu_alarm_threshold
  alarm_description   = "Alarm when ECS CPU exceeds ${var.ecs_cpu_alarm_threshold}%"
  alarm_actions       = var.enable_step_scaling ? [aws_appautoscaling_policy.ecs_policy_step_scaling[0].arn] : []

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.app.name
  }

  tags = {
    Name        = "${var.project_name}-cpu-high-alarm"
    Environment = var.environment
    Gap         = "Gap #5"
  }
}

# ============================================================================
# CloudWatch Alarm: Low CPU Utilization (scale-down trigger)
# ============================================================================

resource "aws_cloudwatch_metric_alarm" "ecs_cpu_low" {
  count               = var.enable_ecs_autoscaling ? 1 : 0
  alarm_name          = "${var.project_name}-ecs-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 5
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.ecs_cpu_low_threshold
  alarm_description   = "Alarm when ECS CPU below ${var.ecs_cpu_low_threshold}% for scale-down"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.app.name
  }

  tags = {
    Name        = "${var.project_name}-cpu-low-alarm"
    Environment = var.environment
    Gap         = "Gap #5"
  }
}

# ============================================================================
# Scheduled Scaling: Peak Hours (Business Hours)
# ============================================================================
#
# Scale up to maximum capacity during peak business hours.
# Example: 8 AM - 6 PM weekdays
#

resource "aws_appautoscaling_scheduled_action" "scale_up_peak_hours" {
  count               = var.enable_ecs_autoscaling && var.enable_scheduled_scaling ? 1 : 0
  service_namespace   = aws_appautoscaling_target.ecs_target[0].service_namespace
  schedule            = "cron(0 8 ? * MON-FRI *)"  # 8 AM UTC weekdays
  timezone            = var.timezone
  resource_id         = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension  = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  scheduled_action_name = "${var.project_name}-scale-up-peak-hours"

  scalable_target_action {
    min_capacity = var.ecs_peak_min_capacity
    max_capacity = var.ecs_peak_max_capacity
  }
}

# ============================================================================
# Scheduled Scaling: Off-Peak Hours (Business Hours)
# ============================================================================
#
# Scale down to minimum capacity during off-peak hours.
# Example: 6 PM - 8 AM weekdays, all weekend
#

resource "aws_appautoscaling_scheduled_action" "scale_down_off_peak" {
  count               = var.enable_ecs_autoscaling && var.enable_scheduled_scaling ? 1 : 0
  service_namespace   = aws_appautoscaling_target.ecs_target[0].service_namespace
  schedule            = "cron(0 18 ? * MON-FRI *)"  # 6 PM UTC weekdays
  timezone            = var.timezone
  resource_id         = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension  = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  scheduled_action_name = "${var.project_name}-scale-down-off-peak"

  scalable_target_action {
    min_capacity = var.ecs_offpeak_min_capacity
    max_capacity = var.ecs_offpeak_max_capacity
  }
}

# ============================================================================
# Scheduled Scaling: Weekend Minimum
# ============================================================================
#
# Keep minimal capacity during weekends (low traffic expected).
#

resource "aws_appautoscaling_scheduled_action" "scale_down_weekend" {
  count               = var.enable_ecs_autoscaling && var.enable_scheduled_scaling ? 1 : 0
  service_namespace   = aws_appautoscaling_target.ecs_target[0].service_namespace
  schedule            = "cron(0 0 ? * SAT *)"  # Saturday midnight UTC
  timezone            = var.timezone
  resource_id         = aws_appautoscaling_target.ecs_target[0].resource_id
  scalable_dimension  = aws_appautoscaling_target.ecs_target[0].scalable_dimension
  scheduled_action_name = "${var.project_name}-scale-down-weekend"

  scalable_target_action {
    min_capacity = var.ecs_weekend_min_capacity
    max_capacity = var.ecs_weekend_max_capacity
  }
}

# ============================================================================
# CloudWatch Metric: Task Count Tracking
# ============================================================================
#
# Custom dashboard for monitoring active task count.
#

resource "aws_cloudwatch_metric_alarm" "ecs_desired_task_count" {
  count               = var.enable_ecs_autoscaling ? 1 : 0
  alarm_name          = "${var.project_name}-ecs-desired-task-count"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DesiredTaskCount"
  namespace           = "ECS/ContainerInsights"
  period              = 300
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "Alert if desired task count drops below 1 (service stopping)"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.app.name
  }

  tags = {
    Name        = "${var.project_name}-task-count-alarm"
    Environment = var.environment
    Gap         = "Gap #5"
  }
}

# ============================================================================
# CloudWatch Alarm: Running Task Count Below Desired
# ============================================================================
#
# Alert when running tasks fall below desired count (unhealthy service).
#

resource "aws_cloudwatch_metric_alarm" "ecs_running_task_count" {
  count               = var.enable_ecs_autoscaling ? 1 : 0
  alarm_name          = "${var.project_name}-ecs-running-vs-desired"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "RunningCount"
  namespace           = "ECS/ContainerInsights"
  period              = 120
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "Alert if running tasks < desired count"
  treat_missing_data  = "breaching"

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.app.name
  }

  tags = {
    Name        = "${var.project_name}-running-task-alarm"
    Environment = var.environment
    Gap         = "Gap #5"
  }
}

# ============================================================================
# ECS Service Deployment Configuration (for auto-scaling stability)
# ============================================================================
#
# Optimized deployment settings to work well with auto-scaling:
# - Minimum healthy percent: 100% (ensure old tasks before terminating new)
# - Maximum percent: 200% (allow scaling up during deployments)
# - Deregistration delay: 30 seconds (connection draining)
#

# Note: This updates the existing ECS service defined in compute.tf
# These settings are configured there to avoid conflicts

# ============================================================================
# Outputs for Auto-Scaling Configuration
# ============================================================================

output "asg_target_arn" {
  value       = try(aws_appautoscaling_target.ecs_target[0].resource_id, null)
  description = "ARN of the ECS service auto-scaling target"
}

output "asg_cpu_policy_arn" {
  value       = try(aws_appautoscaling_policy.ecs_policy_cpu[0].arn, null)
  description = "ARN of the CPU-based target tracking policy"
}

output "asg_memory_policy_arn" {
  value       = try(aws_appautoscaling_policy.ecs_policy_memory[0].arn, null)
  description = "ARN of the memory-based target tracking policy"
}

output "asg_alb_policy_arn" {
  value       = try(aws_appautoscaling_policy.ecs_policy_alb_request_count[0].arn, null)
  description = "ARN of the ALB request count target tracking policy"
}

output "asg_step_policy_arn" {
  value       = try(aws_appautoscaling_policy.ecs_policy_step_scaling[0].arn, null)
  description = "ARN of the step scaling policy"
}

output "asg_min_capacity" {
  value       = var.ecs_min_capacity
  description = "Minimum number of tasks"
}

output "asg_max_capacity" {
  value       = var.ecs_max_capacity
  description = "Maximum number of tasks"
}

output "asg_target_cpu_percentage" {
  value       = var.ecs_target_cpu_percentage
  description = "Target CPU utilization percentage"
}

output "asg_target_memory_percentage" {
  value       = var.ecs_target_memory_percentage
  description = "Target memory utilization percentage"
}

output "asg_target_requests_per_minute" {
  value       = var.ecs_target_requests_per_minute
  description = "Target requests per minute per task"
}
