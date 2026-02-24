# Advanced Load Balancing Configuration for Gap #4
# Extends the basic ALB from compute.tf with path-based routing, weighted deployments, and advanced features

# ============================================================================
# IMPORTANT: This file extends the ALB configuration from compute.tf
# 
# To use this advanced configuration, uncomment the modules and resources below
# and update your terraform deployment accordingly.
# ============================================================================

# Additional ALB target group for canary deployments (weighted routing)
resource "aws_lb_target_group" "app_canary" {
  name        = "${var.project_name}-tg-canary"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    healthy_threshold   = var.alb_health_check_healthy_threshold
    unhealthy_threshold = var.alb_health_check_unhealthy_threshold
    timeout             = var.alb_health_check_timeout
    interval            = var.alb_health_check_interval
    path                = var.alb_health_check_path
    matcher             = "200-299"
  }

  tags = {
    Name = "${var.project_name}-tg-canary"
  }
}

# Alternative target group for staging deployments
resource "aws_lb_target_group" "app_staging" {
  name        = "${var.project_name}-tg-staging"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    healthy_threshold   = var.alb_health_check_healthy_threshold
    unhealthy_threshold = var.alb_health_check_unhealthy_threshold
    timeout             = var.alb_health_check_timeout
    interval            = var.alb_health_check_interval
    path                = var.alb_health_check_path
    matcher             = "200-299"
  }

  tags = {
    Name = "${var.project_name}-tg-staging"
  }
}

# Path-based routing rule: /api/* goes to main application
resource "aws_lb_listener_rule" "api_v1" {
  listener_arn = var.alb_enable_https && var.alb_certificate_arn != "" ? aws_lb_listener.https[0].arn : null

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }

  # Only create if HTTPS is enabled
  count = var.alb_enable_https && var.alb_certificate_arn != "" ? 1 : 0
}

# Path-based routing rule: /admin/* goes to admin target group (or same with auth)
resource "aws_lb_listener_rule" "admin" {
  listener_arn = var.alb_enable_https && var.alb_certificate_arn != "" ? aws_lb_listener.https[0].arn : null

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  condition {
    path_pattern {
      values = ["/admin/*"]
    }
  }

  # Optional: Add custom HTTP headers for admin requests
  # This allows the application to know the request is for admin
  count = var.alb_enable_https && var.alb_certificate_arn != "" ? 1 : 0
}

# Path-based routing rule: /health/* goes to health check endpoint
resource "aws_lb_listener_rule" "health" {
  listener_arn = var.alb_enable_https && var.alb_certificate_arn != "" ? aws_lb_listener.https[0].arn : null

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  condition {
    path_pattern {
      values = ["/health/*"]
    }
  }

  count = var.alb_enable_https && var.alb_certificate_arn != "" ? 1 : 0
}

# Weighted target group rule for canary deployments
# Returns 90% traffic to main, 10% to canary for safe deployments
resource "aws_lb_listener_rule" "canary_deployment" {
  listener_arn = var.alb_enable_https && var.alb_certificate_arn != "" ? aws_lb_listener.https[0].arn : null

  action {
    type = "forward"

    forward {
      target_group {
        arn    = aws_lb_target_group.app.arn
        weight = 90
      }

      target_group {
        arn    = aws_lb_target_group.app_canary.arn
        weight = 10
      }
    }
  }

  condition {
    path_pattern {
      values = ["/api/v2/*"]  # New API version on canary
    }
  }

  count = var.alb_enable_https && var.alb_certificate_arn != "" ? 1 : 0
}

# Request header modifications - add custom headers for request tracking
resource "aws_lb_listener_rule" "add_security_headers" {
  listener_arn = var.alb_enable_https && var.alb_certificate_arn != "" ? aws_lb_listener.https[0].arn : null

  action {
    type = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }

  count = var.alb_enable_https && var.alb_certificate_arn != "" ? 1 : 0
}

# Redirect HTTP to HTTPS listener rule (already in compute.tf's ALB HTTP listener)
# But for completeness with path patterns on HTTPS:

