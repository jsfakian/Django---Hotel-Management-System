# ============================================================================
# Gap #6: Advanced Monitoring & Observability
# ============================================================================
#
# This configuration provides:
# - CloudWatch dashboards for system monitoring
# - Distributed tracing with X-Ray
# - Log aggregation and retention
# - Comprehensive alarms and alerts
# - Application Performance Monitoring (APM)
# - Health metrics and KPIs
#
# Features:
# - Multi-level dashboards (system, service, application)
# - Real-time alerting via SNS
# - Log analysis and streaming
# - Distributed request tracing
# - Custom metrics and dimensions
# ============================================================================

# ============================================================================
# CloudWatch Log Group for ECS
# ============================================================================

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.enable_log_encryption ? aws_kms_key.logs[0].arn : null

  tags = {
    Name        = "${var.project_name}-ecs-logs"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

# ============================================================================
# CloudWatch Log Group for ALB
# ============================================================================

resource "aws_cloudwatch_log_group" "alb_logs" {
  count             = var.enable_alb_access_logs ? 1 : 0
  name              = "/aws/alb/${var.project_name}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.enable_log_encryption ? aws_kms_key.logs[0].arn : null

  tags = {
    Name        = "${var.project_name}-alb-logs"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

# ============================================================================
# CloudWatch Log Group for RDS
# ============================================================================

resource "aws_cloudwatch_log_group" "rds_logs" {
  count             = var.enable_rds_logs ? 1 : 0
  name              = "/aws/rds/${var.project_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-rds-logs"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

# ============================================================================
# SNS Topic for Alerts
# ============================================================================

resource "aws_sns_topic" "alerts" {
  name              = "${var.project_name}-alerts"
  kms_master_key_id = var.enable_log_encryption ? aws_kms_key.logs[0].id : "alias/aws/sns"

  tags = {
    Name        = "${var.project_name}-alerts-topic"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ============================================================================
# CloudWatch Dashboard: System Overview
# ============================================================================

resource "aws_cloudwatch_dashboard" "system_overview" {
  count          = var.enable_monitoring_dashboards ? 1 : 0
  dashboard_name = "${var.project_name}-system-overview"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", { stat = "Sum", label = "Total Requests" }],
            ["AWS/ApplicationELB", "TargetResponseTime", { stat = "Average", label = "Avg Response Time" }],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", { stat = "Sum", label = "5XX Errors" }],
            ["AWS/ECS", "CPUUtilization", { stat = "Average", label = "Avg CPU %" }],
            ["AWS/ECS", "MemoryUtilization", { stat = "Average", label = "Avg Memory %" }],
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "System Health Overview"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["ECS/ContainerInsights", "DesiredTaskCount", { stat = "Average" }],
            ["ECS/ContainerInsights", "RunningCount", { stat = "Average" }],
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Task Count (Desired vs Running)"
        }
      },
      {
        type = "log"
        properties = {
          query   = "fields @timestamp, @message, @duration | stats count() by bin(5m)"
          region  = var.aws_region
          title   = "Request Volume by Time"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "UnHealthyHostCount", { stat = "Maximum" }],
            ["AWS/ApplicationELB", "HealthyHostCount", { stat = "Average" }],
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Target Health Status"
        }
      },
    ]
  })
}

# ============================================================================
# CloudWatch Dashboard: Application Performance
# ============================================================================

resource "aws_cloudwatch_dashboard" "application_performance" {
  count          = var.enable_monitoring_dashboards ? 1 : 0
  dashboard_name = "${var.project_name}-app-performance"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", { stat = "Average", label = "Avg" }],
            ["AWS/ApplicationELB", "TargetResponseTime", { stat = "p99", label = "p99" }],
            ["AWS/ApplicationELB", "TargetResponseTime", { stat = "p95", label = "p95" }],
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "Response Time Distribution"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", { stat = "Sum", label = "2XX Success" }],
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", { stat = "Sum", label = "4XX Client Error" }],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", { stat = "Sum", label = "5XX Server Error" }],
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Response Code Distribution"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", { stat = "Average" }],
            ["AWS/ECS", "MemoryUtilization", { stat = "Average" }],
          ]
          period = 60
          stat   = "Average"
          region = var.aws_region
          title  = "Resource Utilization"
        }
      },
      {
        type = "log"
        properties = {
          query   = "fields @duration | stats avg(@duration), max(@duration), pct(@duration, 95) by ispresent(@error)"
          region  = var.aws_region
          title   = "Request Duration Analysis"
        }
      },
    ]
  })
}

# ============================================================================
# CloudWatch Dashboard: Error Tracking
# ============================================================================

resource "aws_cloudwatch_dashboard" "error_tracking" {
  count          = var.enable_monitoring_dashboards ? 1 : 0
  dashboard_name = "${var.project_name}-error-tracking"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", { stat = "Sum" }],
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", { stat = "Sum" }],
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Error Rate Over Time"
        }
      },
      {
        type = "log"
        properties = {
          query   = "fields @message, @timestamp, @duration | filter @message like /error|exception|ERROR/ | stats count() as error_count by @message | sort error_count desc"
          region  = var.aws_region
          title   = "Top Errors by Type"
        }
      },
      {
        type = "log"
        properties = {
          query   = "fields @timestamp, @message, @duration | filter @duration > 5000 | stats count() by bin(10m)"
          region  = var.aws_region
          title   = "Slow Requests (>5s)"
        }
      },
    ]
  })
}

