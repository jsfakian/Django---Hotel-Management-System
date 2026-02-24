# General Configuration
variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "nephele-hms"
}

variable "application_name" {
  description = "Application name"
  type        = string
  default     = "hotel-management-system"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway"
  type        = bool
  default     = false
}

variable "availability_zones" {
  description = "Number of availability zones"
  type        = number
  default     = 2
}

# RDS Database Configuration
variable "rds_engine" {
  description = "RDS database engine"
  type        = string
  default     = "postgres"
}

variable "rds_engine_version" {
  description = "RDS engine version"
  type        = string
  default     = "15.4"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100
}

variable "rds_max_allocated_storage" {
  description = "RDS maximum allocated storage for autoscaling"
  type        = number
  default     = 200
}

variable "rds_database_name" {
  description = "RDS database name"
  type        = string
  default     = "hotel_management_system"
  sensitive   = true
}

variable "rds_database_username" {
  description = "RDS database username"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "rds_backup_retention_days" {
  description = "RDS backup retention period in days"
  type        = number
  default     = 30
}

variable "rds_multi_az" {
  description = "Enable RDS Multi-AZ deployment"
  type        = bool
  default     = false
}

variable "rds_enable_encryption" {
  description = "Enable RDS encryption at rest"
  type        = bool
  default     = true
}

# ECR Configuration
variable "ecr_image_tag_mutability" {
  description = "ECR image tag mutability"
  type        = string
  default     = "IMMUTABLE"
}

variable "ecr_scan_on_push" {
  description = "Enable ECR image scanning on push"
  type        = bool
  default     = true
}

# ECS Configuration
variable "ecs_launch_type" {
  description = "ECS launch type (FARGATE or EC2)"
  type        = string
  default     = "FARGATE"
}

variable "ecs_task_cpu" {
  description = "ECS task CPU units"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "ECS task memory in MB"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "ECS service desired task count"
  type        = number
  default     = 2
}

variable "ecs_autoscaling_min_capacity" {
  description = "ECS autoscaling minimum task count"
  type        = number
  default     = 2
}

variable "ecs_autoscaling_max_capacity" {
  description = "ECS autoscaling maximum task count"
  type        = number
  default     = 6
}

variable "ecs_autoscaling_target_cpu" {
  description = "Target CPU percentage for autoscaling"
  type        = number
  default     = 70
}

variable "ecs_autoscaling_target_memory" {
  description = "Target memory percentage for autoscaling"
  type        = number
  default     = 80
}

# ElastiCache Configuration
variable "elasticache_engine" {
  description = "ElastiCache engine"
  type        = string
  default     = "redis"
}

variable "elasticache_engine_version" {
  description = "ElastiCache engine version"
  type        = string
  default     = "7.0"
}

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "elasticache_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 2
}

# ALB Configuration
variable "alb_enable_https" {
  description = "Enable HTTPS on load balancer"
  type        = bool
  default     = true
}

variable "alb_certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
  default     = ""
}

variable "alb_enable_access_logs" {
  description = "Enable ALB access logs"
  type        = bool
  default     = true
}

variable "alb_health_check_enabled" {
  description = "Enable ALB health checks"
  type        = bool
  default     = true
}

variable "alb_health_check_path" {
  description = "ALB health check path"
  type        = string
  default     = "/api/v1/health/"
}

variable "alb_health_check_interval" {
  description = "ALB health check interval"
  type        = number
  default     = 30
}

variable "alb_health_check_timeout" {
  description = "ALB health check timeout"
  type        = number
  default     = 5
}

variable "alb_health_check_healthy_threshold" {
  description = "ALB healthy threshold"
  type        = number
  default     = 2
}

variable "alb_health_check_unhealthy_threshold" {
  description = "ALB unhealthy threshold"
  type        = number
  default     = 3
}

# Advanced Load Balancing Configuration (Gap #4)
variable "enable_path_based_routing" {
  description = "Enable path-based routing rules for microservices"
  type        = bool
  default     = true
}

variable "enable_canary_deployments" {
  description = "Enable canary deployment target groups (weighted routing)"
  type        = bool
  default     = true
}