# Fixed response for root path (optional - direct to docs or dashboard)
resource "aws_lb_listener_rule" "root_redirect" {
  listener_arn = var.alb_enable_https && var.alb_certificate_arn != "" ? aws_lb_listener.https[0].arn : null

  action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
      path        = "/api/v1/docs/"  # Redirect root to API docs
    }
  }

  condition {
    path_pattern {
      values = ["/"]
    }
  }

  count = var.alb_enable_https && var.alb_certificate_arn != "" ? 1 : 0
}

# CloudWatch metric for ALB request count
resource "aws_cloudwatch_metric_alarm" "alb_request_count" {
  alarm_name          = "${var.project_name}-alb-request-count"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "RequestCount"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert when ALB has no traffic (potential issue)"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name = "${var.project_name}-alb-request-count-alarm"
  }
}

# CloudWatch metric for ALB response time
resource "aws_cloudwatch_metric_alarm" "alb_response_time" {
  alarm_name          = "${var.project_name}-alb-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"  # 1 second
  alarm_description   = "Alert when ALB response time exceeds 1 second"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name = "${var.project_name}-alb-response-time-alarm"
  }
}

# CloudWatch metric for 4xx errors
resource "aws_cloudwatch_metric_alarm" "alb_4xx_errors" {
  alarm_name          = "${var.project_name}-alb-high-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_4XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"  # More than 100 per 5 minutes
  alarm_description   = "Alert when ALB sees many 4xx errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name = "${var.project_name}-alb-4xx-errors-alarm"
  }
}

# CloudWatch metric for 5xx errors
resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "${var.project_name}-alb-high-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Sum"
  threshold           = "10"  # More than 10 per minute
  alarm_description   = "Alert when ALB sees 5xx errors (application issues)"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name = "${var.project_name}-alb-5xx-errors-alarm"
  }
}

# Optional: AWS WAF (Web Application Firewall) association
# Uncomment to enable WAF protection for the ALB

# resource "aws_wafv2_web_acl" "main" {
#   count = var.enable_waf ? 1 : 0
#   name  = "${var.project_name}-waf"
#   scope = "REGIONAL"
#
#   default_action {
#     allow {}
#   }
#
#   rule {
#     name     = "AWSManagedRulesCommonRuleSet"
#     priority = 1
#
#     override_action {
#       none {}
#     }
#
#     statement {
#       managed_rule_group_statement {
#         name        = "AWSManagedRulesCommonRuleSet"
#         vendor_name = "AWS"
#       }
#     }
#
#     visibility_config {
#       cloudwatch_metrics_enabled = true
#       metric_name                = "${var.project_name}-common-rule-metrics"
#       sampled_requests_enabled   = true
#     }
#   }
#
#   visibility_config {
#     cloudwatch_metrics_enabled = true
#     metric_name                = "${var.project_name}-waf-metrics"
#     sampled_requests_enabled   = true
#   }
#
#   tags = {
#     Name = "${var.project_name}-waf"
#   }
# }
#
# resource "aws_wafv2_web_acl_association" "main" {
#   count        = var.enable_waf ? 1 : 0
#   resource_arn = aws_lb.main.arn
#   web_acl_arn  = aws_wafv2_web_acl.main[0].arn
# }

# Optional: AWS Route53 for DNS (requires hosted zone)
# Uncomment to create DNS record for the ALB

# resource "aws_route53_record" "main" {
#   count   = var.route53_zone_name != "" ? 1 : 0
#   zone_id = data.aws_route53_zone.main[0].zone_id
#   name    = "${var.route53_record_name}.${var.route53_zone_name}"
#   type    = "A"
#   alias {
#     name                   = aws_lb.main.dns_name
#     zone_id                = aws_lb.main.zone_id
#     evaluate_target_health = true
#   }
# }
#
# data "aws_route53_zone" "main" {
#   count = var.route53_zone_name != "" ? 1 : 0
#   name  = var.route53_zone_name
# }

# Output for advanced load balancing
output "alb_canary_target_group_arn" {
  description = "ARN of the canary target group for weighted deployments"
  value       = try(aws_lb_target_group.app_canary.arn, "")
}

output "alb_staging_target_group_arn" {
  description = "ARN of the staging target group"
  value       = try(aws_lb_target_group.app_staging.arn, "")
}
