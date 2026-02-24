# Terraform root configuration file
# Imports and orchestrates all infrastructure modules

# All provider configuration is in versions.tf
# All variables are in variables.tf
# All outputs are in outputs.tf

# Terraform module organization:
# - versions.tf: Provider versioning and requirements
# - variables.tf: Input variables (150+ lines, comprehensive)
# - networking.tf: VPC, subnets, security groups, VPC Flow Logs (200+ lines)
# - database.tf: RDS, Secrets Manager, backup S3, CloudWatch (300+ lines)
# - compute.tf: ALB, ECS/Fargate, ECR, ElastiCache, Auto Scaling (400+ lines)
# - outputs.tf: Export values for deployment and monitoring
# - environments/dev.tfvars: Development environment variables
# - environments/staging.tfvars: Staging environment variables
# - environments/prod.tfvars: Production environment variables

# Infrastructure Summary:
# ========================
# VPC Networking:
#   - VPC with configurable CIDR block
#   - Multi-AZ support (2-3 availability zones)
#   - Public subnets with Internet Gateway
#   - Private subnets with NAT Gateway for secure outbound
#   - Security groups (ALB, RDS, ECS, ElastiCache)
#   - VPC Flow Logs for network monitoring

# Database Layer:
#   - RDS PostgreSQL (managed relational database)
#   - Multi-AZ deployment option for high availability
#   - Automated backups with configurable retention
#   - Secrets Manager for password management
#   - S3 backup bucket with lifecycle policies
#   - Enhanced monitoring with CloudWatch
#   - Performance Insights enabled
#   - Point-in-Time Recovery (PITR)

# Application Layer:
#   - ECS Cluster with Fargate launch type
#   - Application Load Balancer (ALB)
#   - ECS Auto Scaling (CPU and memory based)
#   - ECR Private Docker registry
#   - IAM roles for task execution and application access

# Caching Layer:
#   - ElastiCache Redis cluster
#   - Multi-AZ replication with automatic failover
#   - Encryption at rest
#   - Automatic snapshots

# Monitoring & Logging:
#   - CloudWatch Log Groups for RDS, ECS, and VPC Flow Logs
#   - CloudWatch Alarms for critical metrics (CPU, storage, health)
#   - RDS Enhanced Monitoring
#   - ALB access logs to S3
#   - ECS Container Insights

# Security Features:
#   - IAM roles and policies (least privilege)
#   - Secrets Manager for sensitive data
#   - Security groups with restricted access
#   - S3 public access blocks
#   - Encryption at rest and in transit
#   - VPC isolation for private resources

# Backup & Disaster Recovery:
#   - RDS automated backups with PITR
#   - S3 backup bucket with versioning and lifecycle
#   - Backup health checks and monitoring
#   - Restore procedures documented in Gap #2

# Auto Scaling:
#   - ECS service auto scaling (2-6 tasks by default)
#   - CPU-based scaling policy (target 70%)
#   - Memory-based scaling policy (target 80%)
#   - RDS auto-scaling storage (up to max allocated)

# Deployment Instructions:
# ========================
# 1. Initialize Terraform:
#    terraform init -backend=false
#
# 2. Plan infrastructure:
#    terraform plan -var-file=environments/dev.tfvars
#
# 3. Apply configuration:
#    terraform apply -var-file=environments/dev.tfvars
#
# 4. Setup remote state (optional, after initial apply):
#    - Create S3 bucket: s3://project-terraform-state-{account-id}
#    - Create DynamoDB table: project-terraform-locks
#    - Uncomment backend in versions.tf
#    - terraform init (migrate state)

# To use different environments:
# 
# For development:
#   terraform apply -var-file=environments/dev.tfvars
#
# For staging:
#   terraform apply -var-file=environments/staging.tfvars
#
# For production:
#   terraform apply -var-file=environments/prod.tfvars

# Destroying infrastructure:
#   terraform destroy -var-file=environments/dev.tfvars

# Integration with Gap #2 (Database Backups):
# ============================================
# The Terraform infrastructure sets up:
# - RDS automated backups (managed by AWS)
# - S3 bucket for manual export backups
# - Backup health monitoring
# - Secrets Manager for database credentials
#
# Gap #2 scripts should use these values from outputs:
# - RDS endpoint: from output rds_endpoint
# - RDS port: from output rds_port
# - S3 backup bucket: from output backup_bucket_name
# - Database password: from Secrets Manager