variable "api_v1_path_patterns" {
  description = "URL path patterns for API v1 routing"
  type        = list(string)
  default     = ["/api/v1/*"]
}

variable "api_v2_path_patterns" {
  description = "URL path patterns for API v2 routing (canary)"
  type        = list(string)
  default     = ["/api/v2/*"]
}

variable "admin_path_patterns" {
  description = "URL path patterns for admin routing"
  type        = list(string)
  default     = ["/admin/*"]
}

variable "health_path_patterns" {
  description = "URL path patterns for health checks"
  type        = list(string)
  default     = ["/health/*", "/api/v1/health/*"]
}

variable "canary_traffic_weight" {
  description = "Percentage of traffic to send to canary deployment (0-100)"
  type        = number
  default     = 10
  validation {
    condition     = var.canary_traffic_weight >= 0 && var.canary_traffic_weight <= 100
    error_message = "Canary traffic weight must be between 0 and 100."
  }
}

variable "alb_response_time_threshold" {
  description = "ALB response time threshold in seconds for alarms"
  type        = number
  default     = 1
}

variable "enable_alb_detailed_logging" {
  description = "Enable detailed ALB request logging"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

# Route53 Configuration
variable "route53_zone_name" {
  description = "Route53 hosted zone name"
  type        = string
  default     = ""
}

variable "route53_record_name" {
  description = "Route53 DNS record name"
  type        = string
  default     = ""
}

# CloudWatch Configuration
variable "cloudwatch_log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
}

variable "cloudwatch_alarm_email" {
  description = "Email for CloudWatch alarms"
  type        = string
  default     = ""
}

# Backups Configuration
variable "enable_backups" {
  description = "Enable automated backups"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Backup retention period in days"
  type        = number
  default     = 30
}

variable "enable_s3_backup" {
  description = "Enable S3 backup bucket"
  type        = bool
  default     = true
}

variable "s3_backup_bucket_name" {
  description = "S3 bucket name for backups"
  type        = string
  default     = ""
}

# Security Configuration
variable "enable_waf" {
  description = "Enable AWS WAF"
  type        = bool
  default     = false
}

variable "enable_shield_advanced" {
  description = "Enable AWS Shield Advanced"
  type        = bool
  default     = false
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access resources"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs"
  type        = bool
  default     = true
}

# Tagging
variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}

variable "cost_allocation_tags" {
  description = "Cost allocation tags"
  type        = map(string)
  default = {
    CostCenter = "Engineering"
    Team       = "DevOps"
  }
}

# ============================================================================
# Advanced Auto-Scaling Configuration (Gap #5)
# ============================================================================

variable "enable_ecs_autoscaling" {
  description = "Enable ECS service auto-scaling"
  type        = bool
  default     = true
}

variable "ecs_min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
  default     = 2
  validation {
    condition     = var.ecs_min_capacity >= 1
    error_message = "Minimum capacity must be at least 1."
  }
}

variable "ecs_max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
  default     = 10
  validation {
    condition     = var.ecs_max_capacity >= var.ecs_min_capacity
    error_message = "Maximum capacity must be greater than or equal to minimum capacity."
  }
}

variable "enable_cpu_scaling" {
  description = "Enable CPU-based target tracking scaling"
  type        = bool
  default     = true
}

variable "ecs_target_cpu_percentage" {
  description = "Target CPU utilization percentage for scaling"
  type        = number
  default     = 70
  validation {
    condition     = var.ecs_target_cpu_percentage > 0 && var.ecs_target_cpu_percentage <= 100
    error_message = "CPU percentage must be between 1 and 100."
  }
}

variable "enable_memory_scaling" {
  description = "Enable memory-based target tracking scaling"
  type        = bool
  default     = true
}

variable "ecs_target_memory_percentage" {
  description = "Target memory utilization percentage for scaling"
  type        = number
  default     = 75
  validation {
    condition     = var.ecs_target_memory_percentage > 0 && var.ecs_target_memory_percentage <= 100
    error_message = "Memory percentage must be between 1 and 100."
  }
}

variable "enable_alb_request_scaling" {
  description = "Enable ALB request count-based scaling"
  type        = bool
  default     = true
}

