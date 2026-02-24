# Disaster Recovery & High Availability (Gap #10)
# Multi-region deployment, automatic failover, RTO/RPO targets

# ==============================================================================
# ROUTE 53 HEALTH CHECKS & FAILOVER
# ==============================================================================

resource "aws_route53_health_check" "primary_region" {
  count             = var.enable_dr ? 1 : 0
  ip_address        = var.primary_alb_ip
  port              = 443
  type              = "HTTPS"
  failure_threshold = 3
  request_interval  = 10
  measure_latency   = true
  tags = {
    Name   = "primary-region-health"
    Region = var.primary_region
  }
}

resource "aws_route53_health_check" "secondary_region" {
  count             = var.enable_dr ? 1 : 0
  ip_address        = var.secondary_alb_ip
  port              = 443
  type              = "HTTPS"
  failure_threshold = 3
  request_interval  = 10
  measure_latency   = true
  tags = {
    Name   = "secondary-region-health"
    Region = var.secondary_region
  }
}

# ==============================================================================
# ROUTE 53 FAILOVER POLICY
# ==============================================================================

resource "aws_route53_record" "failover_primary" {
  count              = var.enable_dr ? 1 : 0
  zone_id            = var.route53_zone_id
  name               = var.domain_name
  type               = "A"
  alias {
    name                   = var.primary_alb_dns
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
  failover_routing_policy {
    type = "PRIMARY"
  }
  set_identifier = "primary-${var.primary_region}"

  depends_on = [aws_route53_health_check.primary_region]
}

resource "aws_route53_record" "failover_secondary" {
  count              = var.enable_dr ? 1 : 0
  zone_id            = var.route53_zone_id
  name               = var.domain_name
  type               = "A"
  alias {
    name                   = var.secondary_alb_dns
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
  failover_routing_policy {
    type = "SECONDARY"
  }
  set_identifier = "secondary-${var.secondary_region}"

  depends_on = [aws_route53_health_check.secondary_region]
}

# ==============================================================================
# RDS CROSS-REGION READ REPLICA
# ==============================================================================

resource "aws_db_instance" "dr_replica" {
  count                 = var.enable_rds_dr ? 1 : 0
  identifier            = "${var.db_instance_identifier}-dr"
  replicate_source_db   = var.source_db_id
  skip_final_snapshot   = var.environment != "prod"
  publicly_accessible   = false
  multi_az              = var.db_multi_az
  storage_encrypted     = true
  kms_key_id            = var.kms_key_id
  enable_cloudwatch_logs_exports = [
    "postgresql"
  ]

  # Backup for disaster recovery
  backup_retention_period = 35
  backup_window           = "02:00-03:00"
  copy_tags_to_snapshot   = true

  tags = {
    Name   = "rds-dr-replica"
    Region = var.secondary_region
  }
}

# ==============================================================================
# S3 CROSS-REGION REPLICATION
# ==============================================================================

resource "aws_s3_bucket_replication_configuration" "dr_replication" {
  count      = var.enable_s3_dr ? 1 : 0
  depends_on = [aws_s3_bucket_versioning.source]
  bucket     = var.source_bucket_id

  role = aws_iam_role.s3_replication_role[0].arn

  rule {
    id     = "cross-region-replication"
    status = "Enabled"

    filter {
      prefix = ""
    }

    destination {
      bucket       = var.destination_bucket_arn
      region       = var.secondary_region
      storage_class = "STANDARD_IA"

      replication_time {
        status = "Enabled"
        time {
          minutes = 15
        }
      }

      metrics {
        status = "Enabled"
        event_threshold {
          minutes = 15
        }
      }
    }
  }
}

resource "aws_s3_bucket_versioning" "source" {
  count  = var.enable_s3_dr ? 1 : 0
  bucket = var.source_bucket_id

  versioning_configuration {
    status = "Enabled"
  }
}

# ==============================================================================
# RDS AUTOMATED BACKUP & RESTORE
# ==============================================================================

resource "aws_backup_vault" "dr_vault" {
  count = var.enable_backup_vault ? 1 : 0
  name  = "nephele-hms-dr-vault-${var.environment}"

  tags = {
    Name = "dr-backup-vault"
  }
}

resource "aws_backup_plan" "dr_plan" {
  count = var.enable_backup_vault ? 1 : 0
  name  = "nephele-hms-dr-plan-${var.environment}"

  rule {
    rule_name         = "daily_backup"
    target_backup_vault_name = aws_backup_vault.dr_vault[0].name
    schedule          = "cron(0 2 * * ? *)"  # 2 AM UTC
    start_window      = 60
    completion_window = 120

    recovery_point_tags = {
      Environment = var.environment
      Type        = "Daily"
    }

    lifecycle {
      delete_after = 35  # 35-day retention
      cold_storage_after = 7
    }
  }

  rule {
    rule_name         = "weekly_backup"
    target_backup_vault_name = aws_backup_vault.dr_vault[0].name
    schedule          = "cron(0 3 ? * 1 *)"  # Every Monday 3 AM UTC
    start_window      = 60
    completion_window = 180

    recovery_point_tags = {
      Environment = var.environment
      Type        = "Weekly"
    }

    lifecycle {
      delete_after = 90
    }
  }

  rule {
    rule_name         = "monthly_backup"
    target_backup_vault_name = aws_backup_vault.dr_vault[0].name
    schedule          = "cron(0 4 1 * ? *)"  # 1st of month 4 AM UTC
    start_window      = 60
    completion_window = 240

    recovery_point_tags = {
      Environment = var.environment
      Type        = "Monthly"
    }

    lifecycle {
      delete_after = 365
    }
  }
}

resource "aws_backup_resource_assignment" "rds_backup" {
  count              = var.enable_backup_vault ? 1 : 0
  backup_plan_id     = aws_backup_plan.dr_plan[0].id
  iam_role_arn       = aws_iam_role.backup_role[0].arn
  resource_arn       = var.rds_arn

  depends_on = [aws_backup_plan.dr_plan]
}

# ==============================================================================
# ELASTICACHE CROSS-REGION REPLICATION
# ==============================================================================

resource "aws_elasticache_replication_group" "dr_replica" {
  count                       = var.enable_elasticache_dr ? 1 : 0
  replication_group_description = "DR replica of primary ElastiCache"
  primary_cluster_id          = var.primary_elasticache_cluster_id
  num_cache_clusters          = var.elasticache_replica_count
  automatic_failover_enabled  = true
  multi_az_enabled           = true
  node_type                   = var.elasticache_node_type
  engine_version              = var.elasticache_version
  parameter_group_name        = var.elasticache_parameter_group

  security_group_ids = [var.elasticache_security_group_id]
  subnet_group_name  = var.elasticache_subnet_group

  at_rest_encryption_enabled = true
  kms_key_id                = var.kms_key_id
  transit_encryption_enabled = true

  tags = {
    Name   = "elasticache-dr-replica"
    Region = var.secondary_region
  }
}

# ==============================================================================
# IAM ROLES FOR DR OPERATIONS
# ==============================================================================

resource "aws_iam_role" "s3_replication_role" {
  count = var.enable_s3_dr ? 1 : 0
  name  = "nephele-hms-s3-replication-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "s3_replication_policy" {
  count  = var.enable_s3_dr ? 1 : 0
  name   = "s3-replication-policy"
  role   = aws_iam_role.s3_replication_role[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Resource = var.source_bucket_arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Resource = "${var.source_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Resource = "${var.destination_bucket_arn}/*"
      }
    ]
  })
}

resource "aws_iam_role" "backup_role" {
  count = var.enable_backup_vault ? 1 : 0
  name  = "nephele-hms-backup-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "backup_policy" {
  count              = var.enable_backup_vault ? 1 : 0
  role               = aws_iam_role.backup_role[0].name
  policy_arn         = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

# ==============================================================================
# ECS CLUSTER AUTO-SCALING FOR DISASTER RECOVERY
# ==============================================================================

resource "aws_appautoscaling_target" "dr_scaling_target" {
  count              = var.enable_dr ? 1 : 0
  max_capacity       = var.dr_max_capacity
  min_capacity       = var.dr_min_capacity
  resource_id        = "service/${var.ecs_cluster_name}/${var.ecs_service_name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "dr_cpu_scaling" {
  count              = var.enable_dr ? 1 : 0
  policy_name        = "nephele-hms-dr-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.dr_scaling_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.dr_scaling_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.dr_scaling_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = var.dr_cpu_target
  }
}

# ==============================================================================
# OUTPUTS
# ==============================================================================

output "failover_domain" {
  description = "Domain with automatic failover"
  value       = var.enable_dr ? var.domain_name : ""
}

output "primary_region_health" {
  description = "Primary region health check ID"
  value       = var.enable_dr ? aws_route53_health_check.primary_region[0].id : ""
}

output "secondary_region_health" {
  description = "Secondary region health check ID"
  value       = var.enable_dr ? aws_route53_health_check.secondary_region[0].id : ""
}

output "rds_dr_endpoint" {
  description = "RDS DR read replica endpoint"
  value       = var.enable_rds_dr ? aws_db_instance.dr_replica[0].endpoint : ""
}

output "backup_vault_arn" {
  description = "AWS Backup vault for disaster recovery"
  value       = var.enable_backup_vault ? aws_backup_vault.dr_vault[0].arn : ""
}

output "dr_summary" {
  description = "Disaster recovery configuration summary"
  value = {
    primary_region              = var.primary_region
    secondary_region            = var.secondary_region
    rto_minutes                 = var.dr_rto_minutes
    rpo_hours                   = var.dr_rpo_hours
    failover_enabled            = var.enable_dr
    rds_dr_enabled              = var.enable_rds_dr
    s3_replication_enabled      = var.enable_s3_dr
    elasticache_dr_enabled      = var.enable_elasticache_dr
    backup_retention_days       = 35
    backup_frequency            = "Daily + Weekly + Monthly"
  }
}
