# Terraform Outputs - Export infrastructure values for deployment and monitoring

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "nat_gateway_ips" {
  description = "Elastic IPs of NAT Gateways"
  value       = try(aws_eip.nat[*].public_ip, [])
}

# Security Group Outputs
output "alb_security_group_id" {
  description = "Security group ID for ALB"
  value       = aws_security_group.alb.id
}

output "rds_security_group_id" {
  description = "Security group ID for RDS"
  value       = aws_security_group.rds.id
}

output "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  value       = aws_security_group.ecs.id
}

output "elasticache_security_group_id" {
  description = "Security group ID for ElastiCache"
  value       = aws_security_group.elasticache.id
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS database endpoint address"
  value       = aws_db_instance.main.address
}

output "rds_port" {
  description = "RDS database port"
  value       = aws_db_instance.main.port
}

output "rds_db_name" {
  description = "Name of the database"
  value       = aws_db_instance.main.db_name
  sensitive   = true
}

output "rds_instance_identifier" {
  description = "RDS instance identifier"
  value       = aws_db_instance.main.identifier
}

output "rds_instance_arn" {
  description = "ARN of the RDS instance"
  value       = aws_db_instance.main.arn
}

output "rds_backup_retention_days" {
  description = "RDS backup retention period"
  value       = aws_db_instance.main.backup_retention_period
}

output "rds_username" {
  description = "RDS master username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "rds_password_secret_arn" {
  description = "ARN of the Secrets Manager secret containing RDS password"
  value       = aws_secretsmanager_secret.rds_password.arn
}

# S3 Backup Bucket Outputs
output "backup_bucket_name" {
  description = "Name of the S3 backup bucket"
  value       = try(aws_s3_bucket.backups[0].id, "")
}

output "backup_bucket_arn" {
  description = "ARN of the S3 backup bucket"
  value       = try(aws_s3_bucket.backups[0].arn, "")
}

# ALB Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "alb_arn_suffix" {
  description = "ARN suffix for CloudWatch metrics"
  value       = aws_lb.main.arn_suffix
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

# Target Group Outputs
output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.app.arn
}

output "target_group_arn_suffix" {
  description = "ARN suffix for CloudWatch metrics"
  value       = aws_lb_target_group.app.arn_suffix
}

# ECS Cluster Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

# ECS Service Outputs
output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}

output "ecs_service_arn" {
  description = "ARN of the ECS service"
  value       = aws_ecs_service.app.arn
}

# ECS Task Definition Outputs
output "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = aws_ecs_task_definition.app.arn
}

output "ecs_task_definition_revision" {
  description = "Current revision of the ECS task definition"
  value       = aws_ecs_task_definition.app.revision
}

# ECR Repository Outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.app.arn
}

# ElastiCache Outputs
output "elasticache_primary_endpoint_address" {
  description = "Primary endpoint address of the Redis cluster"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "elasticache_primary_endpoint_port" {
  description = "Port of the Redis cluster"
  value       = aws_elasticache_replication_group.main.port
}

output "elasticache_member_clusters" {
  description = "Member clusters of the Redis cluster"
  value       = aws_elasticache_replication_group.main.member_clusters
}

output "elasticache_replication_group_id" {
  description = "ID of the Redis replication group"
  value       = aws_elasticache_replication_group.main.id
}

# CloudWatch Log Groups
output "rds_log_group_name" {
  description = "CloudWatch log group for RDS"
  value       = aws_cloudwatch_log_group.rds.name
}

output "ecs_log_group_name" {
  description = "CloudWatch log group for ECS"
  value       = aws_cloudwatch_log_group.ecs.name
}

output "vpc_flow_logs_group_name" {
  description = "CloudWatch log group for VPC Flow Logs"
  value       = try(aws_cloudwatch_log_group.vpc_flow_logs[0].name, "")
}

# IAM Role Outputs
output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

# Auto Scaling Outputs
output "ecs_autoscaling_target_resource_id" {
  description = "Resource ID of the ECS service for auto scaling"
  value       = aws_appautoscaling_target.ecs_target.resource_id
}

output "ecs_autoscaling_min_capacity" {
  description = "Minimum ECS task count for auto scaling"
  value       = aws_appautoscaling_target.ecs_target.min_capacity
}

output "ecs_autoscaling_max_capacity" {
  description = "Maximum ECS task count for auto scaling"
  value       = aws_appautoscaling_target.ecs_target.max_capacity
}

# System Summary Output
output "system_summary" {
  description = "Summary of the deployed infrastructure"
  value = {
    environment = var.environment
    region      = var.aws_region
    project     = var.project_name
    
    vpc = {
      id              = aws_vpc.main.id
      cidr            = aws_vpc.main.cidr_block
      subnets_public  = length(aws_subnet.public)
      subnets_private = length(aws_subnet.private)
      availability_zones = var.availability_zones
    }
    
    database = {
      endpoint            = aws_db_instance.main.address
      port                = aws_db_instance.main.port
      instance_class      = aws_db_instance.main.instance_class
      storage_gb          = aws_db_instance.main.allocated_storage
      backup_retention    = aws_db_instance.main.backup_retention_period
      multi_az            = aws_db_instance.main.multi_az
      engine_version      = aws_db_instance.main.engine_version
    }
    
    application = {
      alb_dns              = aws_lb.main.dns_name
      ecs_cluster          = aws_ecs_cluster.main.name
      ecs_service          = aws_ecs_service.app.name
      desired_task_count   = aws_ecs_service.app.desired_count
      autoscaling_min      = aws_appautoscaling_target.ecs_target.min_capacity
      autoscaling_max      = aws_appautoscaling_target.ecs_target.max_capacity
      task_cpu             = var.ecs_task_cpu
      task_memory          = var.ecs_task_memory
    }
    
    caching = {
      engine               = aws_elasticache_replication_group.main.engine
      primary_endpoint     = aws_elasticache_replication_group.main.primary_endpoint_address
      port                 = aws_elasticache_replication_group.main.port
      num_clusters         = var.elasticache_num_cache_nodes
    }
  }
}

# Deployment Variable File Output
# Use this to generate tfvars files for different environments
output "deployment_commands" {
  description = "Commands to deploy and manage infrastructure"
  value = {
    init    = "terraform init -backend=false"
    plan    = "terraform plan -var-file=environments/${var.environment}.tfvars"
    apply   = "terraform apply -var-file=environments/${var.environment}.tfvars"
    destroy = "terraform destroy -var-file=environments/${var.environment}.tfvars"
    validate = "terraform validate"
    format  = "terraform fmt -recursive"
  }
}