variable "ecs_target_requests_per_minute" {
  description = "Target requests per minute per task"
  type        = number
  default     = 1000
  validation {
    condition     = var.ecs_target_requests_per_minute > 0
    error_message = "Target requests must be greater than 0."
  }
}

variable "ecs_scale_out_cooldown" {
  description = "Cooldown period (seconds) after scale-out action"
  type        = number
  default     = 60
}

variable "ecs_scale_in_cooldown" {
  description = "Cooldown period (seconds) after scale-in action"
  type        = number
  default     = 300
}

variable "ecs_disable_scale_in" {
  description = "Disable scale-in for safety (during deployments)"
  type        = bool
  default     = false
}

variable "enable_step_scaling" {
  description = "Enable step scaling for rapid response"
  type        = bool
  default     = true
}

variable "ecs_step_scaling_cooldown" {
  description = "Cooldown period (seconds) for step scaling"
  type        = number
  default     = 60
}

variable "ecs_cpu_alarm_threshold" {
  description = "CPU utilization threshold for high CPU alarm"
  type        = number
  default     = 80
}

variable "ecs_cpu_low_threshold" {
  description = "CPU utilization threshold for low CPU alarm (scale-down)"
  type        = number
  default     = 30
}

variable "enable_scheduled_scaling" {
  description = "Enable scheduled scaling for predictable patterns"
  type        = bool
  default     = true
}

variable "timezone" {
  description = "Timezone for scheduled scaling (e.g., 'America/New_York', 'UTC')"
  type        = string
  default     = "UTC"
}

variable "ecs_peak_min_capacity" {
  description = "Minimum capacity during peak hours (business hours)"
  type        = number
  default     = 4
}

variable "ecs_peak_max_capacity" {
  description = "Maximum capacity during peak hours (business hours)"
  type        = number
  default     = 10
}

variable "ecs_offpeak_min_capacity" {
  description = "Minimum capacity during off-peak hours"
  type        = number
  default     = 2
}

variable "ecs_offpeak_max_capacity" {
  description = "Maximum capacity during off-peak hours"
  type        = number
  default     = 6
}

variable "ecs_weekend_min_capacity" {
  description = "Minimum capacity during weekends"
  type        = number
  default     = 1
}

variable "ecs_weekend_max_capacity" {
  description = "Maximum capacity during weekends"
  type        = number
  default     = 4
}

# ============================================================================
# Advanced Monitoring & Observability Configuration (Gap #6)
# ============================================================================

variable "enable_monitoring_dashboards" {
  description = "Enable CloudWatch dashboards for monitoring"
  type        = bool
  default     = true
}

variable "enable_critical_alarms" {
  description = "Enable critical alerting alarms"
  type        = bool
  default     = true
}

variable "enable_database_alarms" {
  description = "Enable database-specific alarms"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention must be a valid CloudWatch retention period."
  }
}

variable "enable_alb_access_logs" {
  description = "Enable ALB access logging"
  type        = bool
  default     = true
}

variable "enable_rds_logs" {
  description = "Enable RDS database logging"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications"
  type        = string
  default     = ""
  sensitive   = true
}

variable "alarm_5xx_threshold" {
  description = "Threshold for 5XX error alarm (count per 5 minutes)"
  type        = number
  default     = 10
  validation {
    condition     = var.alarm_5xx_threshold > 0
    error_message = "5XX threshold must be greater than 0."
  }
}

variable "alarm_cpu_threshold" {
  description = "Threshold for CPU utilization alarm (percentage)"
  type        = number
  default     = 85
  validation {
    condition     = var.alarm_cpu_threshold > 0 && var.alarm_cpu_threshold <= 100
    error_message = "CPU threshold must be between 1 and 100."
  }
}

variable "alarm_memory_threshold" {
  description = "Threshold for memory utilization alarm (percentage)"
  type        = number
  default     = 90
  validation {
    condition     = var.alarm_memory_threshold > 0 && var.alarm_memory_threshold <= 100
    error_message = "Memory threshold must be between 1 and 100."
  }
}

variable "alarm_response_time_threshold" {
  description = "Threshold for response time alarm (seconds)"
  type        = number
  default     = 2.0
  validation {
    condition     = var.alarm_response_time_threshold > 0
    error_message = "Response time threshold must be greater than 0."
  }
}

