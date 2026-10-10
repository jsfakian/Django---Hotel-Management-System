# Terraform Infrastructure as Code Guide
## Gap #3: Infrastructure as Code Implementation

**Status:** ✅ Complete  
**Created:** 2024  
**Last Updated:** 2024  
**Version:** 1.0.0

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [File Structure](#file-structure)
6. [Configuration](#configuration)
7. [Deployment](#deployment)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Integration with Gap #2](#integration-with-gap-2)

---

## 🎯 Overview

This Terraform infrastructure code provisions a production-ready AWS environment for the Hotel Management System (HMS). It creates a complete cloud infrastructure including:

- **Networking:** VPC with multi-AZ availability
- **Database:** RDS PostgreSQL with automated backups
- **Application:** ECS/Fargate with auto-scaling
- **Caching:** ElastiCache Redis cluster
- **Load Balancing:** Application Load Balancer
- **Monitoring:** CloudWatch with comprehensive logging

### Key Features

✅ **Multi-Environment Support:** Dev, Staging, Production  
✅ **High Availability:** Multi-AZ deployment (3 AZs for prod)  
✅ **Auto-Scaling:** ECS service scales based on CPU/memory  
✅ **Automated Backups:** RDS backups with S3 export  
✅ **Security:** Security groups, IAM roles, encryption  
✅ **Monitoring:** CloudWatch alarms and log aggregation  
✅ **Cost Optimization:** Environment-specific sizing  
✅ **Infrastructure as Code:** Complete version control  

---

## 🏗️ Architecture

### Infrastructure Layers

```
┌─────────────────────────────────────────────────────┐
│                   Application Layer                  │
│        (ECS Fargate + Application Load Balancer)     │
├─────────────────────────────────────────────────────┤
│                      Network Layer                   │
│     (VPC, Subnets, Security Groups, NAT Gateway)    │
├─────────────────────────────────────────────────────┤
│                     Data Layers                      │
│   (RDS PostgreSQL, ElastiCache Redis, S3 Backups)   │
├─────────────────────────────────────────────────────┤
│                    Monitoring Layer                  │
│        (CloudWatch, VPC Flow Logs, Log Groups)      │
└─────────────────────────────────────────────────────┘
```

### Resource Topology

**VPC Networking:**
- VPC with configurable CIDR block (10.0.0.0/16 by default)
- Public subnets (1 per AZ) with Internet Gateway
- Private subnets (1 per AZ) with NAT Gateway
- Security groups for ALB, RDS, ECS, ElastiCache

**Application Layer:**
- Application Load Balancer (ALB) in public subnets
- ECS Cluster with Fargate launch type
- ECS Service with 2-6 tasks (scalable)
- ECR Private Docker Registry

**Data Layer:**
- RDS PostgreSQL instance in private subnet
- Multi-AZ deployment option
- Automated backups with Point-in-Time Recovery
- ElastiCache Redis cluster with automatic failover
- S3 bucket for backup export and static files

**Monitoring:**
- CloudWatch Log Groups for RDS, ECS, VPC Flow Logs
- CloudWatch Alarms for critical metrics
- Performance Insights for database analysis

---

## 📦 Prerequisites

### Required Tools

1. **Terraform >= 1.5.0**
   ```bash
   terraform version
   ```

2. **AWS CLI >= 2.0**
   ```bash
   aws --version
   ```

3. **AWS Account with Credentials**
   ```bash
   aws configure
   # Or set environment variables:
   export AWS_ACCESS_KEY_ID=xxx
   export AWS_SECRET_ACCESS_KEY=xxx
   export AWS_DEFAULT_REGION=us-east-1
   ```

4. **jq (for JSON output parsing - optional)**
   ```bash
   jq --version
   ```

### AWS Permissions Required

Minimum IAM permissions needed:
- ec2:* (VPC, Security Groups, NAT Gateway)
- rds:* (Database instances, parameter groups)
- ecs:* (ECS cluster, services, task definitions)
- ecr:* (ECR repositories)
- elasticache:* (Redis cluster)
- elbv2:* (Load balancer)
- s3:* (Backup bucket)
- iam:* (Roles and policies)
- cloudwatch:* (Monitoring)
- secretsmanager:* (Password management)
- logs:* (CloudWatch logs)

**Recommended:** Use a dedicated IAM user account with appropriate permissions.

---

## ⚡ Quick Start

### 1. Initialize Terraform

```bash
# Initialize Terraform (local state)
make tf-init

# Or manually:
cd terraform
terraform init -backend=false
cd ..
```

**Note:** The `-backend=false` flag tells Terraform to use local state. After the initial apply, you can configure remote state (S3 backend) for team collaboration.

### 2. Validate Configuration

```bash
# Validate the Terraform files
make tf-validate

# Or manually:
cd terraform
terraform validate
cd ..
```

### 3. Plan Infrastructure

```bash
# Plan for development environment
make tf-plan-dev

# Or staging:
make tf-plan-staging

# Or production:
make tf-plan-prod
```

Review the output to understand what resources will be created.

### 4. Apply Configuration

```bash
# Apply to development
make tf-apply-dev

# Or staging:
make tf-apply-staging

# Or production (requires confirmation):
make tf-apply-prod
```

**Important:** For production, the Makefile will request confirmation before applying.

### 5. View Outputs

```bash
# Display infrastructure outputs
make tf-output

# Or manually:
cd terraform
terraform output
# or JSON format:
terraform output -json | jq '.'
cd ..
```

**Outputs include:**
- ALB DNS name (for accessing the application)
- RDS endpoint (for database connections)
- ECR repository URL (for pushing Docker images)
- ECS cluster name (for service management)
- Redis endpoint (for cache connections)

---

## 📂 File Structure

```
terraform/
├── versions.tf              # Provider versions and requirements
├── variables.tf             # Input variables definition (150+ lines)
├── main.tf                  # Main configuration and documentation
├── networking.tf            # VPC, subnets, security groups
├── database.tf              # RDS, Secrets Manager, backups
├── compute.tf               # ALB, ECS, ECR, ElastiCache
├── outputs.tf               # Exported infrastructure values
├── environments/
│   ├── dev.tfvars          # Development environment variables
│   ├── staging.tfvars      # Staging environment variables
│   └── prod.tfvars         # Production environment variables
├── terraform.tfstate        # Local state file (gitignored)
└── terraform.tfstate.backup # State backup (gitignored)
```

### File Descriptions

**versions.tf (25 lines)**
- Terraform version requirements
- Provider configuration (AWS, Random)
- Default tags for all resources
- S3 backend template (commented for future use)

**variables.tf (150+ lines)**
- All input variables with descriptions
- Defaults for each environment
- Validation rules
- Sensitive variable flags

**main.tf (Documentation)**
- Comprehensive comments
- Deployment instructions
- Troubleshooting guides
- Integration notes

**networking.tf (200+ lines)**
- VPC creation
- Public/private subnets
- Internet Gateway and NAT Gateway
- Security groups (ALB, RDS, ECS, ElastiCache)
- VPC Flow Logs

**database.tf (300+ lines)**
- RDS PostgreSQL instance
- Parameter group customization
- Secrets Manager for password
- S3 backup bucket
- CloudWatch monitoring
- Database alarms

**compute.tf (400+ lines)**
- Application Load Balancer
- ECS Cluster and Service
- ECS Task Definition
- ECR Repository
- ElastiCache Redis
- Auto Scaling policies
- CloudWatch alarms

**outputs.tf (200+ lines)**
- VPC outputs (IDs, CIDR blocks)
- RDS outputs (endpoint, port, credentials)
- ALB outputs (DNS name, ARN)
- ECS outputs (cluster, service, task definition)
- ECR outputs (repository URL)
- ElastiCache outputs (endpoint)
- Monitoring outputs (log groups)
- System summary (all-in-one output)

---

## ⚙️ Configuration

### Environment-Specific Settings

The infrastructure supports three environments with different configurations:

#### Development Environment (dev.tfvars)

```hcl
environment              = "dev"
vpc_cidr                 = "10.0.0.0/16"
availability_zones       = 1
rds_instance_class       = "db.t3.micro"
rds_allocated_storage    = 20
ecs_desired_count        = 1
ecs_autoscaling_max_capacity = 2
elasticache_node_type    = "cache.t3.micro"
alb_enable_https         = false
```

**Use Case:** Local development, testing, cost minimization

#### Staging Environment (staging.tfvars)

```hcl
environment              = "staging"
vpc_cidr                 = "10.1.0.0/16"
availability_zones       = 2
rds_instance_class       = "db.t3.small"
rds_allocated_storage    = 50
ecs_desired_count        = 2
ecs_autoscaling_max_capacity = 4
elasticache_node_type    = "cache.t3.small"
alb_enable_https         = true
```

**Use Case:** QA, integration testing, near-production testing

#### Production Environment (prod.tfvars)

```hcl
environment              = "prod"
vpc_cidr                 = "10.2.0.0/16"
availability_zones       = 3
rds_instance_class       = "db.t3.large"
rds_allocated_storage    = 200
rds_multi_az             = true
ecs_desired_count        = 3
ecs_autoscaling_max_capacity = 10
elasticache_node_type    = "cache.t3.large"
elasticache_num_cache_nodes = 3
alb_enable_https         = true
enable_waf               = true
enable_shield_advanced   = true
enable_vpc_flow_logs     = true
```

**Use Case:** Production deployment, high availability, full compliance

### Customizing Variables

To customize variables for your environment:

1. **Edit the tfvars file:**
   ```bash
   vim terraform/environments/prod.tfvars
   ```

2. **Or pass variables on command line:**
   ```bash
   cd terraform
   terraform apply -var="aws_region=eu-west-1" -var-file=environments/prod.tfvars
   ```

3. **Or create environment variables:**
   ```bash
   export TF_VAR_aws_region="eu-west-1"
   export TF_VAR_rds_instance_class="db.t3.xlarge"
   ```

### Important Variable Notes

**Sensitive Variables:**
- `rds_database_password`: Generated automatically, stored in Secrets Manager
- `rds_database_username`: Treated as sensitive
- `s3_backup_bucket_name`: Should be globally unique (append account ID)

**Validation Rules:**
- `environment` must be: dev, staging, or prod
- `rds_backup_retention_days`: 1-35 days for automated backups
- `availability_zones`: 1-3 AZs depending on account limits

**Cost Implications:**
- Dev: ~$20-30/month (t3.micro resources)
- Staging: ~$100-150/month (t3.small resources)
- Prod: ~$300-500+/month (t3.large + Multi-AZ + ALB)

---

## 🚀 Deployment

### Step-by-Step Deployment

#### 1. Prepare AWS Account

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Set output format
aws configure set output json
```

#### 2. Initialize Terraform

```bash
make tf-init
```

This creates local state file: `terraform/terraform.tfstate`

#### 3. Review Configuration

```bash
make tf-validate
```

Check for any syntax errors or missing resources.

#### 4. Generate Plan

For **development:**
```bash
make tf-plan-dev
```

For **staging:**
```bash
make tf-plan-staging
```

For **production:**
```bash
make tf-plan-prod
```

**Important:** Always review the plan output before applying!

#### 5. Apply Infrastructure

For **development:**
```bash
make tf-apply-dev
```

For **staging:**
```bash
make tf-apply-staging
```

For **production (with confirmation):**
```bash
make tf-apply-prod
```

**Wait time:** 15-30 minutes for complete deployment

#### 6. Verify Deployment

```bash
# View outputs
make tf-output

# Check AWS resources
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=nephele-hms-vpc"
aws rds describe-db-instances --db-instance-identifier nephele-hms-db
aws elbv2 describe-load-balancers --names nephele-hms-alb
```

#### 7. Configure Application

```bash
# Get RDS endpoint from outputs
RDS_ENDPOINT=$(cd terraform && terraform output -raw rds_endpoint)

# Get ALB DNS name
ALB_DNS=$(cd terraform && terraform output -raw alb_dns_name)

# Push Docker image to ECR
ECR_REPO=$(cd terraform && terraform output -raw ecr_repository_url)
docker tag hms:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

# Update ECS task definition with new image
aws ecs update-service --cluster nephele-hms-cluster --service nephele-hms-service --force-new-deployment
```

### Remote State Setup (After Initial Deploy)

For team collaboration, migrate to S3 backend:

#### 1. Create S3 Bucket and DynamoDB Table

```bash
# Create S3 bucket
aws s3api create-bucket \
  --bucket nephele-hms-terraform-state-$(aws sts get-caller-identity --query Account --output text) \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket nephele-hms-terraform-state-$(aws sts get-caller-identity --query Account --output text) \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locks
aws dynamodb create-table \
  --table-name nephele-hms-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

#### 2. Uncomment Backend in Terraform

Edit `terraform/versions.tf`:

```hcl
backend "s3" {
  bucket         = "nephele-hms-terraform-state-123456789"
  key            = "prod/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "nephele-hms-terraform-locks"
}
```

#### 3. Migrate State

```bash
cd terraform
terraform init

# Choose "yes" to migrate state to S3
```

#### 4. Verify Remote State

```bash
# List S3 objects
aws s3 ls s3://nephele-hms-terraform-state-123456789/

# Check local state file (should be small now)
ls -lh terraform.tfstate
```

---

## 📊 Monitoring

### CloudWatch Dashboards

Create a monitoring dashboard:

```bash
# View available log groups
aws logs describe-log-groups --query 'logGroups[*].logGroupName'

# View RDS logs
aws logs tail /aws/rds/instance/nephele-hms-db --follow

# View ECS logs
aws logs tail /ecs/nephele-hms --follow

# View VPC Flow Logs
aws logs tail /aws/vpc/flowlogs/nephele-hms --follow
```

### CloudWatch Alarms

Alarms are automatically created for:

1. **RDS CPU Utilization** (threshold: 80%)
2. **RDS Free Storage** (threshold: 10GB)
3. **ECS CPU Utilization** (threshold: 70%)
4. **ALB Unhealthy Targets** (threshold: 1+)

View alarms:

```bash
aws cloudwatch describe-alarms \
  --query 'MetricAlarms[?contains(AlarmName, `nephele-hms`)]'
```

### Manual Monitoring

```bash
# Check ECS service health
aws ecs describe-services \
  --cluster nephele-hms-cluster \
  --services nephele-hms-service \
  --query 'services[0].[runningCount,desiredCount,deployments]'

# Check RDS instance status
aws rds describe-db-instances \
  --db-instance-identifier nephele-hms-db \
  --query 'DBInstances[0].[DBInstanceStatus,DBInstanceClass,AllocatedStorage]'

# Check ElastiCache cluster status
aws elasticache describe-replication-groups \
  --query 'ReplicationGroups[*].[ReplicationGroupId,Status,MemberClusters]'

# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/nephele-hms-tg/1234567890123456
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Provider not available"

**Error:** `No valid credential sources found`

**Solution:**
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"

# Verify credentials
aws sts get-caller-identity
```

#### Issue 2: "VPC CIDR already exists"

**Error:** `Error creating VPC: VpcLimitExceeded`

**Solution:**
```bash
# Check existing VPCs
aws ec2 describe-vpcs

# Choose a different CIDR block
# Edit terraform/environments/prod.tfvars:
# vpc_cidr = "10.2.0.0/16"  # Change this
```

#### Issue 3: "RDS password doesn't work"

**Error:** `password authentication failed`

**Solution:**
```bash
# Retrieve password from Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id nephele-hms/rds/password \
  --query 'SecretString' | jq -r '.password'

# Use this password to connect
psql -h <rds-endpoint> -U postgres -d hotel_management_system
```

#### Issue 4: "ECS tasks failing to start"

**Error:** `CannotPullContainerImage`

**Solution:**
```bash
# Check ECR image exists
aws ecr describe-images \
  --repository-name nephele-hms-app

# Push image to ECR
ECR_REPO=$(cd terraform && terraform output -raw ecr_repository_url)
docker tag hms:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

# Force ECS task update
aws ecs update-service --cluster nephele-hms-cluster \
  --service nephele-hms-service --force-new-deployment
```

#### Issue 5: "ALB returning 502 Bad Gateway"

**Error:** Application Load Balancer returns 502 errors

**Solution:**
```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# Check ECS task logs
aws logs tail /ecs/nephele-hms --follow

# Check security group rules
aws ec2 describe-security-groups \
  --group-ids sg-xxxxxxxx \
  --query 'SecurityGroups[0].IpPermissions'
```

#### Issue 6: "Terraform state lock timeout"

**Error:** `Error acquiring the state lock`

**Solution:**
```bash
# List DynamoDB lock table items
aws dynamodb scan --table-name nephele-hms-terraform-locks

# Force unlock (use with caution!)
cd terraform
terraform force-unlock <LOCK-ID>

# Then retry the operation
```

### Debug Terraform

```bash
# Enable debug logging
export TF_LOG=DEBUG
make tf-plan-dev

# Disable debug logging
unset TF_LOG

# Graph infrastructure dependencies
cd terraform
terraform graph > graph.txt
# Convert to image: dot -Tpng graph.txt -o graph.png
```

### Verify AWS Resources

```bash
# List all resources created by this Terraform
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=ManagedBy,Values=Terraform

# Get specific resource details
aws ec2 describe-vpcs --filters Name=tag:Project,Values=nephele-hms
aws rds describe-db-instances
aws ecs list-clusters
aws ecr describe-repositories
```

---

## 🔗 Integration with Gap #2

### Database Backup Strategy

The Terraform infrastructure sets up automated RDS backups. Gap #2 scripts provide additional manual and export capabilities:

#### RDS Automated Backups

Configured by Terraform:
- **Retention:** 7 days (dev), 14 days (staging), 30 days (prod)
- **Backup Window:** 03:00-04:00 UTC
- **Backup Type:** Full daily backups with automatic snapshots

#### S3 Export Backups

Set up by Gap #2 scripts:
- **Bucket:** `nephele-hms-backups-{account-id}`
- **Location:** `s3://nephele-hms-backups-{account-id}/exports/`
- **Lifecycle:** 30-90 day retention, then archive

#### Integration Commands

```bash
# Get RDS credentials from Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id nephele-hms/rds/password \
  --query 'SecretString' | jq .

# Get database endpoint from Terraform outputs
RDS_ENDPOINT=$(cd terraform && terraform output -raw rds_endpoint)

# Use with Gap #2 backup scripts
export DATABASE_HOST=$RDS_ENDPOINT
export DATABASE_USER=postgres
export DATABASE_PASSWORD=$(aws secretsmanager get-secret-value --secret-id nephele-hms/rds/password --query 'SecretString' | jq -r '.password')

# Run backup
bash scripts/backup-daily.sh

# Verify backup in S3
aws s3 ls s3://nephele-hms-backups-{account-id}/exports/ --recursive
```

### Disaster Recovery Procedure

```bash
# 1. Launch alternative RDS instance via Terraform
make tf-apply-staging  # Create staging environment with clean RDS

# 2. Restore database from backup
export DATABASE_HOST=$(aws rds describe-db-instances \
  --db-instance-identifier nephele-hms-db \
  --query 'DBInstances[0].Endpoint.Address' --output text)

bash scripts/restore-latest.sh

# 3. Update ECS to point to new database
# (Update environment variables in task definition)

# 4. Verify data
aws ecs update-service --cluster nephele-hms-cluster \
  --service nephele-hms-service --force-new-deployment
```

---

## 📝 Additional Resources

### Documentation Files

- [DATABASE_BACKUP_GUIDE.md](../DATABASE_BACKUP_GUIDE.md) - Backup and recovery procedures
- [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md) - Pre-deployment verification
- [PRODUCTION_READINESS_ROADMAP.md](../PRODUCTION_READINESS_ROADMAP.md) - Overall project roadmap

### Terraform Official Documentation

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Language](https://www.terraform.io/docs/language)
- [Best Practices](https://www.terraform.io/docs/terraform/best-practices)

### AWS Resources

- [AWS Architecture Center](https://aws.amazon.com/architecture/)
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/)
- [RDS Documentation](https://docs.aws.amazon.com/rds/)
- [ECS Documentation](https://docs.aws.amazon.com/ecs/)

---

## 📞 Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `aws logs tail /ecs/nephele-hms --follow`
3. Check resource status: `make tf-output`
4. Review Terraform state: `cd terraform && terraform show`

---

**Last Updated:** 2024  
**Version:** 1.0.0  
**Status:** Production Ready ✅
