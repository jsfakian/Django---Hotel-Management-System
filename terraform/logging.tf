# Advanced Logging Infrastructure (Gap #9)
# Elasticsearch, Logstash, Kibana (ELK Stack) + Log Aggregation
# Centralized logging for all application, infrastructure, and security events

# ==============================================================================
# ELASTICSEARCH DOMAIN CONFIGURATION
# ==============================================================================

resource "aws_elasticsearch_domain" "logging" {
  count           = var.enable_elasticsearch ? 1 : 0
  domain_name     = "nephele-hms-${var.environment}"
  engine_version  = var.elasticsearch_version

  cluster_config {
    instance_type            = var.elasticsearch_instance_type
    instance_count           = var.elasticsearch_instance_count
    dedicated_master_enabled = var.elasticsearch_instance_count > 1
    dedicated_master_type    = var.elasticsearch_instance_count > 1 ? var.elasticsearch_master_type : null
    dedicated_master_count   = var.elasticsearch_instance_count > 1 ? 3 : null
    zone_awareness_enabled   = var.elasticsearch_instance_count > 1
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = var.elasticsearch_ebs_volume_size
  }

  encryption_at_rest {
    enabled    = true
    kms_key_id = var.kms_key_id
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "logstash.amazonaws.com"
        }
        Action = [
          "es:*"
        ]
        Resource = "arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/nephele-hms-${var.environment}/*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "masterdata.elasticsearch.amazonaws.com"
        }
        Action = [
          "es:DescribeElasticsearchDomain",
          "es:DescribeElasticsearchDomainConfig",
          "es:DescribeElasticsearchDomains",
          "es:DescribeElasticsearchInstanceTypeLimits",
          "es:ListDomainNames",
          "es:ListElasticsearchInstanceTypes",
          "es:ListElasticsearchVersions",
          "es:GetCompatibleElasticsearchVersions"
        ]
        Resource = "*"
      }
    ]
  })

  log_publishing_options {
    cloudwatch_log_group_arn = aws_cloudwatch_log_group.elasticsearch_app_logs[0].arn
    enabled                  = true
    log_type                 = "ES_APPLICATION_LOGS"
    log_format               = "JSON"
  }

  advanced_options = {
    "indices.fielddata.cache.size"           = "25"
    "indices.memory.index_buffer_size"       = "30"
    "rest.action.multi.allow_explicit_index" = "true"
  }

  enabled_log_types = [
    "ES_APPLICATION_LOGS",
    "INDEX_SLOW_LOGS",
    "SEARCH_SLOW_LOGS"
  ]

  depends_on = [
    aws_cloudwatch_log_resource_policy.elasticsearch_logs
  ]

  tags = {
    Name        = "nephele-hms-elasticsearch"
    Environment = var.environment
    Gap         = "Gap9"
  }
}

# ==============================================================================
# CLOUDWATCH LOG GROUPS FOR ELASTICSEARCH
# ==============================================================================