variable "alarm_rds_cpu_threshold" {
  description = "Threshold for RDS CPU utilization alarm (percentage)"
  type        = number
  default     = 80
  validation {
    condition     = var.alarm_rds_cpu_threshold > 0 && var.alarm_rds_cpu_threshold <= 100
    error_message = "RDS CPU threshold must be between 1 and 100."
  }
}

variable "alarm_rds_connections_threshold" {
  description = "Threshold for RDS database connections alarm"
  type        = number
  default     = 80
}

variable "enable_xray" {
  description = "Enable AWS X-Ray for distributed tracing"
  type        = bool
  default     = true
}

variable "xray_sample_rate" {
  description = "X-Ray sampling rate (0.0-1.0, where 1.0 = 100%)"
  type        = number
  default     = 0.1
  validation {
    condition     = var.xray_sample_rate >= 0 && var.xray_sample_rate <= 1
    error_message = "X-Ray sample rate must be between 0 and 1."
  }
}

variable "enable_log_encryption" {
  description = "Enable encryption for CloudWatch Logs"
  type        = bool
  default     = true
}

# ============================================================================
# REDIS CACHING CONFIGURATION (Gap #7)
# ============================================================================

variable "enable_redis_caching" {
  description = "Enable Redis ElastiCache cluster for session and data caching"
  type        = bool
  default     = true
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type (t4g.micro, t4g.small, cache.t4g.medium, etc.)"
  type        = string
  default     = "cache.t4g.micro"
  validation {
    condition     = contains(["cache.t4g.micro", "cache.t4g.small", "cache.t4g.medium", "cache.r7g.large", "cache.r7g.xlarge", "cache.r7g.2xlarge"], var.redis_node_type)
    error_message = "Redis node type must be a valid ElastiCache instance type."
  }
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes (1 for non-HA, 2+ for high availability)"
  type        = number
  default     = 1
  validation {
    condition     = var.redis_num_nodes >= 1 && var.redis_num_nodes <= 10
    error_message = "Number of Redis nodes must be between 1 and 10."
  }
}

variable "redis_engine_version" {
  description = "Redis engine version (7.0, 7.1, etc.)"
  type        = string
  default     = "7.0"
}

variable "redis_num_databases" {
  description = "Number of Redis databases (default 16)"
  type        = number
  default     = 16
}

variable "redis_enable_multi_az" {
  description = "Enable Multi-AZ for Redis (requires 2+ nodes)"
  type        = bool
  default     = false
}

variable "redis_snapshot_retention_days" {
  description = "Number of days to retain Redis snapshots"
  type        = number
  default     = 5
}

variable "redis_alarm_cpu_threshold" {
  description = "Alert threshold for Redis CPU utilization (%)"
  type        = number
  default     = 75
  validation {
    condition     = var.redis_alarm_cpu_threshold > 0 && var.redis_alarm_cpu_threshold <= 100
    error_message = "Redis CPU threshold must be between 1 and 100."
  }
}

variable "redis_alarm_memory_threshold" {
  description = "Alert threshold for Redis memory utilization (%)"
  type        = number
  default     = 80
  validation {
    condition     = var.redis_alarm_memory_threshold > 0 && var.redis_alarm_memory_threshold <= 100
    error_message = "Redis memory threshold must be between 1 and 100."
  }
}

variable "enable_redis_encryption" {
  description = "Enable encryption at rest and in transit for Redis"
  type        = bool
  default     = true
}

variable "enable_redis_notifications" {
  description = "Enable SNS notifications for Redis events"
  type        = bool
  default     = true
}

variable "enable_redis_monitoring" {
  description = "Enable CloudWatch logs for Redis slow queries and engine logs"
  type        = bool
  default     = true
}

# ============================================================================
# DATABASE PERFORMANCE TUNING (Gap #7)
# ============================================================================

variable "rds_instance_identifier" {
  description = "RDS instance identifier to apply performance tuning"
  type        = string
  default     = "nephele-hms-db"
}

variable "rds_engine" {
  description = "RDS database engine (postgres, mysql)"
  type        = string
  default     = "postgres"
  validation {
    condition     = contains(["postgres", "mysql"], var.rds_engine)
    error_message = "RDS engine must be postgres or mysql."
  }
}

