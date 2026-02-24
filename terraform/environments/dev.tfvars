# Development Environment Configuration
# Minimal resources for development and testing

environment              = "dev"
aws_region               = "us-east-1"
project_name             = "nephele-hms"
application_name         = "hotel-management-system"

# VPC Configuration - Single AZ for cost savings
vpc_cidr                 = "10.0.0.0/16"
enable_nat_gateway       = true
enable_vpn_gateway       = false
availability_zones       = 1

# RDS Configuration - Minimal for development
rds_engine               = "postgres"
rds_engine_version       = "15.4"
rds_instance_class       = "db.t3.micro"
rds_allocated_storage    = 20
rds_max_allocated_storage = 50
rds_database_name        = "hotel_management_system_dev"
rds_database_username    = "postgres"
rds_backup_retention_days = 7
rds_multi_az             = false
rds_enable_encryption    = true

# ECR Configuration
ecr_image_tag_mutability = "MUTABLE"
ecr_scan_on_push         = false

# ECS Configuration - Minimal tasks for development
ecs_launch_type          = "FARGATE"
ecs_task_cpu             = 256
ecs_task_memory          = 512
ecs_desired_count        = 1
ecs_autoscaling_min_capacity = 1
ecs_autoscaling_max_capacity = 2
ecs_autoscaling_target_cpu   = 70
ecs_autoscaling_target_memory = 80

# ElastiCache Configuration - Minimal for development
elasticache_engine       = "redis"
elasticache_engine_version = "7.0"
elasticache_node_type    = "cache.t3.micro"
elasticache_num_cache_nodes = 1

# ALB Configuration
alb_enable_https         = false
alb_certificate_arn      = ""
alb_enable_access_logs   = false
alb_health_check_enabled = true
alb_health_check_path    = "/api/v1/health/"
alb_health_check_interval = 30
alb_health_check_timeout = 5
alb_health_check_healthy_threshold = 2
alb_health_check_unhealthy_threshold = 3

# Route53 Configuration (disabled for dev)
route53_zone_name        = ""
route53_record_name      = ""

# CloudWatch Configuration
cloudwatch_log_retention_days = 7
cloudwatch_alarm_email   = ""

# Backups Configuration
enable_backups           = true
backup_retention_days    = 7
enable_s3_backup         = true
s3_backup_bucket_name    = ""

# Security Configuration
enable_waf               = false
enable_shield_advanced   = false
allowed_cidr_blocks      = ["0.0.0.0/0"]
enable_vpc_flow_logs     = false

# Tags
tags = {
  Environment = "development"
  CostCenter  = "Engineering"
  Team        = "DevOps"
  Tier        = "Development"
}

cost_allocation_tags = {
  CostCenter = "Engineering"
  Team       = "DevOps"
}