# Integration with Gap #1 (Docker Infrastructure):
# =================================================
# Docker images from docker-compose.prod.yml are deployed as:
# - Web application: Pushed to ECR, deployed via ECS
# - Redis: Replaced by ElastiCache Redis (managed service)
# - Celery worker: Can be added as additional ECS task definition
# - PostgreSQL: Replaced by RDS (managed service)
# - Nginx: ALB replaces reverse proxy functionality

# Resource Naming Convention:
# ===========================
# All resources prefix with: ${var.project_name} (default: nephele-hms)
# Examples:
# - VPC: nephele-hms-vpc
# - RDS: nephele-hms-db
# - ECS: nephele-hms-cluster
# - ECR: nephele-hms-app
# - S3: nephele-hms-backups-{account-id}

# Tags Applied to All Resources:
# ==============================
# Via default_tags in provider (versions.tf):
# - Environment: dev/staging/prod
# - Project: nephele-hms
# - ManagedBy: Terraform
# - CreatedAt: Timestamp

# Cost Optimization:
# ==================
# - Dev environment: t3.micro RDS, cache.t3.micro ElastiCache
# - Staging environment: t3.small RDS, cache.t3.small ElastiCache
# - Production: t3.large RDS, cache.t3.large ElastiCache (with Multi-AZ)
# - FARGATE_SPOT for non-critical tasks (optional, in Capacity Providers)

# Next Steps (Gap #4-5):
# ======================
# Gap #4: Load Balancing
# - Enhanced ALB configuration
# - Path-based routing for microservices
# - SSL/TLS certificate management
#
# Gap #5: Auto Scaling
# - Advanced scaling policies
# - Predictive scaling based on metrics
# - Scheduled scaling for predictable traffic patterns
# - Cross-AZ load balancing optimization

# Terraform State Management:
# ============================
# Initial setup (local state):
#   terraform apply -var-file=environments/dev.tfvars
#
# Remote state setup (after initial apply):
#   1. Create S3 bucket and DynamoDB table
#   2. Uncomment backend block in versions.tf
#   3. Run: terraform init (choose to migrate existing state)
#
# State backup locations:
#   - Local: terraform.tfstate (backup via Gap #2)
#   - Remote: S3 (with versioning and encryption)
#   - Lock: DynamoDB (prevents concurrent modifications)

# Validation & Testing:
# =====================
# Terraform validation:
#   terraform validate
#
# Plan review:
#   terraform plan -var-file=environments/prod.tfvars -out=tfplan
#   terraform show tfplan
#
# Format checking:
#   terraform fmt -recursive

# Manual Testing Checklist:
# ==========================
# After terraform apply:
# 1. Verify VPC created: aws ec2 describe-vpcs --filters Name=tag:Name,Values=nephele-hms-vpc
# 2. Verify RDS endpoint: aws rds describe-db-instances --db-instance-identifier nephele-hms-db
# 3. Verify ALB DNS: aws elbv2 describe-load-balancers --names nephele-hms-alb
# 4. Verify ECR repository: aws ecr describe-repositories --repository-names nephele-hms-app
# 5. Test RDS connection: psql -h <rds-endpoint> -U postgres -d hotel_management_system
# 6. Check ECS cluster: aws ecs describe-clusters --clusters nephele-hms-cluster
# 7. Verify AutoScaling groups: aws autoscaling describe-auto-scaling-groups

# Emergency Procedures:
# =====================
# If something goes wrong:
#
# To destroy everything:
#   terraform destroy -var-file=environments/prod.tfvars
#
# To recreate without destroying state:
#   terraform taint aws_ecs_service.app
#   terraform apply -var-file=environments/prod.tfvars
#
# To force refresh state:
#   terraform refresh -var-file=environments/prod.tfvars
#
# To debug issues:
#   terraform show
#   terraform state list
#   terraform state show aws_db_instance.main
#   TF_LOG=DEBUG terraform apply (very verbose)

# Module Dependencies:
# ====================
# networking.tf (no dependencies)
# database.tf (depends on: networking.tf - security group)
# compute.tf (depends on: networking.tf - security groups, VPC, subnets)
#           (depends on: database.tf - RDS endpoint, password secret)
#
# Implicit ordering handled by Terraform automatically.