# ============================================================================
# CloudWatch Alarms: Critical System Health
# ============================================================================

# High 5XX Error Rate
resource "aws_cloudwatch_metric_alarm" "high_5xx_errors" {
  count               = var.enable_critical_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-high-5xx-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = var.alarm_5xx_threshold
  alarm_description   = "Alert when 5XX errors exceed ${var.alarm_5xx_threshold} in 5 minutes"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name        = "${var.project_name}-5xx-alarm"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

# High CPU Utilization
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  count               = var.enable_critical_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-high-cpu"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.alarm_cpu_threshold
  alarm_description   = "Alert when CPU exceeds ${var.alarm_cpu_threshold}%"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
  }

  tags = {
    Name        = "${var.project_name}-cpu-alarm"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

# High Memory Utilization
resource "aws_cloudwatch_metric_alarm" "high_memory" {
  count               = var.enable_critical_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-high-memory"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.alarm_memory_threshold
  alarm_description   = "Alert when memory exceeds ${var.alarm_memory_threshold}%"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
  }

  tags = {
    Name        = "${var.project_name}-memory-alarm"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

# High Response Time
resource "aws_cloudwatch_metric_alarm" "high_response_time" {
  count               = var.enable_critical_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-high-response-time"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 3
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Average"
  threshold           = var.alarm_response_time_threshold
  alarm_description   = "Alert when response time exceeds ${var.alarm_response_time_threshold} seconds"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name        = "${var.project_name}-response-time-alarm"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

# Unhealthy Targets
resource "aws_cloudwatch_metric_alarm" "unhealthy_targets" {
  count               = var.enable_critical_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-unhealthy-targets"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Maximum"
  threshold           = 1
  alarm_description   = "Alert when any target becomes unhealthy"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer   = aws_lb.main.arn_suffix
    TargetGroup    = aws_lb_target_group.app.arn_suffix
  }

  tags = {
    Name        = "${var.project_name}-unhealthy-targets-alarm"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

# ============================================================================
# CloudWatch Alarms: Database Health
# ============================================================================

# RDS CPU Utilization
resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  count               = var.enable_database_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-rds-cpu-high"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.alarm_rds_cpu_threshold
  alarm_description   = "Alert when RDS CPU exceeds ${var.alarm_rds_cpu_threshold}%"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = {
    Name        = "${var.project_name}-rds-cpu-alarm"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

# RDS Database Connections
resource "aws_cloudwatch_metric_alarm" "rds_connections_high" {
  count               = var.enable_database_alarms ? 1 : 0
  alarm_name          = "${var.project_name}-rds-connections-high"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = var.alarm_rds_connections_threshold
  alarm_description   = "Alert when database connections exceed ${var.alarm_rds_connections_threshold}"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = {
    Name        = "${var.project_name}-rds-connections-alarm"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

# ============================================================================
# X-Ray Enabled Service Map
# ============================================================================

resource "aws_xray_sampling_rule" "main" {
  count                 = var.enable_xray ? 1 : 0
  rule_name             = "${var.project_name}-sampling"
  priority              = 1000
  version               = 1
  reservoir_size        = 1
  fixed_rate            = var.xray_sample_rate
  url_path              = "*"
  host                  = "*"
  http_method           = "*"
  service_type          = "*"
  service_name          = "*"
  resource_arn          = "*"

  attributes = {
    environment = var.environment
  }
}

# ============================================================================
# KMS Key for Log Encryption
# ============================================================================

resource "aws_kms_key" "logs" {
  count                   = var.enable_log_encryption ? 1 : 0
  description             = "KMS key for CloudWatch Logs encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM Root Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-logs-key"
    Environment = var.environment
    Gap         = "Gap #6"
  }
}

resource "aws_kms_alias" "logs" {
  count         = var.enable_log_encryption ? 1 : 0
  name          = "alias/${var.project_name}-logs"
  target_key_id = aws_kms_key.logs[0].key_id
}

# ============================================================================
# Data Source for AWS Account ID
# ============================================================================

data "aws_caller_identity" "current" {}

# ============================================================================
# Outputs for Monitoring Configuration
# ============================================================================

output "sns_topic_arn" {
  value       = aws_sns_topic.alerts.arn
  description = "SNS topic ARN for alerts"
}

output "log_group_name" {
  value       = aws_cloudwatch_log_group.ecs.name
  description = "ECS CloudWatch log group name"
}

output "log_group_arn" {
  value       = aws_cloudwatch_log_group.ecs.arn
  description = "ECS CloudWatch log group ARN"
}

output "cloudwatch_dashboard_system_url" {
  value       = try(aws_cloudwatch_dashboard.system_overview[0].dashboard_name, "")
  description = "System overview dashboard name"
}

output "cloudwatch_dashboard_performance_url" {
  value       = try(aws_cloudwatch_dashboard.application_performance[0].dashboard_name, "")
  description = "Application performance dashboard name"
}

output "cloudwatch_dashboard_errors_url" {
  value       = try(aws_cloudwatch_dashboard.error_tracking[0].dashboard_name, "")
  description = "Error tracking dashboard name"
}

output "xray_enabled" {
  value       = var.enable_xray
  description = "Whether X-Ray tracing is enabled"
}

output "log_encryption_enabled" {
  value       = var.enable_log_encryption
  description = "Whether log encryption is enabled"
}
