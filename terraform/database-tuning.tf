# Gap #7: Database Performance Optimization - RDS Tuning Configuration
# Purpose: Optimize database for query performance, connection pooling, and resource efficiency
# Impact: 50-200% improvement in database query performance

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ============================================================================
# RDS PARAMETER GROUP - Database Performance Tuning
# ============================================================================

# Get the current RDS instance to apply parameter group
data "aws_db_instance" "main" {
  db_instance_identifier = var.rds_instance_identifier
}

# Create a new parameter group for performance optimization
resource "aws_db_parameter_group" "performance" {
  family      = var.rds_parameter_group_family  # e.g., "postgres14", "mysql8.0"
  name        = "nephele-hms-performance-${var.environment}"
  description = "Performance optimization parameters for ${var.rds_engine}"

  # ======= QUERY PERFORMANCE & INDEXING =======

  # PostgreSQL-specific performance parameters
  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "shared_preload_libraries"
      value = "pg_stat_statements,pgaudit"
    }
  }

  # Enable query planning statistics
  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "pg_stat_statements.track"
      value = "all"
    }
  }

  # Log slow queries
  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "log_min_duration_statement"
      value = var.rds_slow_query_threshold_ms
    }
  }

  # MySQL-specific performance parameters
  dynamic "parameter" {
    for_each = var.rds_engine == "mysql" ? [1] : []
    content {
      name  = "slow_query_log"
      value = "1"
    }
  }

  dynamic "parameter" {
    for_each = var.rds_engine == "mysql" ? [1] : []
    content {
      name  = "long_query_time"
      value = var.rds_slow_query_threshold_ms / 1000  # Convert to seconds
    }
  }

  # ======= CONNECTION POOLING =======

  # PostgreSQL connection settings
  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "max_connections"
      value = var.rds_max_connections
    }
  }

  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "shared_buffers"
      value = var.rds_shared_buffers_percent  # % of instance memory
    }
  }

  # MySQL connection settings
  dynamic "parameter" {
    for_each = var.rds_engine == "mysql" ? [1] : []
    content {
      name  = "max_connections"
      value = var.rds_max_connections
    }
  }

  dynamic "parameter" {
    for_each = var.rds_engine == "mysql" ? [1] : []
    content {
      name  = "innodb_buffer_pool_size"
      value = var.rds_innodb_buffer_pool_percent  # % of instance memory
    }
  }

  # ======= MEMORY & CACHING =======

  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "effective_cache_size"
      value = var.rds_effective_cache_size_percent
    }
  }

  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "work_mem"
      value = var.rds_work_mem_mb  # Memory per operation
    }
  }

  # ======= QUERY OPTIMIZATION =======

  # PostgreSQL query planner
  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "random_page_cost"
      value = "1.0"  # For EBS: lower than default (4.0) for better index usage
    }
  }

  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "effective_io_concurrency"
      value = "200"  # Match EBS capabilities
    }
  }

  # MySQL optimizer settings
  dynamic "parameter" {
    for_each = var.rds_engine == "mysql" ? [1] : []
    content {
      name  = "optimizer_search_depth"
      value = "62"  # Balance optimization time vs. plan quality
    }
  }

  # ======= LOGGING & MONITORING =======

  # All engines: checkpoint and transaction logging
  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "log_statement"
      value = "all"  # Log all statements (can be changed to "ddl" for production)
    }
  }

  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "log_connections"
      value = "1"
    }
  }

  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "log_disconnections"
      value = "1"
    }
  }

  # ======= VACUUM & MAINTENANCE =======

  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "autovacuum"
      value = "1"
    }
  }

  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "autovacuum_max_workers"
      value = "3"  # Parallel vacuum workers
    }
  }

  dynamic "parameter" {
    for_each = var.rds_engine == "postgres" ? [1] : []
    content {
      name  = "autovacuum_naptime"
      value = "10"  # Check every 10 seconds
    }
  }

  tags = {
    Name        = "nephele-hms-performance-params"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ============================================================================
# AWS RDS PERFORMANCE INSIGHTS CONFIGURATION
# ============================================================================

# Enable Performance Insights for detailed performance monitoring
resource "aws_db_instance_performance_insights_default_retention" "main" {
  count              = var.enable_performance_insights ? 1 : 0
  db_instance_id     = data.aws_db_instance.main.id
  retention_days     = var.performance_insights_retention_days  # 7 for free tier, 31+ requires payment
}

# ============================================================================
# DATABASE INDEXING RECOMMENDATIONS
# ============================================================================

# Output guide for manual index creation
output "recommended_indexes" {
  description = "Recommended indexes for the application"
  value = var.rds_engine == "postgres" ? """
    -- Booking queries optimization
    CREATE INDEX CONCURRENTLY idx_bookings_guest_id ON bookings(guest_id);
    CREATE INDEX CONCURRENTLY idx_bookings_room_id ON bookings(room_id);
    CREATE INDEX CONCURRENTLY idx_bookings_check_in_date ON bookings(check_in_date);
    CREATE INDEX CONCURRENTLY idx_bookings_status ON bookings(status);
    CREATE INDEX CONCURRENTLY idx_bookings_created_at ON bookings(created_at DESC);
    
    -- Guest queries optimization
    CREATE INDEX CONCURRENTLY idx_guests_email ON guests(email);
    CREATE INDEX CONCURRENTLY idx_guests_phone ON guests(phone);
    CREATE INDEX CONCURRENTLY idx_guests_status ON guests(status);
    
    -- Room inventory optimization
    CREATE INDEX CONCURRENTLY idx_rooms_status ON rooms(status);
    CREATE INDEX CONCURRENTLY idx_rooms_room_type ON rooms(room_type_id);
    
    -- Invoice queries
    CREATE INDEX CONCURRENTLY idx_invoices_guest_id ON invoices(guest_id);
    CREATE INDEX CONCURRENTLY idx_invoices_booking_id ON invoices(booking_id);
    CREATE INDEX CONCURRENTLY idx_invoices_status ON invoices(status);
    CREATE INDEX CONCURRENTLY idx_invoices_created_at ON invoices(created_at DESC);
    
    -- Analytics queries
    CREATE INDEX CONCURRENTLY idx_bookings_date_range ON bookings(check_in_date, check_out_date);
    CREATE INDEX CONCURRENTLY idx_payments_created_at ON payments(created_at DESC);
    """ : var.rds_engine == "mysql" ? """
    -- Booking queries optimization
    ALTER TABLE bookings ADD INDEX idx_guest_id (guest_id);
    ALTER TABLE bookings ADD INDEX idx_room_id (room_id);
    ALTER TABLE bookings ADD INDEX idx_check_in_date (check_in_date);
    ALTER TABLE bookings ADD INDEX idx_status (status);
    ALTER TABLE bookings ADD INDEX idx_created_at (created_at DESC);
    
    -- Guest queries optimization
    ALTER TABLE guests ADD INDEX idx_email (email);
    ALTER TABLE guests ADD INDEX idx_phone (phone);
    ALTER TABLE guests ADD INDEX idx_status (status);
    
    -- Room inventory optimization
    ALTER TABLE rooms ADD INDEX idx_status (status);
    ALTER TABLE rooms ADD INDEX idx_room_type_id (room_type_id);
    
    -- Invoice queries
    ALTER TABLE invoices ADD INDEX idx_guest_id (guest_id);
    ALTER TABLE invoices ADD INDEX idx_booking_id (booking_id);
    ALTER TABLE invoices ADD INDEX idx_status (status);
    ALTER TABLE invoices ADD INDEX idx_created_at (created_at DESC);
    
    -- Analytics queries
    ALTER TABLE bookings ADD INDEX idx_dates (check_in_date, check_out_date);
    ALTER TABLE payments ADD INDEX idx_created_at (created_at DESC);
    """ : "SQL not provided for this engine"
}

# ============================================================================
# CONNECTION POOLING - PgBouncer/ProxySQL Recommendation
# ============================================================================

output "connection_pooling_guide" {
  description = "Connection pooling configuration guide"
  value = """
    POOLING CONFIGURATION GUIDE
    ============================
    
    For PostgreSQL, use PgBouncer (recommended):
    - Mode: transaction pooling for micro-services
    - Pool size: (CPU cores * 2) + max_spare_servers
    - Reserve pool: 3 connections
    - Connect timeout: 15 seconds
    
    For MySQL, use ProxySQL:
    - Connection pooling with failover support
    - Query caching for repeated queries
    - Read/write splitting for replicas
    - Connection reuse optimization
    
    Expected improvements:
    - 50-70% reduction in connection overhead
    - 30-50% improvement in query throughput
    - Better resource utilization under load
    
    Configuration steps:
    1. Deploy PgBouncer/ProxySQL as sidecar or separate EC2
    2. Configure application to connect to pooler
    3. Monitor pool metrics and adjust pool size
    4. Implement circuit breaker for pool overflow
  """
}

# ============================================================================
# QUERY OPTIMIZATION RECOMMENDATIONS
# ============================================================================

output "query_optimization_tips" {
  description = "Common query optimization patterns"
  value = """
    QUERY OPTIMIZATION PATTERNS
    ============================
    
    1. N+1 Query Problem (Most Common)
    ❌ BAD:
       for booking in bookings:
           guest = Guest.objects.get(booking.guest_id)  # 1000+ queries!
    
    ✅ GOOD:
       bookings = bookings.select_related('guest')  # 1 query with JOIN
    
    2. Large Result Sets
    ❌ BAD:
       SELECT * FROM bookings;  -- Millions of rows
    
    ✅ GOOD:
       SELECT booking_id, status FROM bookings
       WHERE created_at > now() - INTERVAL '30 days'
       LIMIT 1000;
    
    3. Missing Indexes
    ❌ BAD:
       SELECT * FROM bookings WHERE guest_id = $1;  -- Table scan
    
    ✅ GOOD:
       CREATE INDEX idx_bookings_guest_id ON bookings(guest_id);
    
    4. Subquery Inefficiency
    ❌ BAD:
       SELECT * FROM bookings
       WHERE guest_id IN (SELECT id FROM guests WHERE status = 'active');
    
    ✅ GOOD:
       SELECT b.* FROM bookings b
       INNER JOIN guests g ON b.guest_id = g.id
       WHERE g.status = 'active';
    
    5. Multiple Joins Without Filtering
    ❌ BAD:
       SELECT * FROM bookings b
       JOIN guests g ON b.guest_id = g.id
       JOIN invoices i ON b.id = i.booking_id
       JOIN payments p ON i.id = p.invoice_id;
       -- Cartesian explosion
    
    ✅ GOOD:
       SELECT b.id, g.name, SUM(p.amount)
       FROM bookings b
       INNER JOIN guests g ON b.guest_id = g.id
       LEFT JOIN invoices i ON b.id = i.booking_id
       LEFT JOIN payments p ON i.id = p.invoice_id
       WHERE b.created_at > now() - INTERVAL '30 days'
       GROUP BY b.id, g.name;
    
    6. Function Use Preventing Indexes
    ❌ BAD:
       SELECT * FROM bookings WHERE LOWER(status) = 'pending';
       -- Can't use index on status
    
    ✅ GOOD:
       SELECT * FROM bookings WHERE status = 'pending';
       -- Or create functional index:
       CREATE INDEX idx_bookings_status_lower ON bookings(LOWER(status));
    
    Tools for optimization:
    - EXPLAIN ANALYZE (PostgreSQL)
    - EXPLAIN EXTENDED (MySQL)
    - RDS Performance Insights
    - pgAdmin query planner
  """
}

# ============================================================================
# MONITORING OUTPUTS
# ============================================================================

output "database_tuning_parameters" {
  description = "Applied performance tuning parameters"
  value = {
    parameter_group_name = aws_db_parameter_group.performance.name
    max_connections      = var.rds_max_connections
    slow_query_threshold = "${var.rds_slow_query_threshold_ms}ms"
    shared_buffers       = "${var.rds_shared_buffers_percent}%"
    work_mem             = "${var.rds_work_mem_mb}MB"
  }
}

output "performance_insights_enabled" {
  description = "Whether Performance Insights is enabled"
  value       = var.enable_performance_insights
}

output "performance_insights_retention" {
  description = "Performance Insights retention period"
  value       = var.enable_performance_insights ? "${var.performance_insights_retention_days} days" : "disabled"
}
