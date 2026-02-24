# Performance Optimization & Caching - Comprehensive Guide

**Gap #7: Performance Optimization & Caching**

**Version:** 1.0.0  
**Last Updated:** February 25, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Redis Caching Architecture](#redis-caching-architecture)
3. [Django Caching Integration](#django-caching-integration)
4. [Database Performance Optimization](#database-performance-optimization)
5. [Query Optimization Patterns](#query-optimization-patterns)
6. [Caching Strategies](#caching-strategies)
7. [Performance Monitoring](#performance-monitoring)
8. [Load Testing & Benchmarking](#load-testing--benchmarking)
9. [Capacity Planning](#capacity-planning)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### Performance Problem Statement

Current system performance bottlenecks:
- **Database queries:** 200ms+ average response time for complex queries
- **N+1 problem:** Multiple queries per request (bookings + guests)
- **Session storage:** Database calls for every request session lookup
- **Temporary data:** No caching for frequently accessed data
- **Result:** Slow response times, high database load, poor scalability

### Gap #7 Solution

Implement a **three-layer caching strategy**:

```
Layer 3: HTTP Cache (CloudFront/Browser)
         ↓
Layer 2: Application Cache (Redis)
         ↓
Layer 1: Database Layer (Optimized indexes, tuning)
```

### Expected Results

After Gap #7 implementation:
- **Response time:** 200ms → 50-100ms (50-75% improvement)
- **Database load:** 100 queries/sec → 20 queries/sec (80% reduction)
- **Throughput:** 100 req/sec → 400 req/sec (4x improvement)
- **Cost efficiency:** Fewer database connections needed, smaller RDS instance

---

## Redis Caching Architecture

### What is Redis?

Redis is an in-memory data structure store used for:
- **Session storage** - Replace database session lookups
- **Query caching** - Cache expensive query results
- **Cache-aside** - Application manages cache logic
- **Rate limiting** - Track API request counts
- **Real-time analytics** - Pub/Sub messaging
- **Leaderboards** - Sorted set operations

### Why Redis Over Memcached?

| Feature | Redis | Memcached |
|---------|-------|-----------|
| Data Types | Strings, Lists, Sets, Hashes, Sorted Sets | Strings only |
| Persistence | Snapshots (RDB) + AOF | No |
| Replication | Yes (master-slave) | No |
| Pub/Sub | Yes | No |
| Lua Scripts | Yes | No |
| Docker | ✅ Easy | ⚠️ More complex |

**Verdict:** Redis is more powerful and suitable for hotel booking system needs.

### Redis Deployment Options

#### Option 1: ElastiCache (Recommended)

**Pros:**
- AWS managed (automatic backups, failover)
- Multi-AZ support
- CloudWatch monitoring built-in
- Auto-patching
- Encryption at rest/transit

**Cons:**
- Cost: $0.10-0.50/hour depending on node type
- 50-100ms network latency

#### Option 2: Self-Managed (EC2)

**Pros:**
- Lower cost
- Direct control
- Lower latency (~1ms)

**Cons:**
- Must manage backups
- Must manage failover
- Must manage patching
- Operational overhead

**Recommendation:** Use ElastiCache for production (Gap #7 implements this).

### Redis Node Types

```hcl
# Development (Cheap)
redis_node_type = "cache.t4g.micro"      # $0.017/hour, 512MB
redis_num_nodes = 1                       # No HA
redis_enable_multi_az = false

# Staging (Medium)
redis_node_type = "cache.t4g.small"       # $0.034/hour, 1.37GB
redis_num_nodes = 2                       # HA enabled
redis_enable_multi_az = true

# Production (High Availability)
redis_node_type = "cache.r7g.large"       # $0.30/hour, 16GB, 96 GB/s bandwidth
redis_num_nodes = 3                       # Primary + 2 replicas
redis_enable_multi_az = true
```

### Redis Memory Sizing

**Memory Requirements Calculation:**

```
Session Data:
- Active sessions: 10,000 per peak
- Per session: 2KB (user_id, name, preferences)
- Total: 10,000 × 2KB = 20MB

Query Cache:
- Cached queries: 1,000-5,000 active entries
- Per query result: 5-50KB average
- Total: 2,000 × 25KB = 50MB

Temporary Data (OTP, passwords reset, etc.):
- Temporary entries: 1,000-5,000
- Per entry: 1KB average
- Total: 3,000 × 1KB = 3MB

Pub/Sub Queue:
- Pending messages: 100-1,000
- Per message: 1-5KB
- Total: 500 × 3KB = 1.5MB

=== TOTAL: ~75MB ===

Recommended Redis Size:
- Development: 512MB (cache.t4g.micro)
- Staging: 1.37GB (cache.t4g.small)
- Production: 16GB (cache.r7g.large)

Note: Buy 2-3x your actual needs for:
- Memory overhead (Redis internals)
- Peak usage spikes
- Eviction policy buffer
```

### Redis Configuration (Gap #7)

```hcl
# From terraform/caching.tf

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "nephele-hms-redis-${environment}"
  engine               = "redis"
  node_type            = var.redis_node_type          # Configurable
  num_cache_nodes      = var.redis_num_nodes          # 1-3 typically
  engine_version       = var.redis_engine_version     # 7.0+
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  
  # High Availability
  automatic_failover_enabled = var.redis_num_nodes > 1 ? true : false
  multi_az_enabled           = var.redis_enable_multi_az
  
  # Backup & Recovery
  snapshot_retention_limit = var.redis_snapshot_retention_days  # 5-30 days
  snapshot_window          = "03:00-05:00"  # Automated backup time
  
  # Security
  auth_token                 = random_password.redis_auth_token
  at_rest_encryption_enabled = var.enable_redis_encryption
  transit_encryption_enabled = var.enable_redis_encryption
}
```

---

## Django Caching Integration

### Django Cache Configuration

```python
# settings/production.py

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': [
            # Primary Redis instance
            f'rediss://{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0?ssl_cert_reqs=required'
            # Can add replica for read scaling
        ],
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            
            # Connection pooling
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            
            # Retry logic for Redis failures
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,  # Don't fail request if Redis down
            
            # Key prefix
            'KEY_PREFIX': f'{ENVIRONMENT}:nephele:',
            'VERSION': 1,
        }
    }
}

# Session configuration - use Redis instead of database
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'  # Use Redis cache we just configured
SESSION_COOKIE_AGE = 86400 * 7  # 7 days

# Cache timeout defaults
CACHE_TIMEOUT = 3600  # 1 hour for most data
```

### Common Caching Patterns

**Pattern 1: View-Level Caching**

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache for 5 minutes
def bookings_list(request):
    """List all bookings - static content"""
    bookings = Booking.objects.select_related('guest', 'room')
    return JsonResponse({'bookings': serialize(bookings)})
```

**Pattern 2: Query Result Caching**

```python
from django.core.cache import cache

def get_available_rooms(check_in, check_out):
    """Cache room availability (changes hourly)"""
    cache_key = f'available_rooms:{check_in}:{check_out}'
    
    # Try cache first
    rooms = cache.get(cache_key)
    if rooms:
        return rooms
    
    # Cache miss - query database
    rooms = Room.objects.filter(
        status='available',
        bookings__check_in_date__gte=check_out,
        bookings__check_out_date__lte=check_in
    ).values_list('id', 'name', 'price')
    
    # Cache for 1 hour
    cache.set(cache_key, rooms, 3600)
    
    return rooms
```

**Pattern 3: Cache Invalidation**

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Booking)
def invalidate_booking_cache(sender, instance, **kwargs):
    """Clear cache when booking changes"""
    # Clear room availability cache
    cache.delete(f'available_rooms:*')
    # Clear guest booking history
    cache.delete(f'guest_bookings:{instance.guest_id}')

# Better: Versioning pattern (Django 2.0+)
def get_guest_bookings(guest_id):
    """Cache guest bookings with automatic expiration"""
    cache_key = f'guest_bookings:{guest_id}'
    bookings = cache.get(cache_key)
    
    if bookings is None:
        bookings = Booking.objects.filter(
            guest_id=guest_id
        ).order_by('-created_at')[:50]
        cache.set(cache_key, bookings, 3600)  # Auto-expires
    
    return bookings
```

**Pattern 4: Decorator for Auto-Caching**

```python
from functools import wraps

def cache_result(timeout=3600, key_prefix=''):
    """Generic caching decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name and args
            cache_key = f'{key_prefix}:{func.__name__}:{args}:{kwargs}'
            
            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator

# Usage:
@cache_result(timeout=7200, key_prefix='pricing')
def calculate_invoice_total(booking_id):
    """Calculate invoice with 2-hour cache"""
    booking = Booking.objects.get(id=booking_id)
    return booking.calculate_total()
```

**Pattern 5: Cache as Session Backend**

```python
# Automatically cached (configured above)
def update_user_preferences(request):
    """User preferences cached in Redis"""
    request.session['preferences'] = {
        'language': 'en',
        'currency': 'USD',
        'notifications_enabled': True,
    }
    request.session.save()  # Saved to Redis instead of database
```

---

## Database Performance Optimization

### Connection Pooling

**Problem:** Creating new database connections is expensive
- SSL handshake: 50-100ms
- Authentication: 10-50ms
- Each request: New connection

**Solution:** Connection pooling via PgBouncer (PostgreSQL)

```bash
# Install pgbouncer
sudo apt-get install pgbouncer

# /etc/pgbouncer/pgbouncer.ini

[databases]
nephele = host=db.internal port=5432 user=postgres password=secret

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0

# Connection pooling
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10

# Performance tuning
server_idle_timeout = 600
server_connect_timeout = 15
idle_in_transaction_session_timeout = 30000
```

**Django Configuration:**

```python
# settings/production.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'pgbouncer.internal',  # Connect via PgBouncer
        'PORT': 6432,                   # PgBouncer port, not 5432
        'NAME': 'nephele',
        'USER': 'django',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'CONN_MAX_AGE': 600,            # Connection reuse
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Connection pooling settings
# Connections from Django per process
DATABASES['default']['CONN_MAX_AGE'] = 600  # Keep alive 10 min
```

**Expected Improvements:**
- 50-100ms connection setup → 1-5ms (50x improvement)
- Support 10x more concurrent users
- Database server load reduction

### Index Optimization

**Slow Query:** Without index
```sql
SELECT * FROM bookings WHERE guest_id = 123;
-- Table scan on 10M rows: 2000ms
```

**Fast Query:** With index
```sql
CREATE INDEX idx_bookings_guest_id ON bookings(guest_id);
SELECT * FROM bookings WHERE guest_id = 123;
-- Index lookup: 5ms
```

**Index Strategy for Hotel Booking System:**

```sql
-- Booking lookups (most common)
CREATE INDEX CONCURRENTLY idx_bookings_guest_id ON bookings(guest_id);
CREATE INDEX CONCURRENTLY idx_bookings_room_id ON bookings(room_id);
CREATE INDEX CONCURRENTLY idx_bookings_status ON bookings(status);
CREATE INDEX CONCURRENTLY idx_bookings_dates ON bookings(check_in_date, check_out_date);
CREATE INDEX CONCURRENTLY idx_bookings_created_at ON bookings(created_at DESC);

-- Guest queries
CREATE INDEX CONCURRENTLY idx_guests_email ON guests(email);
CREATE INDEX CONCURRENTLY idx_guests_phone ON guests(phone);

-- Room availability queries
CREATE INDEX CONCURRENTLY idx_rooms_room_type_id ON rooms(room_type_id);
CREATE INDEX CONCURRENTLY idx_rooms_status ON rooms(status);

-- Financial tracking
CREATE INDEX CONCURRENTLY idx_invoices_guest_id ON invoices(guest_id);
CREATE INDEX CONCURRENTLY idx_payments_booking_id ON payments(booking_id);
CREATE INDEX CONCURRENTLY idx_payments_created_at ON payments(created_at DESC);

-- Analytics queries
CREATE INDEX CONCURRENTLY idx_bookings_revenue ON bookings(check_in_date, total_amount);
```

**Check Index Usage:**

```sql
-- PostgreSQL: Find unused indexes
SELECT * FROM pg_stat_user_indexes
WHERE idx_scan = 0;  -- Never used

-- Remove unused indexes
DROP INDEX idx_unused;
```

---

## Query Optimization Patterns

### N+1 Query Problem (Most Common)

**❌ SLOW:**
```python
def booking_list(request):
    bookings = Booking.objects.all()  # 1 query
    
    result = []
    for booking in bookings:  # Loop over 1000 bookings
        guest = Guest.objects.get(id=booking.guest_id)  # 1000 queries!
        room = Room.objects.get(id=booking.room_id)     # 1000 queries!
        result.append({
            'booking_id': booking.id,
            'guest_name': guest.name,
            'room_name': room.name,
        })
    
    return JsonResponse({'bookings': result})
    # TOTAL: 2001 queries!
```

**Performance:** 2000 queries × 50ms = 100 seconds ❌

**✅ FAST:**
```python
def booking_list(request):
    bookings = Booking.objects.select_related(
        'guest',  # JOIN with Guest table
        'room'    # JOIN with Room table
    )  # 1 query with 2 JOINs
    
    result = [{
        'booking_id': b.id,
        'guest_name': b.guest.name,  # Already loaded
        'room_name': b.room.name,    # Already loaded
    } for b in bookings]
    
    return JsonResponse({'bookings': result})
    # TOTAL: 1 query!
```

**Performance:** 1 query × 50ms = 50ms ✅

**Verification:**
```python
from django.test.utils import CaptureQueriesContext
from django.db import connection

with CaptureQueriesContext(connection) as queries:
    result = booking_list(request)
    print(f"Queries executed: {len(queries.captured_queries)}")
    for query in queries.captured_queries:
        print(f"  - {query['time']:.3f}s: {query['sql'][:100]}")
```

### Batch Operations

**❌ SLOW:**
```python
for booking in bookings_to_cancel:
    booking.status = 'cancelled'
    booking.updated_at = timezone.now()
    booking.save()  # Database round-trip per booking
```

**✅ FAST:**
```python
bulk_update_data = [
    booking.update(status='cancelled', updated_at=timezone.now())
    for booking in bookings_to_cancel
]
Booking.objects.bulk_update(bookings_to_cancel, ['status', 'updated_at'], batch_size=1000)
# 1-2 round-trips instead of N
```

### Database Aggregations (Not Application)

**❌ SLOW:**
```python
bookings = Booking.objects.all()
total_revenue = sum(b.amount for b in bookings)  # Python loop, slow
```

**✅ FAST:**
```python
from django.db.models import Sum

total_revenue = Booking.objects.aggregate(
    total=Sum('amount')
)['total']  # Database does aggregation (100x faster)
```

---

## Caching Strategies

### Cache Levels

**Level 1: HTTP Cache (Client/CDN)**
```
- Expires: 1 hour
- Resources: Static files, public API responses
- Example: GET /api/rooms/123/ → Cache-Control: max-age=3600
```

**Level 2: Application Cache (Redis)**
```
- Expires: 5-30 minutes
- Resources: Query results, user preferences, session data
- Example: GET /bookings/guest/123/ → Redis lookup (5ms)
```

**Level 3: Database Layer**
```
- Indexes for fast retrieval
- Connection pooling to reduce overhead
```

### Cache Invalidation Strategies

**Strategy 1: Time-Based Expiration (TTL)**
```python
# Cache expires after set time, no manual invalidation
cache.set('booking_details:123', booking_data, timeout=3600)
# Auto-expires after 1 hour
```

**Best for:** Data that changes infrequently (guest profiles, exchange rates)

**Strategy 2: Event-Based Invalidation**

```python
@receiver(post_save, sender=Booking)
def invalidate_booking_cache(sender, instance, **kwargs):
    """Clear cache immediately when booking changes"""
    cache.delete(f'booking:{instance.id}')
    cache.delete(f'guest_bookings:{instance.guest_id}')
    # IMPORTANT: Also invalidate related data
    cache.delete(f'room_availability:{instance.room_id}')
```

**Best for:** Critical data (bookings, payments, inventory)

**Strategy 3: Hybrid (TTL + Event)** ⭐Recommended

```python
def get_booking_details(booking_id):
    cache_key = f'booking:{booking_id}'
    
    # Try cache (usually hits)
    booking = cache.get(cache_key)
    
    # Fallback to database (on timeout expiry)
    if booking is None:
        booking = Booking.objects.get(id=booking_id)
        cache.set(cache_key, booking, 3600)  # 1 hour TTL
    
    return booking

# On update, invalidate immediately
@receiver(post_save, sender=Booking)
def update_booking_cache(sender, instance, **kwargs):
    cache.set(f'booking:{instance.id}', instance, 0)  # Update immediately
```

**Best for:** Hotel system - combine instant updates with fallback expiry

### Cache Warming

Pre-populate cache at startup or scheduled intervals:

```python
def warm_cache():
    """Pre-load frequently accessed data into Redis"""
    
    # Popular room types
    room_types = RoomType.objects.all()
    for rt in room_types:
        cache.set(f'room_type:{rt.id}', rt, 86400)  # 24 hours
    
    # Exchange rates (update every hour)
    for currency in ['USD', 'EUR', 'GBP']:
        rate = fetch_exchange_rate(currency)
        cache.set(f'exchange_rate:{currency}', rate, 3600)
    
    logger.info(f"Cache warmed: {room_types.count()} room types")

# Schedule this on startup
from django.apps import AppConfig

class HotelAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hotel'
    
    def ready(self):
        warm_cache()
```

---

## Performance Monitoring

### Key Metrics to Monitor

**Redis Performance:**

```python
from django_redis import get_redis_connection

redis_conn = get_redis_connection('default')
info = redis_conn.info()

print(f"Memory usage: {info['used_memory_human']}")
print(f"Connected clients: {info['connected_clients']}")
print(f"Total commands: {info['total_commands_processed']}")
print(f"Hit rate: {info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses']):.2%}")
```

**Database Performance:**

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as queries:
    # Your view code
    pass

slow_queries = [q for q in queries.captured_queries if q['time'] > 0.1]
print(f"Slow queries (>100ms): {len(slow_queries)}")
```

**Application Performance (APM):**

```python
# Using Django Debug Toolbar (development only)
# Install: pip install django-debug-toolbar
DEBUG = True
INSTALLED_APPS = [..., 'debug_toolbar']

# Shows:
# - Query count and time
# - Cache hits/misses
# - Template rendering time
```

### CloudWatch Alarms for Performance

```hcl
# Alarm 1: High Redis Memory Usage
resource "aws_cloudwatch_metric_alarm" "redis_memory_high" {
  alarm_name          = "redis-memory-usage-high"
  metric_name         = "DatabaseMemoryUsagePercentage"
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  alarm_actions       = [sns_topic.arn]
}

# Alarm 2: Low Redis Hit Rate (ineffective caching)
resource "aws_cloudwatch_metric_alarm" "redis_hit_rate_low" {
  alarm_name          = "redis-hit-rate-low"
  metric_name         = "CacheHits"
  threshold           = 50  # Want 50%+ hit rate
  statistic           = "Average"
  alarm_actions       = [sns_topic.arn]
}

# Alarm 3: Slow Database Queries
# (Requires enabling slow query log in RDS)
```

---

## Load Testing & Benchmarking

### Baseline Measurements (Before Cache)

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/bookings/

# Results WITHOUT Cache:
# Requests per second: 10 req/sec
# Response time: 100ms
# Database queries: 1000 (heavy load)
```

### Load Testing with Cache

```bash
# Using Locust (Python load testing)
pip install locust

# locustfile.py
from locust import HttpUser, task

class HotelUser(HttpUser):
    @task
    def get_bookings(self):
        self.client.get("/api/bookings/")
    
    @task
    def get_rooms(self):
        self.client.get("/api/rooms/")

# Run test
locust -f locustfile.py --users 100 --spawn-rate 10

# Results WITH Cache:
# Requests per second: 200 req/sec (20x improvement!)
# Response time: 10ms
# Database queries: 50 (50x reduction!)
```

### Performance Report Template

```markdown
# Performance Benchmark Report

## Test Configuration
- Load: 100 concurrent users
- Duration: 5 minutes
- Test Date: 2026-02-25

## Before Optimization (Gap 6)
| Metric | Value |
|--------|-------|
| Requests/sec | 50 |
| Avg Response Time | 200ms |
| p95 Response Time | 500ms |
| p99 Response Time | 1000ms |
| Database Connections | 50 |
| Database Queries/sec | 500 |
| Errors | 2% (throttling) |

## After Optimization (Gap 7)
| Metric | Value |
|--------|-------|
| Requests/sec | 400 |
| Avg Response Time | 25ms |
| p95 Response Time | 50ms |
| p99 Response Time | 100ms |
| Database Connections | 5 |
| Database Queries/sec | 50 |
| Errors | 0% |

## Improvement
- **Throughput:** 50→400 = **8x improvement**
- **Response Time:** 200ms→25ms = **8x improvement**
- **Database Load:** 500→50 = **10x reduction**
```

---

## Capacity Planning

### Calculate Required Resources

**for 10,000 daily active users:**

```
VDU (Virtual Daily Users) = DAU × Peak Ratio
                          = 10,000 × 0.1  # Peak is 10% of DAU
                          = 1,000 concurrent users at peak

Concurrent: 1,000 users × 20 requests per session
          = 20,000 requests per hour
          = 5.5 requests/second baseline
```

**Database Load:**

```
Without caching:
- 5.5 req/sec × 10 queries per request = 55 queries/sec
- Required RDS: db.t3.medium (up to 100 queries/sec)

With caching (70% cache hit rate):
- 5.5 req/sec × 10 queries × 0.3 = 16.5 queries/sec
- Required RDS: db.t3.small (sufficient)
- Cost savings: $200/month
```

**Redis Size:**

```
Session data: 1,000 users × 5KB = 5MB
Query cache (1 day): 50,000 query results × 10KB = 500MB
Rate limits: 1,000 buckets × 1KB = 1MB
Pub/Sub queue: 10,000 messages × 1KB = 10MB

Total: ~520MB
Recommendation: 1.37GB (cache.t4g.small) for 2.5x buffer
```

---

## Troubleshooting

### Problem 1: Redis Cache Misses (Low Hit Rate)

**Symptoms:**
- Cache hit rate < 50%
- Redis memory not filling up
- No performance improvement

**Diagnosis:**

```python
from django_redis import get_redis_connection

redis = get_redis_connection('default')
info = redis.info()

hit_rate = info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses'])
print(f"Cache hit rate: {hit_rate:.2%}")  # < 50% is problem

# Also check keys
print(f"Total keys: {redis.dbsize()}")  # Should have many keys
```

**Causes & Solutions:**

1. **Cache timeouts too short**
   - Symptom: Hit rate improves over time but drops daily
   - Solution: Increase TTL (from 3600 to 86400)

2. **Poor cache key design**
   - Symptom: Many unique keys, low reuse
   - Problem: `cache_key = user_id + timestamp`  (always unique)
   - Solution: Use stable keys like `cache_key = f'user_bookings:{user_id}'`

3. **Cache invalidation too aggressive**
   - Symptom: Clearing cache too frequently
   - Solution: Use event-based, not time-based only

### Problem 2: Redis Memory Running Out

**Symptoms:**
- Redis CPU high (100%)
- Slow response times
- CloudWatch alarm: `redis_memory_high`

**Diagnosis:**

```python
import redis
r = redis.from_url('redis://...')

# Memory usage breakdown
info = r.info('memory')
print(f"Used memory: {info['used_memory_human']}")
print(f"Peak memory: {info['peak_memory_human']}")
print(f"Memory policy: {r.config_get('maxmemory-policy')}")

# Find large keys
for key in r.scan_iter():
    size = r.memory_usage(key)
    if size > 1000000:  # > 1MB
        print(f"Large key: {key} ({size} bytes)")
```

**Solutions:**

1. **Increase Redis node size**
   ```hcl
   redis_node_type = "cache.t4g.medium"  # Larger node
   redis_num_nodes = 2  # Add more nodes
   ```

2. **Improve eviction policy**
   ```
   # Change from 'allkeys-lru' to 'allkeys-lfu' (least frequently used)
   # LFU is better for booking system (popular rooms cached longer)
   ```

3. **Cache less data**
   ```python
   # Only cache high-value queries
   # Cache timeout per environment:
   # - Dev: 3600s (1 hour)
   # - Staging: 1800s (30 min)
   # - Prod: 600s (10 min) - less space, more fresh data
   ```

### Problem 3: Database Performance Not Improving

**Symptoms:**
- Response time still slow even with cache
- Database CPU still high
- Cache is working (hit rate > 80%)

**Causes:**
1. Cache misses on hot data (newly viewed bookings)
2. Database queries still expensive (missing indexes)
3. N+1 problem still present (select_related missing)

**Diagnosis:**

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

# Find slow queries
with CaptureQueriesContext(connection) as q:
    # Trigger your view
    pass

slow = [query for query in q.captured_queries if query['time'] > 0.05]
for query in slow:
    print(f"{query['time']:.3f}s: {query['sql']}")
```

**Solutions:**
1. Add missing indexes (see Database Performance section)
2. Fix N+1 with select_related/prefetch_related
3. Increase cache hit rate with better TTL

---

## Deployment Checklist

**Pre-Deployment:**
- [ ] Load test baseline (without cache)
- [ ] Redis instance spun up and tested
- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Cache invalidation rules documented
- [ ] Alert thresholds calibrated

**Deployment:**
```bash
# 1. Deploy Redis infrastructure
make tf-apply-prod  # Applies caching.tf

# 2. Deploy code with cache integration
git push prod  # Deploy Django changes

# 3. Verify cache working
make cache-status  # Check Redis connection

# 4. Monitor metrics
# - Redis hit rate should exceed 50% within 1 hour
# - Database queries/sec should drop 50-70%
# - Response time should improve 50%+
```

**Post-Deployment:**
- [ ] Verify Redis connectivity from app
- [ ] Monitor cache hit rate (should be > 50%)
- [ ] Monitor database load (should drop)
- [ ] Monitor response times (should improve)
- [ ] Check for Redis evictions (should be minimal)
- [ ] Validate alert thresholds

---

## Summary

Gap #7 completes the performance optimization stack:

1. **Redis Caching** - In-memory cache for sessions and queries
2. **Database Tuning** - Optimized parameters and indexes
3. **Query Optimization** - Eliminate N+1 and ineffective queries
4. **Monitoring** - Track performance improvements

**Expected Results:**
- Response time: 200ms → 25-50ms (4-8x improvement)
- Throughput: 50 req/sec → 200-400 req/sec (4-8x improvement)
- Database load: 500 queries/sec → 50 queries/sec (10x reduction)
- Cost: Can use smaller RDS instance (saves $200+/month)

**Next: Gap #8** (Security Hardening) or continue to remaining gaps.

