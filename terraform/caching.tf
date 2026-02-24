# Gap #7: Redis Caching Layer - ElastiCache Configuration
# Purpose: High-performance in-memory caching for sessions, queries, and frequently accessed data
# Impact: 200-400% performance improvement for cacheable operations

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ============================================================================
# ELASTICACHE REDIS CLUSTER - Primary Cache Layer
# ============================================================================

# Security group for Redis access from ECS tasks
resource "aws_security_group" "redis" {
  name_prefix = "nephele-hms-redis-"
  description = "Security group for ElastiCache Redis cluster"
  vpc_id      = var.vpc_id

  # Inbound: Allow Redis traffic from ECS tasks
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
    description     = "Redis from ECS tasks"
  }

  # Outbound: Full internet access (for DNS, package downloads)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "nephele-hms-redis"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ElastiCache subnet group (must span multiple AZs for high availability)
resource "aws_elasticache_subnet_group" "redis" {
  name       = "nephele-hms-redis-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "nephele-hms-redis-subnet-group"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Primary Redis Cluster (with replication if enabled)
resource "aws_elasticache_cluster" "redis" {
  count = var.enable_redis_caching ? 1 : 0

  cluster_id           = "nephele-hms-redis-${var.environment}"
  engine               = "redis"
  node_type           = var.redis_node_type           # t4g.micro, t4g.small, cache.t4g.medium, etc
  num_cache_nodes     = var.redis_num_nodes           # 1 for dev, 2+ for HA
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  engine_version      = var.redis_engine_version      # 7.0, 7.1, etc
  port                = 6379
  subnet_group_name   = aws_elasticache_subnet_group.redis.name
  security_group_ids  = [aws_security_group.redis.id]

  # Automated failover for multi-node clusters
  automatic_failover_enabled = var.redis_num_nodes > 1 ? true : false

  # Multi-AZ for high availability
  multi_az_enabled = var.redis_enable_multi_az

  # Backup configuration
  snapshot_retention_limit = var.redis_snapshot_retention_days
  snapshot_window          = "03:00-05:00"  # UTC time window
  maintenance_window       = "sun:05:00-sun:07:00"

  # Encryption at rest (if enabled)
  at_rest_encryption_enabled = var.enable_redis_encryption
  auth_token                 = var.enable_redis_encryption ? random_password.redis_auth_token[0].result : null
  auth_token_enable          = var.enable_redis_encryption

  # Encryption in transit
  transit_encryption_enabled = var.enable_redis_encryption
  transit_encryption_mode    = var.enable_redis_encryption ? "preferred" : null

  # Performance and memory optimization
  # Eviction policy: allkeys-lru = evict any key when memory full
  num_cache_nodes = var.redis_num_nodes

  # Notifications
  notification_topic_arn = var.enable_redis_notifications ? aws_sns_topic.redis_events[0].arn : null

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow_log[0].name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
    enabled          = true
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_engine_log[0].name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "engine-log"
    enabled          = true
  }

  # Allow automatic minor version upgrades
  auto_minor_version_upgrade = true

  # Preserve data during upgrades
  apply_immediately = false

  tags = {
    Name        = "nephele-hms-redis"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  depends_on = [
    aws_elasticache_parameter_group.redis,
    aws_security_group.redis
  ]
}

# ============================================================================
# REDIS PARAMETER GROUP - Performance Tuning
# ============================================================================

resource "aws_elasticache_parameter_group" "redis" {
  family = "redis${split(".", var.redis_engine_version)[0]}"
  name   = "nephele-hms-redis-params-${var.environment}"

  # Memory management
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"  # Evict least recently used when memory full
  }

  # Slow log threshold (microseconds)
  parameter {
    name  = "slowlog-log-slower-than"
    value = "10000"  # Log queries slower than 10ms
  }

  parameter {
    name  = "slowlog-max-len"
    value = "1000"  # Keep 1000 slow log entries
  }

  # Connection settings
  parameter {
    name  = "timeout"
    value = "300"  # Close idle connections after 5 min
  }

  parameter {
    name  = "tcp-keepalive"
    value = "300"  # keepalive for TCP connections
  }

  # Database settings
  parameter {
    name  = "databases"
    value = var.redis_num_databases  # default: 16
  }

  # Client output buffer limits
  parameter {
    name  = "client-output-buffer-limit-normal-hard-limit"
    value = "0"  # Unlimited for normal clients
  }

  parameter {
    name  = "client-output-buffer-limit-pubsub-hard-limit"
    value = "33554432"  # 32MB for pub/sub
  }

  # Append-only file (AOF) disabled for performance
  # (RDS snapshots handle durability)

  tags = {
    Name        = "nephele-hms-redis-params"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ============================================================================
# REDIS AUTHENTICATION & ENCRYPTION
# ============================================================================

# Generate secure auth token for Redis
resource "random_password" "redis_auth_token" {
  count   = var.enable_redis_encryption ? 1 : 0
  length  = 32
  special = true
}

# Store auth token in Secrets Manager
resource "aws_secretsmanager_secret" "redis_auth_token" {
  count                   = var.enable_redis_encryption ? 1 : 0
  name                    = "nephele-hms/redis/auth-token-${var.environment}"
  description             = "ElastiCache Redis authentication token"
  recovery_window_in_days = 7

  tags = {
    Name        = "nephele-hms-redis-auth-token"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  count         = var.enable_redis_encryption ? 1 : 0
  secret_id     = aws_secretsmanager_secret.redis_auth_token[0].id
  secret_string = random_password.redis_auth_token[0].result
}

# ============================================================================
# CLOUDWATCH LOGS FOR REDIS
# ============================================================================

resource "aws_cloudwatch_log_group" "redis_slow_log" {
  count             = var.enable_redis_monitoring ? 1 : 0
  name              = "/aws/elasticache/nephele-hms/slow-log"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "nephele-hms-redis-slow-log"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_cloudwatch_log_group" "redis_engine_log" {
  count             = var.enable_redis_monitoring ? 1 : 0
  name              = "/aws/elasticache/nephele-hms/engine-log"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "nephele-hms-redis-engine-log"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ============================================================================
# REDIS MONITORING & ALERTS
# ============================================================================

# SNS topic for Redis events
resource "aws_sns_topic" "redis_events" {
  count = var.enable_redis_notifications ? 1 : 0
  name  = "nephele-hms-redis-events-${var.environment}"

  tags = {
    Name        = "nephele-hms-redis-events"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# CloudWatch Alarms for Redis monitoring
resource "aws_cloudwatch_metric_alarm" "redis_cpu_high" {
  count = var.enable_redis_caching && var.enable_critical_alarms ? 1 : 0

  alarm_name          = "nephele-hms-redis-cpu-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = var.redis_alarm_cpu_threshold
  alarm_description   = "Alert when Redis CPU exceeds ${var.redis_alarm_cpu_threshold}%"
  alarm_actions       = var.enable_critical_alarms ? [var.sns_topic_arn] : []

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis[0].cluster_id
  }

  tags = {
    Name        = "nephele-hms-redis-cpu-alarm"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory_high" {
  count = var.enable_redis_caching && var.enable_critical_alarms ? 1 : 0

  alarm_name          = "nephele-hms-redis-memory-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = var.redis_alarm_memory_threshold
  alarm_description   = "Alert when Redis memory exceeds ${var.redis_alarm_memory_threshold}%"
  alarm_actions       = var.enable_critical_alarms ? [var.sns_topic_arn] : []

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis[0].cluster_id
  }

  tags = {
    Name        = "nephele-hms-redis-memory-alarm"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_evictions" {
  count = var.enable_redis_caching && var.enable_critical_alarms ? 1 : 0

  alarm_name          = "nephele-hms-redis-evictions-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Sum"
  threshold           = 100  # More than 100 evictions per 5 min
  alarm_description   = "Alert when Redis is evicting keys (memory pressure)"
  alarm_actions       = var.enable_critical_alarms ? [var.sns_topic_arn] : []

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis[0].cluster_id
  }

  tags = {
    Name        = "nephele-hms-redis-evictions-alarm"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ============================================================================
# OUTPUTS FOR APPLICATION USE
# ============================================================================

output "redis_endpoint" {
  description = "Redis cluster endpoint (host:port)"
  value       = var.enable_redis_caching ? "${aws_elasticache_cluster.redis[0].cache_nodes[0].address}:${aws_elasticache_cluster.redis[0].port}" : null
}

output "redis_host" {
  description = "Redis host address"
  value       = var.enable_redis_caching ? aws_elasticache_cluster.redis[0].cache_nodes[0].address : null
}

output "redis_port" {
  description = "Redis port"
  value       = var.enable_redis_caching ? aws_elasticache_cluster.redis[0].port : null
}

output "redis_auth_token_secret_arn" {
  description = "ARN of the Redis auth token in Secrets Manager"
  value       = var.enable_redis_encryption ? aws_secretsmanager_secret.redis_auth_token[0].arn : null
  sensitive   = true
}

output "redis_cluster_id" {
  description = "Redis cluster identifier"
  value       = var.enable_redis_caching ? aws_elasticache_cluster.redis[0].cluster_id : null
}

output "redis_engine_version" {
  description = "Redis engine version"
  value       = var.enable_redis_caching ? aws_elasticache_cluster.redis[0].engine_version_actual : null
}

output "redis_node_type" {
  description = "Redis node type"
  value       = var.enable_redis_caching ? aws_elasticache_cluster.redis[0].node_type : null
}

output "redis_num_nodes" {
  description = "Number of Redis nodes"
  value       = var.enable_redis_caching ? aws_elasticache_cluster.redis[0].num_cache_nodes : null
}

output "redis_multi_az_enabled" {
  description = "Whether Multi-AZ is enabled"
  value       = var.enable_redis_caching ? aws_elasticache_cluster.redis[0].multi_az_enabled : null
}

output "redis_slowlog_group" {
  description = "CloudWatch log group for Redis slow log"
  value       = var.enable_redis_monitoring ? aws_cloudwatch_log_group.redis_slow_log[0].name : null
}

output "redis_engine_log_group" {
  description = "CloudWatch log group for Redis engine log"
  value       = var.enable_redis_monitoring ? aws_cloudwatch_log_group.redis_engine_log[0].name : null
}