resource "aws_cloudwatch_log_group" "elasticsearch_app_logs" {
  count             = var.enable_elasticsearch ? 1 : 0
  name              = "/aws/elasticsearch/nephele-hms/${var.environment}/app-logs"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "elasticsearch-app-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "elasticsearch_index_slow_logs" {
  count             = var.enable_elasticsearch ? 1 : 0
  name              = "/aws/elasticsearch/nephele-hms/${var.environment}/index-slow-logs"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "elasticsearch-index-slow-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "elasticsearch_search_slow_logs" {
  count             = var.enable_elasticsearch ? 1 : 0
  name              = "/aws/elasticsearch/nephele-hms/${var.environment}/search-slow-logs"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "elasticsearch-search-slow-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_resource_policy" "elasticsearch_logs" {
  policy_name = "elasticsearch-logs-policy-${var.environment}"

  policy_document = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "es.amazonaws.com"
        }
        Action   = "logs:PutLogEvents"
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/elasticsearch/*"
      }
    ]
  })
}

# ==============================================================================
# KIBANA WORKSPACE (OPTIONAL)
# ==============================================================================

resource "aws_kibana_instance" "logging" {
  count                = var.enable_kibana ? 1 : 0
  instance_type        = var.kibana_instance_type
  availability_zone_id = var.availability_zone

  # Note: Kibana is integrated with Elasticsearch domain in AWS
  # Accessible via: https://<es-domain>.region.es.amazonaws.com/_plugin/kibana/
}

# ==============================================================================
# LOG AGGREGATION FOR CLOUDWATCH LOGS
# ==============================================================================

# Log group for application logs
resource "aws_cloudwatch_log_group" "application_logs" {
  name              = "/ecs/nephele-hms/${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "application-logs"
    Environment = var.environment
  }
}

# Log group for WAF logs (if not already created in Gap #8)
resource "aws_cloudwatch_log_group" "waf_logs" {
  count             = var.enable_waf_logging ? 1 : 0
  name              = "/aws/waf/nephele-hms/${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "waf-logs"
    Environment = var.environment
  }
}

# Log group for RDS logs
resource "aws_cloudwatch_log_group" "rds_logs" {
  name              = "/aws/rds/nephele-hms/${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "rds-logs"
    Environment = var.environment
  }
}

# Log group for ALB access logs (optional)
resource "aws_cloudwatch_log_group" "alb_logs" {
  count             = var.enable_alb_logging ? 1 : 0
  name              = "/aws/alb/nephele-hms/${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "alb-logs"
    Environment = var.environment
  }
}

# Log group for VPC Flow Logs (optional)
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  count             = var.enable_vpc_flow_logs ? 1 : 0
  name              = "/aws/vpc/nephele-hms/${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "vpc-flow-logs"
    Environment = var.environment
  }
}

# ==============================================================================
# KINESIS FIREHOSE FOR LOG STREAMING (Elasticsearch Delivery)
# ==============================================================================

resource "aws_kinesis_firehose_delivery_stream" "logs_to_elasticsearch" {
  count           = var.enable_elasticsearch ? 1 : 0
  name            = "nephele-hms-logs-to-es-${var.environment}"
  destination     = "elasticsearch"
  s3_destination_arn = aws_s3_bucket.elasticsearch_backups[0].arn
  iam_role_arn    = aws_iam_role.firehose_role[0].arn

  elasticsearch_configuration {
    domain_arn            = aws_elasticsearch_domain.logging[0].arn
    role_arn              = aws_iam_role.firehose_role[0].arn
    index_name            = "nephele-logs-%{timestamp:yyyy-MM-dd}"
    index_rotation_period = "OneDay"
    type_name             = "_doc"
    buffering_size        = 100
    buffering_interval    = 60
    retry_duration        = 3600

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose_logs[0].name
      log_stream_name = "S3Delivery"
    }

    processing_configuration {
      enabled = true

      processors {
        type = "Lambda"

        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = aws_lambda_function.log_processor[0].arn
        }
      }
    }
  }

  cloudwatch_logging_options {
    enabled         = true
    log_group_name  = aws_cloudwatch_log_group.firehose_logs[0].name
    log_stream_name = "DestinationDelivery"
  }

  s3_configuration {
    role_arn           = aws_iam_role.firehose_role[0].arn
    bucket_arn         = aws_s3_bucket.elasticsearch_backups[0].arn
    prefix             = "failover/"
    error_output_prefix = "errors/result=!{firehose:error-output-type}/!{timestamp:yyyy/MM/dd}/"
    buffer_size        = 5
    buffer_interval    = 300
    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose_logs[0].name
      log_stream_name = "S3Delivery"
    }
  }

  tags = {
    Name        = "logs-firehose"
    Environment = var.environment
  }
}

# ==============================================================================
# LAMBDA FUNCTION FOR LOG PROCESSING (Transformation)
# ==============================================================================

resource "aws_lambda_function" "log_processor" {
  count         = var.enable_elasticsearch ? 1 : 0
  filename      = "lambda_log_processor.zip"
  function_name = "nephele-hms-log-processor-${var.environment}"
  role          = aws_iam_role.lambda_log_processor[0].arn
  handler       = "index.handler"
  runtime       = "python3.9"
  timeout       = 60

  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }

  tags = {
    Name        = "log-processor"
    Environment = var.environment
  }
}

# ==============================================================================
# S3 BUCKET FOR ELASTICSEARCH BACKUPS
# ==============================================================================

resource "aws_s3_bucket" "elasticsearch_backups" {
  count  = var.enable_elasticsearch ? 1 : 0
  bucket = "nephele-hms-es-backups-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "elasticsearch-backups"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "elasticsearch_backups" {
  count  = var.enable_elasticsearch ? 1 : 0
  bucket = aws_s3_bucket.elasticsearch_backups[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "elasticsearch_backups" {
  count  = var.enable_elasticsearch ? 1 : 0
  bucket = aws_s3_bucket.elasticsearch_backups[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id
    }
  }
}

# ==============================================================================
# IAM ROLES FOR FIREHOSE AND LAMBDA
# ==============================================================================

resource "aws_iam_role" "firehose_role" {
  count = var.enable_elasticsearch ? 1 : 0
  name  = "nephele-hms-firehose-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "firehose.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "firehose-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "firehose_policy" {
  count  = var.enable_elasticsearch ? 1 : 0
  name   = "firehose-policy"
  role   = aws_iam_role.firehose_role[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "es:DescribeElasticsearchDomain",
          "es:DescribeElasticsearchDomainConfig",
          "es:ESHttpPut",
          "es:ESHttpPost"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject",
          "s3:GetObjectVersion"
        ]
        Resource = [
          aws_s3_bucket.elasticsearch_backups[0].arn,
          "${aws_s3_bucket.elasticsearch_backups[0].arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.log_processor[0].arn
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = var.kms_key_id
      }
    ]
  })
}

resource "aws_iam_role" "lambda_log_processor" {
  count = var.enable_elasticsearch ? 1 : 0
  name  = "nephele-hms-lambda-log-processor-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "lambda-log-processor"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  count              = var.enable_elasticsearch ? 1 : 0
  role               = aws_iam_role.lambda_log_processor[0].name
  policy_arn         = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ==============================================================================
# CLOUDWATCH LOG GROUP FOR FIREHOSE
# ==============================================================================

resource "aws_cloudwatch_log_group" "firehose_logs" {
  count             = var.enable_elasticsearch ? 1 : 0
  name              = "/aws/kinesisfirehose/nephele-hms/${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "firehose-logs"
    Environment = var.environment
  }
}

# ==============================================================================
# CLOUDWATCH ALARMS FOR LOGGING
# ==============================================================================

resource "aws_cloudwatch_metric_alarm" "elasticsearch_cluster_health" {
  count               = var.enable_elasticsearch ? 1 : 0
  alarm_name          = "nephele-hms-elasticsearch-cluster-health"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "UnreachableNodeCount"
  namespace           = "AWS/ES"
  period              = 300
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "Alert when Elasticsearch cluster has unreachable nodes"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DomainName = aws_elasticsearch_domain.logging[0].domain_name
  }
}

resource "aws_cloudwatch_metric_alarm" "elasticsearch_storage" {
  count               = var.enable_elasticsearch ? 1 : 0
  alarm_name          = "nephele-hms-elasticsearch-storage-full"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "StorageSpaceUsed"
  namespace           = "AWS/ES"
  period              = 300
  statistic           = "Average"
  threshold           = var.elasticsearch_storage_threshold
  alarm_description   = "Alert when Elasticsearch storage is above threshold"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DomainName = aws_elasticsearch_domain.logging[0].domain_name
  }
}

resource "aws_cloudwatch_metric_alarm" "elasticsearch_indexing_rate" {
  count               = var.enable_elasticsearch ? 1 : 0
  alarm_name          = "nephele-hms-elasticsearch-high-indexing"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "IndexingRate"
  namespace           = "AWS/ES"
  period              = 300
  statistic           = "Average"
  threshold           = 5000  # Documents per second
  alarm_description   = "Alert when Elasticsearch indexing rate is unusually high"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DomainName = aws_elasticsearch_domain.logging[0].domain_name
  }
}

# ==============================================================================
# OUTPUTS
# ==============================================================================

output "elasticsearch_domain_endpoint" {
  description = "Elasticsearch domain endpoint URL"
  value       = var.enable_elasticsearch ? aws_elasticsearch_domain.logging[0].endpoint : ""
}

output "elasticsearch_kibana_url" {
  description = "Kibana dashboard URL"
  value       = var.enable_elasticsearch ? "https://${aws_elasticsearch_domain.logging[0].endpoint}/_plugin/kibana/" : ""
}

output "firehose_delivery_stream_name" {
  description = "Kinesis Firehose delivery stream for logs"
  value       = var.enable_elasticsearch ? aws_kinesis_firehose_delivery_stream.logs_to_elasticsearch[0].name : ""
}

output "elasticsearch_backups_bucket" {
  description = "S3 bucket for Elasticsearch backups"
  value       = var.enable_elasticsearch ? aws_s3_bucket.elasticsearch_backups[0].id : ""
}

output "application_logs_group" {
  description = "CloudWatch log group for application logs"
  value       = aws_cloudwatch_log_group.application_logs.name
}

output "logging_summary" {
  description = "Summary of logging infrastructure"
  value = {
    elasticsearch_enabled = var.enable_elasticsearch
    log_retention_days    = var.log_retention_days
    log_groups_created    = var.enable_elasticsearch ? 6 : 4
    firehose_enabled      = var.enable_elasticsearch
    alarms_created        = var.enable_elasticsearch ? 3 : 0
  }
}