variable "rds_parameter_group_family" {
  description = "Parameter group family (e.g., postgres14, mysql8.0)"
  type        = string
  default     = "postgres14"
}

variable "rds_max_connections" {
  description = "Maximum number of database connections"
  type        = number
  default     = 200
}

variable "rds_shared_buffers_percent" {
  description = "PostgreSQL shared_buffers as percentage of instance memory"
  type        = number
  default     = 25
}

variable "rds_innodb_buffer_pool_percent" {
  description = "MySQL InnoDB buffer pool as percentage of instance memory"
  type        = number
  default     = 75
}

variable "rds_effective_cache_size_percent" {
  description = "PostgreSQL effective_cache_size as percentage of instance memory"
  type        = number
  default     = 50
}

variable "rds_work_mem_mb" {
  description = "PostgreSQL work_mem per operation (MB)"
  type        = number
  default     = 64
}

variable "rds_slow_query_threshold_ms" {
  description = "Threshold for logging slow queries (milliseconds)"
  type        = number
  default     = 1000
  validation {
    condition     = var.rds_slow_query_threshold_ms > 0
    error_message = "Slow query threshold must be greater than 0."
  }
}

variable "enable_performance_insights" {
  description = "Enable AWS RDS Performance Insights for detailed monitoring"
  type        = bool
  default     = true
}

variable "performance_insights_retention_days" {
  description = "Performance Insights data retention period (7 = free tier, 31+ requires payment)"
  type        = number
  default     = 7
  validation {
    condition     = var.performance_insights_retention_days == 7 || var.performance_insights_retention_days >= 31
    error_message = "Performance Insights retention must be 7 (free) or 31+ days."
  }
}

# ============================================================================
# SECURITY HARDENING CONFIGURATION (Gap #8)
# ============================================================================

variable "enable_waf_security" {
  description = "Enable AWS WAF for web application firewall protection"
  type        = bool
  default     = true
}

variable "waf_rate_limit_requests" {
  description = "Rate limit: maximum requests per 5 minutes per IP"
  type        = number
  default     = 2000
  validation {
    condition     = var.waf_rate_limit_requests > 100
    error_message = "Rate limit must be greater than 100 requests."
  }
}

variable "waf_whitelist_ips" {
  description = "List of IPs to whitelist from rate limiting (e.g., monitoring services)"
  type        = list(string)
  default     = []
}

variable "admin_only_ips" {
  description = "List of IPs allowed to access admin endpoints"
  type        = list(string)
  default     = []
}

variable "waf_alarm_threshold" {
  description = "Number of blocked requests to trigger CloudWatch alarm"
  type        = number
  default     = 100
}

variable "enable_geo_blocking" {
  description = "Enable geographic blocking for specific countries"
  type        = bool
  default     = false
}

variable "blocked_countries" {
  description = "List of country codes to block (e.g., ['CN', 'RU'])"
  type        = list(string)
  default     = []
}

variable "enable_waf_logging" {
  description = "Enable logging of WAF activity to CloudWatch"
  type        = bool
  default     = true
}

variable "enable_secrets_management" {
  description = "Enable AWS Secrets Manager for credential storage"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Enable KMS encryption at rest for sensitive data"
  type        = bool
  default     = true
}

variable "enable_https" {
  description = "Enable HTTPS/TLS for all traffic"
  type        = bool
  default     = true
}

