# RDS DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name            = "${var.project_name}-db-subnet-group"
  subnet_ids      = aws_subnet.private[*].id
  skip_final_snapshot = false

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

# RDS Instance Password (generate random password)
resource "random_password" "rds_password" {
  length  = 32
  special = true
}

# Secrets Manager Secret for RDS Password
resource "aws_secretsmanager_secret" "rds_password" {
  name                    = "${var.project_name}/rds/password"
  rotation_rules {
    automatically_after_days = 30
  }

  tags = {
    Name = "${var.project_name}-rds-password"
  }
}

resource "aws_secretsmanager_secret_version" "rds_password" {
  secret_id = aws_secretsmanager_secret.rds_password.id
  secret_string = jsonencode({
    username = var.rds_database_username
    password = random_password.rds_password.result
    engine   = var.rds_engine
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    dbname   = var.rds_database_name
  })
}

# CloudWatch Log Group for RDS
resource "aws_cloudwatch_log_group" "rds" {
  name              = "/aws/rds/instance/${var.project_name}"
  retention_in_days = var.cloudwatch_log_retention_days

  tags = {
    Name = "${var.project_name}-rds-logs"
  }
}

# Enhanced Monitoring IAM Role
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project_name}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
  role       = aws_iam_role.rds_monitoring.name
}

# RDS Instance - Primary
resource "aws_db_instance" "main" {
  identifier            = "${var.project_name}-db"
  engine                = var.rds_engine
  engine_version        = var.rds_engine_version
  instance_class        = var.rds_instance_class
  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = var.rds_enable_encryption
  
  db_name             = var.rds_database_name
  username            = var.rds_database_username
  password            = random_password.rds_password.result
  parameter_group_name = aws_db_parameter_group.main.name
  db_subnet_group_name = aws_db_subnet_group.main.name
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  multi_az                      = var.rds_multi_az
  skip_final_snapshot           = false
  final_snapshot_identifier     = "${var.project_name}-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  backup_retention_period       = var.rds_backup_retention_days
  backup_window                 = "03:00-04:00"
  maintenance_window            = "sun:04:00-sun:05:00"
  deletion_protection           = var.environment == "prod" ? true : false
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  enable_iam_database_authentication = true
  enable_http_endpoint             = false
  
  # Performance Insights
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  
  # Enhanced Monitoring
  monitoring_interval             = 60
  monitoring_role_arn             = aws_iam_role.rds_monitoring.arn
  
  # Automated backups and Point-in-Time Recovery
  copy_tags_to_snapshot = true
  
  tags = {
    Name = "${var.project_name}-db-primary"
  }

  depends_on = [
    aws_db_subnet_group.main,
    aws_cloudwatch_log_group.rds
  ]
}

# RDS Parameter Group (PostgreSQL customization)
resource "aws_db_parameter_group" "main" {
  name   = "${var.project_name}-pg-params"
  family = "postgres15"

  # Connection settings
  parameter {
    name  = "max_connections"
    value = var.environment == "prod" ? "200" : "100"
  }

  # Logging
  parameter {
    name  = "log_statement"
    value = var.environment == "prod" ? "all" : "ddl"
  }

  parameter {
    name  = "log_duration"
    value = "1"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  # Performance
  parameter {
    name  = "shared_buffers"
    value = "{DBInstanceClassMemory/32768}"
  }

  parameter {
    name  = "effective_cache_size"
    value = "{DBInstanceClassMemory/2048}"
  }

  tags = {
    Name = "${var.project_name}-pg-params"
  }
}

# S3 Bucket for RDS and Application Backups
resource "aws_s3_bucket" "backups" {
  count  = var.enable_s3_backup ? 1 : 0
  bucket = var.s3_backup_bucket_name != "" ? var.s3_backup_bucket_name : "${var.project_name}-backups-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-backups"
  }
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "backups" {
  count  = var.enable_s3_backup ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  count  = var.enable_s3_backup ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Lifecycle Policy (archive old backups)
resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  count  = var.enable_s3_backup ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id

  rule {
    id     = "archive-old-backups"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "GLACIER"
    }

    transition {
      days          = 90
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = var.backup_retention_days
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "backups" {
  count  = var.enable_s3_backup ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Policy for RDS Backup to S3
resource "aws_iam_role" "rds_backup_s3" {
  count = var.enable_s3_backup ? 1 : 0
  name  = "${var.project_name}-rds-backup-s3-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "rds_backup_s3" {
  count = var.enable_s3_backup ? 1 : 0
  name  = "${var.project_name}-rds-backup-s3-policy"
  role  = aws_iam_role.rds_backup_s3[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          aws_s3_bucket.backups[0].arn,
          "${aws_s3_bucket.backups[0].arn}/*"
        ]
      }
    ]
  })
}

# CloudWatch Alarm for RDS CPU
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.project_name}-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Alert when RDS CPU exceeds 80%"
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = {
    Name = "${var.project_name}-rds-cpu-alarm"
  }
}

# CloudWatch Alarm for RDS Storage
resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${var.project_name}-rds-high-storage"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "10737418240" # 10 GB in bytes
  alarm_description   = "Alert when RDS free storage is less than 10GB"
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = {
    Name = "${var.project_name}-rds-storage-alarm"
  }
}

# Data source for AWS caller identity
data "aws_caller_identity" "current" {}
