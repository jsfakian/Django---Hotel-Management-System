# Staging Environment Configuration
# Moderate resources for testing and quality assurance

environment              = "staging"
aws_region               = "us-east-1"
project_name             = "nephele-hms"
application_name         = "hotel-management-system"

# VPC Configuration - 2 AZs for basic redundancy
vpc_cidr                 = "10.1.0.0/16"
enable_nat_gateway       = true
enable_vpn_gateway       = false
availability_zones       = 2

# RDS Configuration - Small instance for staging
rds_engine               = "postgres"
rds_engine_version       = "15.4"
rds_instance_class       = "db.t3.small"
rds_allocated_storage    = 50
rds_max_allocated_storage = 100
rds_database_name        = "hotel_management_system_staging"
rds_database_username    = "postgres"
rds_backup_retention_days = 14
rds_multi_az             = false
rds_enable_encryption    = true

# ECR Configuration
ecr_image_tag_mutability = "IMMUTABLE"
ecr_scan_on_push         = true

# ECS Configuration - Moderate tasks for staging
ecs_launch_type          = "FARGATE"
ecs_task_cpu             = 512
ecs_task_memory          = 1024
ecs_desired_count        = 2
ecs_autoscaling_min_capacity = 2
ecs_autoscaling_max_capacity = 4
ecs_autoscaling_target_cpu   = 70
ecs_autoscaling_target_memory = 80

# ElastiCache Configuration - Small cluster for staging
elasticache_engine       = "redis"
elasticache_engine_version = "7.0"
elasticache_node_type    = "cache.t3.small"
elasticache_num_cache_nodes = 2

# ALB Configuration - with basic HTTPS setup
alb_enable_https         = true
alb_certificate_arn      = "" # Add staging certificate ARN here
alb_enable_access_logs   = true
alb_health_check_enabled = true
alb_health_check_path    = "/api/v1/health/"
alb_health_check_interval = 30
alb_health_check_timeout = 5
alb_health_check_healthy_threshold = 2
alb_health_check_unhealthy_threshold = 3

# Route53 Configuration (optional for staging)
route53_zone_name        = "staging.example.com"
route53_record_name      = "api"

# CloudWatch Configuration
cloudwatch_log_retention_days = 14
cloudwatch_alarm_email   = "devops@example.com"

# Backups Configuration
enable_backups           = true
backup_retention_days    = 14
enable_s3_backup         = true
s3_backup_bucket_name    = ""

# Security Configuration
enable_waf               = false
enable_shield_advanced   = false
allowed_cidr_blocks      = ["0.0.0.0/0"]
enable_vpc_flow_logs     = false

# Tags
tags = {
  Environment = "staging"
  CostCenter  = "Engineering"
  Team        = "DevOps"
  Tier        = "Staging"
}

cost_allocation_tags = {
  CostCenter = "Engineering"
  Team       = "DevOps"
}
