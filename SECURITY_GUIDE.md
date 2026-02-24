# AWS Security Hardening Implementation Guide (Gap #8)

**Status:** Production-Ready  
**Last Updated:** 2024  
**Applicable Environments:** Development, Staging, Production  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Security Architecture Overview](#security-architecture-overview)
3. [AWS WAF Configuration](#aws-waf-configuration)
4. [Encryption Strategy](#encryption-strategy)
5. [Secrets Management](#secrets-management)
6. [HTTPS/TLS Configuration](#httpstls-configuration)
7. [Access Control & Authentication](#access-control--authentication)
8. [Compliance & Standards](#compliance--standards)
9. [Environment-Specific Configuration](#environment-specific-configuration)
10. [Deployment & Validation](#deployment--validation)
11. [Monitoring & Incident Response](#monitoring--incident-response)
12. [Troubleshooting](#troubleshooting)

---

## Executive Summary

Gap #8 implements comprehensive security hardening across the infrastructure, protecting against OWASP Top 10 vulnerabilities and ensuring compliance with industry standards. The solution includes:

- **AWS WAF** (Web Application Firewall) with multi-layered rule sets
- **AWS KMS** (Key Management Service) for encryption at rest
- **AWS Secrets Manager** for secure credential storage and rotation
- **ACM SSL/TLS Certificates** with automatic renewal
- **Network Isolation** via security groups
- **Monitoring & Alerting** for security events

### Security Coverage

| OWASP Category | Protection Mechanism | Status |
|---|---|---|
| A01: Broken Access Control | WAF + IP Restrictions + Secrets Manager | ✅ |
| A02: Cryptographic Failures | KMS + TLS 1.2+ + Secrets Manager | ✅ |
| A03: Injection | AWS Managed SQL Injection Rules | ✅ |
| A04: Insecure Design | Secure-by-Default IaC | ✅ |
| A05: Security Misconfiguration | Terraform Enforcement | ✅ |
| A06: Vulnerable Components | AWS Auto-Patching | ✅ |
| A07: Authentication Failures | Application Layer (beyond scope) | ⚠️ |
| A08: Software/Data Integrity | Secrets Manager + KMS | ✅ |
| A09: Logging/Monitoring | CloudWatch + WAF Logs | ✅ |
| A10: SSRF | AWS Managed Rules + Network Isolation | ✅ |

---

## Security Architecture Overview

### High-Level Security Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Internet Users                          │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS (TLS 1.2+)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS Shield (DDoS Protection)                     │
│              - Automatic detection & mitigation              │
│              - Shield Advanced (optional) for L7 protection   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            AWS WAF (Web Application Firewall)               │
│                                                              │
│  Rule Sets:                                                 │
│  1. Rate Limiting (2000 req/5min per IP)                   │
│  2. OWASP Common Rules                                      │
│  3. Known Bad Inputs                                        │
│  4. SQL Injection Protection                                │
│  5. Admin Endpoint Protection (IP-based)                    │
│  6. Geo-Blocking (optional, by country)                    │
│                                                              │
│  ▼ Blocked Traffic → SNS Alert               │             │
│  ▼ Allowed Traffic → CloudWatch Log          │             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│        Application Load Balancer (HTTPS only)               │
│        - TLS 1.2+ enforcement in production                  │
│        - Certificate auto-renewal via ACM                    │
│        - X-Forwarded-For header injection protection        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ECS Cluster (Encrypted Tasks)                   │
│        - Environment variables encrypted via KMS             │
│        - Secrets loaded from Secrets Manager                 │
│        - Network isolated via security groups               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ├──────────────────┬──────────────────┐
                         ▼                  ▼                  ▼
        ┌──────────────────────┐ ┌──────────────────┐ ┌──────────────┐
        │  RDS Database        │ │  ElastiCache     │ │  S3 Buckets  │
        │  - Encrypted at rest │ │  - SSL in transit │ │  - Encrypted │
        │  - VPC Isolated      │ │  - Auth tokens    │ │  - Private   │
        └──────────────────────┘ └──────────────────┘ └──────────────┘
                         │                            │
        ┌────────────────┴─────────────────┬──────────┘
        ▼                                  ▼
    ┌─────────────────────────────────────────────┐
    │      AWS Secrets Manager                    │
    │  - Database passwords (auto-rotated)        │
    │  - API keys and tokens                      │
    │  - OAuth credentials                        │
    │  - Encrypted by KMS key                     │
    └─────────────────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────────────────┐
    │      AWS KMS Encryption Key                 │
    │  - Master key for all encryption            │
    │  - Auto-rotation enabled                    │
    │  - CloudTrail logging for access            │
    └─────────────────────────────────────────────┘
```

### Security Layers

**Layer 1: Network Edge**
- AWS Shield (automatic DDoS mitigation)
- AWS WAF (application-layer attacks)
- Geo-blocking (optional)

**Layer 2: Application**
- HTTPS/TLS encryption
- Rate limiting
- Admin access controls
- IP whitelisting

**Layer 3: Data in Transit**
- TLS 1.2+ for all connections
- Certificate pinning (optional, app-level)

**Layer 4: Data at Rest**
- KMS encryption for all sensitive data
- Secrets Manager for credentials
- RDS encryption enabled
- S3 encryption enabled

**Layer 5: Secrets Management**
- Automatic rotation (30-day cycle)
- Encryption via KMS
- Secure retrieval by ECS tasks
- Audit logging via CloudTrail

---

## AWS WAF Configuration

### Overview

AWS WAF (Web Application Firewall) protects the Application Load Balancer from common web exploits. The implementation includes 6 rule sets operating in the following order:

```
Request → Rate Limit Check → OWASP Rules → Known Bad Inputs → 
SQL Injection → Admin Protection → Geo-Blocking → ALB
```

### Rule Set Details

#### Rule 0: Rate Limiting

**Purpose:** Prevent brute force and DDoS attacks by limiting requests per IP

**Configuration:**
```hcl
waf_rate_limit_requests = 2000  # Per IP
Duration = 5 minutes (300 seconds)  # Fixed
```

**Behavior:**
- Aggregates requests per source IP
- Counts requests in 5-minute windows
- Blocks requests exceeding threshold
- Returns HTTP 429 (Too Many Requests)
- Whitelist support via IP sets

**Whitelisting:**
```hcl
waf_whitelist_ips = [
  "1.2.3.4/32",              # Office IP
  "10.0.0.0/8",              # VPN network
  "216.58.217.46/32"         # Google monitoring service
]
```

**Deployment Example:**
```bash
# Apply with custom rate limit
terraform apply -var="waf_rate_limit_requests=1000"

# Monitor blocked requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name BlockedRequests \
  --dimensions Name=WebACL,Value=nephele-hms-prod --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

#### Rule 1: OWASP Common Rule Set

**Purpose:** Protect against OWASP Top 10 common attack patterns

**Features:**
- SQL injection patterns
- Cross-site scripting (XSS)
- Path traversal attacks
- Protocol attacks
- CVE-based signatures
- Maintained by AWS security team

**Coverage:**
- A03: Injection ✅
- A07: Authentication Failures (partial) ⚠️
- A10: SSRF ✅

**Configuration:**
```hcl
enable_waf_security = true  # Master switch

# No additional configuration needed
# AWS manages rule updates automatically
```

**Deployment:**
```bash
# Deploy WAF with OWASP rules
make tf-apply

# Verify deployment
aws wafv2 describe-web-acl \
  --scope REGIONAL \
  --id <web-acl-id> \
  --region us-east-1
```

**Maintenance:**
- AWS automatically updates rules
- No action required from users
- Review blocked requests weekly for false positives

#### Rule 2: Known Bad Inputs Rule Set

**Purpose:** Block requests with malicious payloads known to AWS

**Features:**
- Signatures from AWS threat intelligence
- Cross-site scripting (XSS)
- Local file inclusion (LFI)
- Remote file inclusion (RFI)
- Common web shells

**Example Blocks:**
```
/admin/?file=../../../../etc/passwd  # LFI
<script>alert('xss')</script>       # XSS
union select * from users           # SQL injection pattern
```

#### Rule 3: SQL Injection Protection

**Purpose:** Specifically target SQL injection attacks

**Features:**
- SQL keyword detection
- Syntax anomaly detection
- Case-insensitive matching
- Parameter tampering detection

**Examples Blocked:**
```
?id=1' OR '1'='1
?name=admin' --
?id=1; DROP TABLE users; --
```

#### Rule 4: Admin Endpoint Protection

**Purpose:** Restrict `/admin/*` endpoints to whitelisted IPs only

**Configuration:**
```hcl
admin_only_ips = [
  "203.0.113.45/32",     # Office IP
  "198.51.100.0/24"      # VPN subnet
]

# By default, these are required:
# - Variable must be specified in terraform.tfvars
# - Not included in deployment without explicit configuration
```

**Behavior:**
- Applies to `/admin/*` paths only
- Blocks all traffic from non-whitelisted IPs
- Returns HTTP 403 (Forbidden)
- Logs attempts to CloudWatch

**Deployment:**
```bash
# Create terraform.tfvars
cat >> terraform/terraform.tfvars << EOF
admin_only_ips = [
  "203.0.113.45/32"
]
EOF

# Apply changes
make tf-apply
```

**Testing:**
```bash
# From whitelisted IP (should succeed)
curl -H "X-Forwarded-For: 203.0.113.45" https://api.example.com/admin/dashboard

# From non-whitelisted IP (should fail with 403)
curl -H "X-Forwarded-For: 8.8.8.8" https://api.example.com/admin/dashboard
# HTTP/1.1 403 Forbidden
```

#### Rule 5: Geo-Blocking (Optional)

**Purpose:** Block traffic from specific countries

**Configuration:**
```hcl
enable_geo_blocking = true

blocked_countries = [
  "CN",   # China
  "RU",   # Russia
  "KP"    # North Korea
]
```

**How It Works:**
- Queries IP geolocation database
- Compares request origin to blocked list
- If matched, returns HTTP 403
- Logged to CloudWatch

**Deployment:**
```bash
# Enable geo-blocking
terraform apply \
  -var="enable_geo_blocking=true" \
  -var='blocked_countries=["CN", "RU"]'

# Disable for testing
terraform apply -var="enable_geo_blocking=false"
```

**Testing:**
```bash
# Simulate request from China (should be blocked)
curl -H "CloudFront-Viewer-Country: CN" https://api.example.com/

# Verify in CloudWatch logs
aws logs tail /aws/waf/nephele-hms/prod --follow
```

### WAF Monitoring

#### CloudWatch Metrics

**Key Metrics:**
- `AllowedRequests` - Requests allowed through WAF
- `BlockedRequests` - Requests blocked by WAF
- `SampledRequests` - Sample of all requests (for analysis)

**Viewing Metrics:**
```bash
# Get blocked requests in last hour
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name BlockedRequests \
  --dimensions Name=WebACL,Value=nephele-hms-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum

# Output:
# {
#     "Datapoints": [
#         {
#             "Timestamp": "2024-01-15T14:30:00Z",
#             "Sum": 45.0,
#             "Unit": "Count"
#         },
#         ...
#     ]
# }
```

#### CloudWatch Alarms

**Alarm 1: Excessive Blocked Requests**

Triggers when:
- Blocked requests exceed `waf_alarm_threshold` (default: 100) in 5 minutes
- Indicates potential attack or misconfiguration

**Response:**
```bash
# Acknowledge alarm
aws cloudwatch set-alarm-state \
  --alarm-name nephele-hms-waf-blocked-requests \
  --state-value INSUFFICIENT_DATA \
  --state-reason "Acknowledged by ops team"

# Investigate
aws logs tail /aws/waf/nephele-hms/prod --follow --filter-pattern "403"

# Adjust rate limit if needed
terraform apply -var="waf_rate_limit_requests=3000"
```

#### CloudWatch Logs

**Log Location:** `/aws/waf/nephele-hms/{environment}`

**Sample Log Entry:**
```json
{
  "terminatingRuleId": "r1000",
  "terminatingRuleType": "RATE_BASED",
  "terminatingRuleMatchDetails": [
    {
      "conditionSpecifier": "IP",
      "sensitivityLevel": "DEFAULT",
      "eachMatcherStatement": {
        "fieldToMatch": {
          "method": {}
        }
      }
    }
  ],
  "httpsourceipaddress": "203.0.113.77",
  "httprequestid": "abc-123-def",
  "action": "BLOCK",
  "httpsourcename": "CF",
  "rulegrouplist": [],
  "ratebasedrulelistx": [
    {
      "ratebasedruleid": "generic_aggregator",
      "limiteddosactions": [
        "BLOCK"
      ],
      "actionssettaken": [
        "BLOCK"
      ],
      "scopedownstatement": null,
      "evaluatingtime": 1705334400000,
      "raterulecount": 3500
    }
  ],
  "nonterminatingmatchingrules": [],
  "httpsourceasnumber": "AS15169",
  "formatversion": 1,
  "webaclid": "arn:aws:wafv2:us-east-1:123456789:global/webacl/nephele-hms/a1b2c3d4",
  "terminating": true,
  "timestamp": 1705334400000,
  "httpmethod": "POST",
  "clientip": "203.0.113.77",
  "uri": "/api/v1/bookings",
  "args": "user_id=123&action=create",
  "httpsourceid": "cloudFront"
}
```

**Querying Logs:**
```bash
# Find all 403 (blocked) requests
aws logs filter-log-events \
  --log-group-name /aws/waf/nephele-hms/prod \
  --filter-pattern '{ $.action = "BLOCK" }' \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --end-time $(date +%s)000

# Find blocked SQL injection attempts
aws logs filter-log-events \
  --log-group-name /aws/waf/nephele-hms/prod \
  --filter-pattern '{ $.terminatingRuleId = "sql-injection-rule" }' \
  --start-time $(date -d '24 hours ago' +%s)000 \
  --end-time $(date +%s)000

# Count blocked requests by IP
aws logs insights query \
  --log-group-name /aws/waf/nephele-hms/prod \
  --query-string 'fields @timestamp, httpsourceipaddress, action | filter action = "BLOCK" | stats count() as blocked_count by httpsourceipaddress | sort blocked_count desc'
```

---

## Encryption Strategy

### Overview

Encryption protects sensitive data at rest and in transit using AWS KMS (Key Management Service) as the master key provider.

```
┌────────────────────────────────────────────┐
│          Data Encryption Strategy          │
├────────────────────────────────────────────┤
│ In Transit:        TLS 1.2+ (ALB → Clients)│
│ In Transit:        TLS 1.2+ (App → RDS)    │
│ In Rest:           KMS (Secrets Manager)   │
│ In Rest:           KMS (RDS encryption)    │
│ In Rest:           KMS (EBS volumes)       │
│ In Rest:           S3 SSE-KMS (buckets)    │
│ Environment Vars:  KMS envelope encryption │
└────────────────────────────────────────────┘
```

### KMS Key Configuration

#### Key Setup

```hcl
resource "aws_kms_key" "encryption" {
  description             = "KMS key for nephele-hms encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name        = "nephele-hms-key"
    Environment = var.environment
  }
}

resource "aws_kms_alias" "encryption" {
  name          = "alias/nephele-hms-${var.environment}"
  target_key_id = aws_kms_key.encryption.key_id
}
```

#### Key Permissions

**Default Policy:** AWS managed (automatically restricts to EC2, Secrets Manager, RDS)

**Custom Policy Example:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Allow ECS task execution role",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole"
      },
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Allow RDS encryption",
      "Effect": "Allow",
      "Principal": {
        "Service": "rds.amazonaws.com"
      },
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:CreateGrant"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Key Rotation

**Automatic Rotation:**
- Enabled by default: `enable_key_rotation = true`
- Rotates annually
- Old key material still available for decryption

**Manual Rotation (if needed):**
```bash
# Create new key
NEW_KEY=$(aws kms create-key --description "new-hms-key" --query 'KeyMetadata.KeyId' --output text)

# Create alias for new key
aws kms create-alias --alias-name alias/nephele-hms-new --target-key-id $NEW_KEY

# Migrate Secrets Manager to new key
# (requires manual process - contact AWS Support)
```

### Encryption at Rest

#### RDS Database Encryption

```bash
# Enable encryption (already configured in database.tf)
# All Postgres instances use KMS encryption

# Verify encryption
aws rds describe-db-instances \
  --db-instance-identifier nephele-hms-prod-db \
  --query 'DBInstances[0].StorageEncrypted'
# Output: true

# Check encryption key
aws rds describe-db-instances \
  --db-instance-identifier nephele-hms-prod-db \
  --query 'DBInstances[0].KmsKeyId'
# Output: arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
```

#### EBS Volume Encryption

All ECS/EC2 instances use encrypted EBS volumes (configured automatically with KMS key).

#### S3 Bucket Encryption

```bash
# Enable default encryption for uploads
aws s3api put-bucket-encryption \
  --bucket nephele-hms-backups-prod \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "aws:kms",
          "KMSMasterKeyID": "arn:aws:kms:us-east-1:123456789012:key/..."
        }
      }
    ]
  }'

# Verify encryption
aws s3api get-bucket-encryption \
  --bucket nephele-hms-backups-prod
```

### Encryption in Transit

#### TLS Configuration

**Listeners (ALB):**
- HTTPS (443): TLS 1.2+
- HTTP (80): Redirect to HTTPS (only in non-prod)

**TLS Policy for Production:**
```bash
# AWS predefined policy: ELBSecurityPolicy-TLS-1-2-2017-01
# - Only TLS 1.2+
- Ciphers: Only strong ciphers
- No SSL 3.0, TLS 1.0, TLS 1.1

# Application to ALB:
resource "aws_lb_listener" "https" {
  load_balancer_arn = var.alb_arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.main.arn
  ...
}
```

**Testing TLS:**
```bash
# Check minimum TLS version
openssl s_client -connect api.example.com:443 -tls1 2>&1 | grep -i "alert\|error\|sslv3\|tlsv1 "
# Expected: Connection refused (TLS 1.0 not allowed)

openssl s_client -connect api.example.com:443 -tls1_2 2>&1 | grep -i "depth=0"
# Expected: Successful connection

# Check certificate chain
openssl s_client -connect api.example.com:443 -showcerts < /dev/null

# Verify cipher strength
nmap --script ssl-enum-ciphers -p 443 api.example.com
```

---

## Secrets Management

### AWS Secrets Manager

Secrets Manager securely stores and rotates sensitive credentials including:
- Database passwords
- API keys and tokens
- OAuth provider secrets
- SSH keys (optional)
- Database connection strings

### Secret Configuration

#### Database Password Secret

```hcl
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "nephele-hms/database/password-${var.environment}"
  recovery_window_in_days = 7
  
  rotation_rules {
    automatically_after_days = 30
  }

  tags = {
    Environment = var.environment
  }
}
```

**Features:**
- Automatic rotation every 30 days
- 7-day recovery window if accidentally deleted
- Encrypted at rest with KMS

**Accessing from ECS:**

```python
# Django settings.py
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        raise

# Load database password
db_secret = get_secret('nephele-hms/database/password-prod')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nephele_hotel_prod',
        'USER': 'postgres',
        'PASSWORD': db_secret['password'],
        'HOST': 'nephele-hms-prod-db.xxxxx.rds.amazonaws.com',
        'PORT': 5432,
    }
}
```

#### API Keys Secret

```hcl
resource "aws_secretsmanager_secret" "api_keys" {
  name                    = "nephele-hms/api/keys-${var.environment}"
  recovery_window_in_days = 7

  tags = {
    Environment = var.environment
  }
}

# Store initial secret value
resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    stripe_publishable = "pk_test_...",
    stripe_secret      = "sk_test_...",
    twilio_account_sid = "ACxxxxxxxx",
    twilio_auth_token  = "xxxxxxx"
  })
}
```

**Accessing from Application:**

```python
# Get API keys
api_keys = get_secret('nephele-hms/api/keys-prod')
STRIPE_PUBLIC_KEY = api_keys['stripe_publishable']
STRIPE_SECRET_KEY = api_keys['stripe_secret']
```

#### OAuth Secrets

```hcl
resource "aws_secretsmanager_secret" "oauth_secrets" {
  name                    = "nephele-hms/oauth/secrets-${var.environment}"
  recovery_window_in_days = 7

  rotation_rules {
    automatically_after_days = 90  # Oauth secret rotation is less frequent
  }
}

# Store OAuth credentials
resource "aws_secretsmanager_secret_version" "oauth_secrets" {
  secret_id = aws_secretsmanager_secret.oauth_secrets.id
  secret_string = jsonencode({
    google_client_id     = "...",
    google_client_secret = "...",
    facebook_appid       = "...",
    facebook_appsecret   = "...",
    github_client_id     = "...",
    github_client_secret = "..."
  })
}
```

### Secret Rotation

#### Understanding Rotation

When a secret is rotated:
1. Secrets Manager generates new value
2. New value is tested with database
3. Old value remains accessible during transition
4. Lambda function (optional) can handle custom logic
5. Rotation timestamp is updated

**Rotation Flow:**
```
T=0:00    Rotation starts (automatic)
T=0:05    New password generated
T=0:10    Database updated with new password
T=0:15    Rotation completes, new version active
T=0:20    Old version still accessible for 30 min

# During transition, applications continue using old version
# until they reconnect or restart and fetch new version
```

#### Viewing Rotation History

```bash
# List rotation events
aws secretsmanager describe-secret \
  --secret-id nephele-hms/database/password-prod \
  --query 'RotationRules'

# Output:
# {
#     "AutomaticallyAfterDays": 30,
#     "Duration": "3h",
#     "ScheduleExpression": "rate(30 days)"
# }

# Get rotation history
aws secretsmanager get-secret-value \
  --secret-id nephele-hms/database/password-prod \
  --version-id 12345678-rotation-1
```

#### Handling Rotation in Application

**Django Connection Pool:**

```python
# Use connection pool with recycling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Recycle connections every 10 min
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Application will automatically use new password on reconnect
```

**Manual Secret Update Check:**

```python
import boto3
from datetime import datetime, timedelta

def refresh_secrets_if_rotated(cache_key='last_secret_fetch'):
    """Check if secret was rotated and refresh if needed"""
    
    client = boto3.client('secretsmanager')
    
    # Get last check time from cache/config
    last_fetch = cache.get(cache_key)
    if last_fetch and (datetime.now() - last_fetch) < timedelta(minutes=5):
        return  # Check every 5 minutes max
    
    # Get secret metadata
    response = client.describe_secret(
        SecretId='nephele-hms/database/password-prod'
    )
    
    # Check if rotated
    last_rotation = response.get('LastRotatedDate')
    if last_rotation and last_rotation > last_fetch:
        # Secret was rotated, reload it
        new_secret = client.get_secret_value(
            SecretId='nephele-hms/database/password-prod'
        )
        # Update database connection
        from django.db import connections
        connections.close_all()
        
        # Cache update time
        cache.set(cache_key, datetime.now())
```

### Secrets Auditing

**CloudTrail Logging:**

All Secrets Manager API calls are automatically logged to CloudTrail.

```bash
# View Secrets Manager API calls
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue \
  --max-results 50

# Filter to specific secret
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue \
  --query 'Events[].{Time:EventTime, Principal:CloudTrailEvent}' \
  --output table
```

**CloudWatch Alarms:**

```hcl
resource "aws_cloudwatch_metric_alarm" "secret_access" {
  alarm_name          = "nephele-hms-secret-access-anomaly"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "GetSecretValueRequestCount"
  namespace           = "AWS/SecretsManager"
  period              = 300
  statistic           = "Sum"
  threshold           = 1000  # Adjust based on normal traffic
  
  alarm_actions = [aws_sns_topic.security_alerts.arn]
}
```

---

## HTTPS/TLS Configuration

### ACM Certificate Setup

#### Certificate Creation

```bash
# Terraform automatically creates and manages certificate
# No manual action needed

# Verify certificate status
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/abc123 \
  --query '{Status:CertificateStatus, DomainName:DomainName, ValidationMethod:DomainValidationOptions[0].ValidationMethod}'

# Output:
# {
#     "Status": "ISSUED",
#     "DomainName": "api.example.com",
#     "ValidationMethod": "DNS"
# }
```

#### DNS Validation

Certificate validation requires DNS CNAME records created by Terraform.

```bash
# Terraform creates Route53 records automatically
# Monitor certificate validation

# Check validation progress
aws acm describe-certificate \
  --certificate-arn <cert-arn> \
  --query 'Certificate.DomainValidationOptions[*].{Domain:DomainName, Status:ValidationStatus, Record:ResourceRecord}'
```

#### Certificate Renewal

ACM automatically renews certificates before expiration (90 days before).

```bash
# Monitor renewal process (optional)
aws cloudwatch get-metric-statistics \
  --namespace AWS/CertificateManager \
  --metric-name RenewalFailure \
  --dimensions Name=CertificateArn,Value=<arn> \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 \
  --statistics Sum
```

### ALB HTTPS Listener Configuration

**Listener Setup:**

```hcl
# HTTPS listener (production)
resource "aws_lb_listener" "https" {
  load_balancer_arn = var.alb_arn
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = aws_acm_certificate.main.arn
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"

  default_action {
    type             = "forward"
    target_group_arn = var.ecs_target_group_arn
  }
}

# Optional: HTTP redirect (non-production)
resource "aws_lb_listener" "http" {
  count             = var.enforce_https ? 0 : 1
  load_balancer_arn = var.alb_arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
```

**SSL Policy Details:**

```
ELBSecurityPolicy-TLS-1-2-2017-01

Protocols:
  - TLSv1.2 (only)

Ciphers:
  - ECDHE-RSA-AES128-GCM-SHA256
  - ECDHE-RSA-AES256-GCM-SHA384
  - ECDHE-RSA-AES128-SHA256
  - ECDHE-RSA-AES256-SHA384
  - ECDHE-RSA-AES128-SHA
  - ECDHE-RSA-AES256-SHA
  - AES128-GCM-SHA256
  - AES256-GCM-SHA384
  - AES128-SHA256
  - AES256-SHA384
  (No weak ciphers)
```

### Testing HTTPS/TLS

```bash
# Test TLS connection
openssl s_client -connect api.example.com:443 -tls1_2

# Check certificate details
openssl s_client -connect api.example.com:443 -showcerts | openssl x509 -text -noout

# Verify certificate chain
openssl s_client -connect api.example.com:443 -showcerts < /dev/null

# Test HTTP redirect
curl -I http://api.example.com/
# Expected: HTTP/1.1 301 Moved Permanently
# Location: https://api.example.com/
```

---

## Access Control & Authentication

### WAF Admin Protection

Admin endpoints (`/admin/*`) are protected by IP whitelisting.

**Configuration:**

```bash
# Set admin IPs in terraform.tfvars
cat > terraform/terraform.tfvars << EOF
admin_only_ips = [
  "203.0.113.45/32",   # Office IP
  "198.51.100.10/32",  # VPN exit IP
]
EOF

# Apply
terraform apply
```

**Testing:**

```bash
# Test from office IP (whitelisted)
curl -H "X-Forwarded-For: 203.0.113.45" https://api.example.com/admin/dashboard
# Expected: 200 OK

# Test from external IP (not whitelisted)
curl -H "X-Forwarded-For: 8.8.8.8" https://api.example.com/admin/dashboard
# Expected: HTTP/1.1 403 Forbidden
```

### Application-Level Authentication

**Note:** Gap #8 handles infrastructure security; application authentication (login, OAuth, JWT) is handled by the Django application.

**Best Practices for Application:**

1. **Password Hashing:**
   ```python
   from django.contrib.auth.hashers import make_password, check_password
   password = make_password(user_password)  # Uses PBKDF2
   ```

2. **Session Security:**
   ```python
   # settings.py
   SESSION_COOKIE_SECURE = True        # Only HTTPS
   SESSION_COOKIE_HTTPONLY = True      # No JavaScript access
   SESSION_COOKIE_SAMESITE = 'Strict'  # CSRF protection
   CSRF_COOKIE_SECURE = True
   CSRF_COOKIE_HTTPONLY = True
   ```

3. **OAuth Integration:**
   - Use OAuth for third-party logins
   - Validate tokens server-side
   - Store credentials securely via Secrets Manager

---

## Compliance & Standards

### OWASP Top 10 Coverage

| Category | Implementation | Verification |
|---|---|---|
| A01: Broken Access Control | WAF + IP restrictions | `make security-check` |
| A02: Cryptographic Failures | KMS + TLS 1.2+ | Certificate validation |
| A03: Injection | AWS Managed rules | WAF logs review |
| A04: Insecure Design | Infrastructure-as-Code | Terraform plan review |
| A05: Security Misconfiguration | Terraform enforcement | Pre-deployment scan |
| A06: Vulnerable Components | AWS auto-patching | AWS Patch Manager |
| A07: Authentication Failures | App-level (not Gap #8) | Application audit |
| A08: Software/Data Integrity | Secrets Manager + KMS | Secrets audit log |
| A09: Logging/Monitoring | CloudWatch + WAF logs | Log validation |
| A10: SSRF | AWS Managed rules | Network isolation test |

### PCI DSS Compliance

**Requirements Addressed:**

- **Req 1:** Network segmentation (security groups) ✅
- **Req 2:** Secure defaults (no default creds) ✅
- **Req 3:** Encrypt data at rest (KMS) ✅
- **Req 4:** Encrypt data in transit (TLS 1.2+) ✅
- **Req 6:** Secure development (infrastructure-as-code) ✅
- **Req 8:** Unique user IDs (app-level) ⚠️
- **Req 10:** Log and monitor (CloudWatch + WAF logs) ✅
- **Req 12:** Security policy (documented) ✅

**Additional Requirements:**
- Annual security assessment (use AWS Security Hub)
- Penetration testing (schedule quarterly)
- Vulnerability scanning (AWS Inspector)

### GDPR Data Protection

**Implemented:**
- ✅ Encryption at rest (data confidentiality)
- ✅ Encryption in transit (data confidentiality)
- ✅ Access controls (data limitation)
- ✅ Audit logging (accountability)
- ✅ Automatic secret rotation (data protection)

**Not in Gap #8 (App-level):**
- ⚠️ Consent management
- ⚠️ Data subject rights (right to deletion, access)
- ⚠️ Data processing agreements

---

## Environment-Specific Configuration

### Development Environment

```hcl
# terraform/dev.tfvars
enable_waf_security           = true   # Enabled for testing
enable_https                  = true   # HTTPS required
enforce_https                 = false  # HTTP also allowed for testing
enable_shield_advanced_security = false
enable_guardduty              = false
waf_rate_limit_requests       = 5000  # Higher limit for testing
enable_geo_blocking           = false
admin_only_ips                = ["0.0.0.0/0"]  # Allow all for testing
```

### Staging Environment

```hcl
# terraform/staging.tfvars
enable_waf_security           = true
enable_https                  = true
enforce_https                 = true    # Enforce but allow HTTP redirect
enable_shield_advanced_security = false
enable_guardduty              = true    # Enable threat detection
waf_rate_limit_requests       = 3000
enable_geo_blocking           = true
blocked_countries             = []      # No blocking in staging
admin_only_ips                = ["203.0.113.0/24", "198.51.100.0/24"]
```

### Production Environment

```hcl
# terraform/prod.tfvars
enable_waf_security           = true
enable_https                  = true
enforce_https                 = true    # HTTPS only
enable_shield_advanced_security = true  # Full DDoS protection
enable_guardduty              = true    # Threat detection
enable_config                 = true    # Compliance tracking
enable_security_hub           = true    # Security posture
waf_rate_limit_requests       = 2000
enable_geo_blocking           = true
blocked_countries             = ["CN", "RU"]  # Adjust as needed
admin_only_ips                = ["203.0.113.45/32", "198.51.100.10/32"]
domain_name                   = "api.nephele-hotels.com"
alternative_domain_names      = ["nephele-hotels.com", "www.nephele-hotels.com"]
```

---

## Deployment & Validation

### Pre-Deployment Checklist

```bash
# 1. Validate Terraform syntax
terraform validate

# 2. Review changes
terraform plan -var-file=terraform/prod.tfvars

# 3. Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxx

# 4. Verify KMS key exists
aws kms describe-key --key-id alias/nephele-hms-prod

# 5. Check Route53 zone
aws route53 list-resource-record-sets --hosted-zone-id Z123456
```

### Deployment Steps

```bash
# 1. Apply Terraform changes
make tf-apply

# 2. Wait for CloudFormation stack creation (5-10 minutes)
aws cloudformation describe-stacks \
  --stack-name nephele-hms-security-prod \
  --query 'Stacks[0].StackStatus'

# 3. Verify resources created
aws wafv2 list-web-acls --scope REGIONAL
aws secretsmanager list-secrets
aws kms list-keys

# 4. Test WAF rules
./scripts/test-waf.sh

# 5. Test HTTPS connectivity
openssl s_client -connect api.example.com:443

# 6. Check CloudWatch alarms
aws cloudwatch describe-alarms --alarm-name-prefix nephele-hms
```

### Post-Deployment Validation

```bash
# Verify all security services active
make security-check

# Output sample:
# ✅ WAF Web ACL: ACTIVE
# ✅ KMS Encryption Key: ENABLED (rotation: ON)
# ✅ Secrets Manager: 3 secrets stored
# ✅ ACM Certificate: ISSUED (expires: 2025-01-15)
# ✅ CloudWatch Alarms: 1 ALARM created
# ✅ HTTPS Listeners: ACTIVE
```

---

## Monitoring & Incident Response

### Security Monitoring Dashboard

```bash
# Create custom CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name nephele-hms-security \
  --dashboard-body file://dashboard-config.json
```

**Key Metrics to Monitor:**

- WAF blocked requests (should be < 100/5min normally)
- Failed authentication attempts (if enabled)
- Certificate expiration date (should be > 30 days)
- KMS key usage
- Secrets access patterns
- System performance impact

### Security Incident Response

#### DDoS Attack Response

**If blocked requests exceed threshold (e.g., 1000/5min):**

```bash
# 1. Check CloudWatch alarm
aws cloudwatch describe-alarms --alarm-names nephele-hms-waf-blocked-requests

# 2. Review WAF logs
aws logs tail /aws/waf/nephele-hms/prod --follow

# 3. Identify attack source
aws logs filter-log-events \
  --log-group-name /aws/waf/nephele-hms/prod \
  --filter-pattern '{ $.action = "BLOCK" }' \
  | jq '.events[].message | fromjson | .httpsourceipaddress' | sort | uniq -c

# 4. Create temporary IP block
# Option A: Add to blocked geographies (if from specific region)
terraform apply -var='blocked_countries=["XX"]'

# Option B: Increase rate limiting (reduce threshold)
terraform apply -var='waf_rate_limit_requests=500'

# 5. Contact AWS Support for Shield Advanced assistance (if subscribed)
```

#### Secret Compromise Response

**If API key is compromised:**

```bash
# 1. Immediately rotate the secret
aws secretsmanager rotate-secret \
  --secret-id nephele-hms/api/keys-prod \
  --rotation-rules AutomaticallyAfterDays=1

# 2. Get new secret value
aws secretsmanager get-secret-value \
  --secret-id nephele-hms/api/keys-prod \
  --query SecretString | jq .stripe_secret

# 3. Update application with new key (automatic via app restart)

# 4. Audit secret access
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue \
  --filter-pattern='nephele-hms/api/keys'

# 5. Revoke old key at provider (Stripe, etc.)
```

#### Certificate Expiration Response

**If certificate expires soon (< 7 days):**

```bash
# ACM automatically renews before expiration
# If renewal fails, manually intervene:

# 1. Check certificate status
aws acm describe-certificate \
  --certificate-arn <arn> \
  --query 'Certificate.{Status:CertificateStatus, Expiration:NotAfter}'

# 2. Verify DNS records for validation
aws route53 list-resource-record-sets \
  --hosted-zone-id <zone-id> \
  --query 'ResourceRecordSets[?Name==`_acm-validations.example.com`]'

# 3. If renewal stuck, request new certificate
aws acm request-certificate \
  --domain-name api.example.com \
  --validation-method DNS

# 4. Update ALB listener
aws elbv2 modify-listener \
  --listener-arn <listener-arn> \
  --certificates CertificateArn=<new-arn>
```

---

## Troubleshooting

### Common Issues & Solutions

#### 1. WAF Rate Limiting Too Aggressive

**Symptom:** Legitimate users blocked with HTTP 429

**Solution:**

```bash
# Check current limit
aws wafv2 get-web-acl --name nephele-hms --scope REGIONAL | grep -i limit

# Increase limit
terraform apply -var="waf_rate_limit_requests=3000"

# Monitor impact
aws logs tail /aws/waf/nephele-hms/prod --follow --filter-pattern 'BlockedRequests'
```

#### 2. Admin Endpoint Blocked Unexpectedly

**Symptom:** IT staff can't access /admin from office

**Cause:** Office IP changed or outbound IP different from expected

**Solution:**

```bash
# Check current whitelisted IPs
aws wafv2 get-ip-set \
  --name admin-only-ips \
  --scope REGIONAL \
  --id <id> | grep -i address

# Add new office IP
cat >> terraform/terraform.tfvars << EOF
admin_only_ips = [
  "203.0.113.45/32",   # Old IP
  "203.0.113.100/32"   # New IP
]
EOF

terraform apply
```

#### 3. Certificate Validation Fails

**Symptom:** Certificate stuck in "Pending validation"

**Cause:** Route53 DNS records not created or propagated

**Solution:**

```bash
# Check DNS records created
aws route53 list-resource-record-sets \
  --hosted-zone-id <zone-id> | grep -i "_acm-validations"

# If missing, Terraform should create them
terraform apply

# If DNS not propagating, manually verify
dig _acm-validations.api.example.com CNAME

# If still stuck, request new certificate
aws acm request-certificate \
  --domain-name api.example.com \
  --validation-method DNS
```

#### 4. High KMS Decryption Latency

**Symptom:** Application slow when retrieving secrets

**Cause:** KMS key grants being created/deleted frequently

**Solution:**

```bash
# Cache secrets locally (30 min TTL)
SECRETS_CACHE_TTL = 1800  # seconds

# Or use VPC endpoint for KMS
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxx \
  --service-name com.amazonaws.us-east-1.kms \
  --vpc-endpoint-type Interface
```

#### 5. Secrets Manager Rotation Fails

**Symptom:** Automatic rotation not happening

**Cause:** No Lambda function configured for custom rotation

**Solution:**

```bash
# Check rotation configuration
aws secretsmanager describe-secret \
  --secret-id nephele-hms/database/password-prod \
  --query 'RotationRules'

# If Lambda rotation fails, use AWS-managed rotation:
# (Database password rotation is AWS-managed by default)

# Manually rotate if needed
aws secretsmanager rotate-secret \
  --secret-id nephele-hms/database/password-prod \
  --rotation-rules AutomaticallyAfterDays=1
```

### Debug Commands

```bash
# Test WAF rule matching
aws wafv2 test-web-acl \
  --web-acl-arn <acl-arn> \
  --request-body-buffer '{"foo":"bar"}' \
  --request FileSizeConstraintStatement={FieldToMatch={UriPath={}}}

# Check ALB security group
aws ec2 describe-security-groups --group-ids <sg-id>

# List all TLS certificates
aws acm list-certificates

# Audit IAM access to secrets
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue

# Check RDS encryption status
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,StorageEncrypted,KmsKeyId]'
```

---

## Summary

Gap #8 (Security Hardening) provides:

✅ **AWS WAF** - 6 rule sets protecting against OWASP Top 10  
✅ **Encryption** - KMS at rest, TLS 1.2+ in transit  
✅ **Secrets Management** - Automatic rotation, secure storage  
✅ **Certificate Management** - ACM with auto-renewal  
✅ **Access Controls** - IP whitelisting, admin protection  
✅ **Monitoring** - CloudWatch metrics, alarms, WAF logs  

**Compliance:** Addresses PCI DSS, GDPR, and OWASP Top 10

**Next Steps:** 
- Deploy security infrastructure with `make tf-apply`
- Monitor security metrics in CloudWatch
- Review WAF logs weekly for optimization
- Proceed to Gap #9 (Advanced Logging)