variable "enforce_https" {
  description = "Enforce HTTPS (redirect HTTP to HTTPS, remove certbot errors)"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "domain_name" {
  description = "Primary domain name for HTTPS certificate"
  type        = string
  default     = ""
}

variable "alternative_domain_names" {
  description = "Alternative domain names for HTTPS certificate (SANs)"
  type        = list(string)
  default     = []
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for DNS validation"
  type        = string
  default     = ""
}

variable "alb_security_group_id" {
  description = "ALB security group ID for WAF association"
  type        = string
  default     = ""
}

variable "alb_arn" {
  description = "ALB ARN for WAF association"
  type        = string
  default     = ""
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for security alarms"
  type        = string
  default     = ""
}

variable "ecs_security_group_id" {
  description = "ECS security group ID"
  type        = string
  default     = ""
}

variable "enable_shield_advanced_security" {
  description = "Enable AWS Shield Advanced for DDoS protection"
  type        = bool
  default     = false
}

variable "enable_guardduty" {
  description = "Enable AWS GuardDuty for threat detection"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "enable_config" {
  description = "Enable AWS Config for compliance tracking"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "enable_security_hub" {
  description = "Enable AWS Security Hub for security posture management"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "password_rotation_days" {
  description = "Rotate secrets every N days"
  type        = number
  default     = 30
  validation {
    condition     = var.password_rotation_days >= 1 && var.password_rotation_days <= 365
    error_message = "Password rotation days must be between 1 and 365."
  }
}

variable "min_tls_version" {
  description = "Minimum TLS version (1.2 or 1.3)"
  type        = string
  default     = "TLSv1.2"
  validation {
    condition     = contains(["TLSv1.2", "TLSv1.3"], var.min_tls_version)
    error_message = "TLS version must be TLSv1.2 or TLSv1.3."
  }
}

# ============================================================================
# ADVANCED LOGGING CONFIGURATION (Gap #9)
# ============================================================================

variable "enable_elasticsearch" {
  description = "Enable Elasticsearch domain for centralized logging"
  type        = bool
  default     = true
}

variable "elasticsearch_version" {
  description = "Elasticsearch engine version"
  type        = string
  default     = "7.10"
}

variable "elasticsearch_instance_type" {
  description = "Elasticsearch instance type (t3.small.elasticsearch for dev, m5.large.elasticsearch for prod)"
  type        = string
  default     = "t3.small.elasticsearch"
  validation {
    condition     = contains(["t3.small.elasticsearch", "t3.medium.elasticsearch", "m5.large.elasticsearch", "m5.xlarge.elasticsearch", "m5.2xlarge.elasticsearch"], var.elasticsearch_instance_type)
    error_message = "Must be a valid Elasticsearch instance type."
  }
}

variable "elasticsearch_instance_count" {
  description = "Number of Elasticsearch instances"
  type        = number
  default     = 1
  validation {
    condition     = var.elasticsearch_instance_count >= 1 && var.elasticsearch_instance_count <= 20
    error_message = "Instance count must be between 1 and 20."
  }
}

variable "elasticsearch_master_type" {
  description = "Elasticsearch master node instance type"
  type        = string
  default     = "m5.large.elasticsearch"
}

variable "elasticsearch_ebs_volume_size" {
  description = "Elasticsearch EBS volume size in GB"
  type        = number
  default     = 100
  validation {
    condition     = var.elasticsearch_ebs_volume_size >= 20 && var.elasticsearch_ebs_volume_size <= 1000
    error_message = "EBS volume size must be between 20 and 1000 GB."
  }
}

variable "elasticsearch_storage_threshold" {
  description = "Alert threshold for Elasticsearch storage usage (as percentage of total)"
  type        = number
  default     = 80
  validation {
    condition     = var.elasticsearch_storage_threshold > 0 && var.elasticsearch_storage_threshold <= 100
    error_message = "Storage threshold must be between 0 and 100."
  }
}

variable "enable_kibana" {
  description = "Enable Kibana for Elasticsearch visualization"
  type        = bool
  default     = true
}

variable "kibana_instance_type" {
  description = "Kibana instance type"
  type        = string
  default     = "t3.small"
}

variable "enable_alb_logging" {
  description = "Enable ALB access logging to CloudWatch"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs for network monitoring"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Must be a valid CloudWatch retention period."
  }
}

variable "log_filter_pattern" {
  description = "CloudWatch log filter pattern for Firehose subscription"
  type        = string
  default     = "[ERROR] | [WARN] | [CRITICAL]"
}

variable "elasticsearch_backup_enabled" {
  description = "Enable automated Elasticsearch backups"
  type        = bool
  default     = true
}

variable "elasticsearch_backup_interval_minutes" {
  description = "Backup interval in minutes"
  type        = number
  default     = 60
}

variable "enable_log_insights_queries" {
  description = "Enable CloudWatch Logs Insights for advanced log querying"
  type        = bool
  default     = true
}

variable "enable_custom_metrics" {
  description = "Enable custom metrics from CloudWatch Logs"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "cloudtrail_log_group" {
  description = "CloudWatch log group for CloudTrail logs"
  type        = string
  default     = "/aws/cloudtrail/nephele-hms"
}

variable "vpc_flow_log_format" {
  description = "VPC Flow Log format (default or custom)"
  type        = string
  default     = "default"
  validation {
    condition     = contains(["default", "extended"], var.vpc_flow_log_format)
    error_message = "VPC Flow Log format must be 'default' or 'extended'."
  }
}

# ============================================================================
# DISASTER RECOVERY CONFIGURATION (Gap #10)
# ============================================================================

variable "enable_dr" {
  description = "Enable disaster recovery and multi-region failover"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "primary_region" {
  description = "Primary AWS region"
  type        = string
  default     = "us-east-1"
}

variable "secondary_region" {
  description = "Secondary AWS region for disaster recovery"
  type        = string
  default     = "us-west-2"
}

variable "primary_alb_ip" {
  description = "Primary ALB IP address for health checks"
  type        = string
  default     = ""
}

variable "secondary_alb_ip" {
  description = "Secondary ALB IP address for health checks"
  type        = string
  default     = ""
}

variable "primary_alb_dns" {
  description = "Primary ALB DNS name"
  type        = string
  default     = ""
}

variable "secondary_alb_dns" {
  description = "Secondary ALB DNS name"
  type        = string
  default     = ""
}

variable "alb_zone_id" {
  description = "Route53 zone ID for ALB"
  type        = string
  default     = ""
}

variable "enable_rds_dr" {
  description = "Enable RDS cross-region read replica for DR"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "source_db_id" {
  description = "Source RDS database identifier for cross-region replica"
  type        = string
  default     = ""
}

variable "db_instance_identifier" {
  description = "RDS database instance identifier"
  type        = string
  default     = "nephele-hms-db"
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "source_bucket_id" {
  description = "Source S3 bucket ID for cross-region replication"
  type        = string
  default     = ""
}

variable "destination_bucket_arn" {
  description = "Destination S3 bucket ARN for DR replication"
  type        = string
  default     = ""
}

variable "enable_s3_dr" {
  description = "Enable S3 cross-region replication"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "enable_elasticache_dr" {
  description = "Enable ElastiCache cross-region replication"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "primary_elasticache_cluster_id" {
  description = "Primary ElastiCache cluster ID"
  type        = string
  default     = ""
}

variable "elasticache_replica_count" {
  description = "Number of cache nodes in DR replica"
  type        = number
  default     = 2
}

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "elasticache_version" {
  description = "ElastiCache engine version"
  type        = string
  default     = "6.x"
}

variable "elasticache_parameter_group" {
  description = "ElastiCache parameter group name"
  type        = string
  default     = "default.redis6.x"
}

variable "elasticache_security_group_id" {
  description = "ElastiCache security group ID"
  type        = string
  default     = ""
}

variable "elasticache_subnet_group" {
  description = "ElastiCache subnet group name"
  type        = string
  default     = ""
}

variable "enable_backup_vault" {
  description = "Enable AWS Backup vault for disaster recovery"
  type        = bool
  default     = var.environment == "prod" ? true : false
}

variable "rds_arn" {
  description = "RDS database ARN for backup"
  type        = string
  default     = ""
}

variable "dr_rto_minutes" {
  description = "Recovery Time Objective in minutes"
  type        = number
  default     = 15  # 15 minutes for full recovery
}

variable "dr_rpo_hours" {
  description = "Recovery Point Objective in hours"
  type        = number
  default     = 1   # 1 hour maximum data loss
}

variable "dr_max_capacity" {
  description = "Maximum ECS task count for DR failover"
  type        = number
  default     = 20
}

variable "dr_min_capacity" {
  description = "Minimum ECS task count for DR region"
  type        = number
  default     = 2
}

variable "dr_cpu_target" {
  description = "Target CPU utilization for DR auto-scaling"
  type        = number
  default     = 70
}

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
  default     = "nephele-hms"
}

variable "ecs_service_name" {
  description = "ECS service name"
  type        = string
  default     = "api"
}
