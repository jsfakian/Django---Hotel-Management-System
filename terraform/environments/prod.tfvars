# Production Environment Configuration
# Full-featured production setup with high availability and security

environment              = "prod"
aws_region               = "us-east-1"
project_name             = "nephele-hms"
application_name         = "hotel-management-system"

# VPC Configuration - 3 AZs for full redundancy
vpc_cidr                 = "10.2.0.0/16"
enable_nat_gateway       = true
enable_vpn_gateway       = true
availability_zones       = 3

# RDS Configuration - Production grade with Multi-AZ
rds_engine               = "postgres"
rds_engine_version       = "15.4"
rds_instance_class       = "db.t3.large"
rds_allocated_storage    = 200
rds_max_allocated_storage = 500
rds_database_name        = "hotel_management_system_prod"
rds_database_username    = "postgres"
rds_backup_retention_days = 30
rds_multi_az             = true
rds_enable_encryption    = true

# ECR Configuration
ecr_image_tag_mutability = "IMMUTABLE"
ecr_scan_on_push         = true

# ECS Configuration - Full scale for production
ecs_launch_type          = "FARGATE"
ecs_task_cpu             = 1024
ecs_task_memory          = 2048
ecs_desired_count        = 3
ecs_autoscaling_min_capacity = 3
ecs_autoscaling_max_capacity = 10
ecs_autoscaling_target_cpu   = 70
ecs_autoscaling_target_memory = 80

# ElastiCache Configuration - Production cluster with failover
elasticache_engine       = "redis"
elasticache_engine_version = "7.0"
elasticache_node_type    = "cache.t3.large"
elasticache_num_cache_nodes = 3

# ALB Configuration - Production grade HTTPS with WAF
alb_enable_https         = true
alb_certificate_arn      = "arn:aws:acm:us-east-1:ACCOUNT-ID:certificate/CERT-ID" # Update with actual certificate
alb_enable_access_logs   = true
alb_health_check_enabled = true
alb_health_check_path    = "/api/v1/health/"
alb_health_check_interval = 30
alb_health_check_timeout = 5
alb_health_check_healthy_threshold = 2
alb_health_check_unhealthy_threshold = 3

# Route53 Configuration - Production domain
route53_zone_name        = "example.com"
route53_record_name      = "api"

# CloudWatch Configuration - Extended retention for production
cloudwatch_log_retention_days = 30
cloudwatch_alarm_email   = "production-alerts@example.com"

# Backups Configuration - Extended retention for production
enable_backups           = true
backup_retention_days    = 30
enable_s3_backup         = true
s3_backup_bucket_name    = "nephele-hms-backups-prod"

# Security Configuration - Full security stack
enable_waf               = true
enable_shield_advanced   = true
allowed_cidr_blocks      = ["0.0.0.0/0"]
enable_vpc_flow_logs     = true

# Tags
tags = {
  Environment = "production"
  CostCenter  = "Operations"
  Team        = "DevOps"
  Tier        = "Production"
  Compliance  = "true"
  BackupPolicy = "30-days"
}

cost_allocation_tags = {
  CostCenter = "Operations"
  Team       = "DevOps"
  ChargeBackCode = "APP-001"
}
