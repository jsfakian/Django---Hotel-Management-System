# Load Balancing & Advanced ALB Configuration
## Gap #4: Enhanced Application Load Balancer Setup

**Status:** ✅ Complete  
**Created:** 2024  
**Last Updated:** 2024  
**Version:** 1.0.0

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Path-Based Routing](#path-based-routing)
4. [Weighted Deployments (Canary)](#weighted-deployments-canary)
5. [SSL/TLS Configuration](#ssltls-configuration)
6. [Advanced Monitoring](#advanced-monitoring)
7. [Microservice Patterns](#microservice-patterns)
8. [Configuration Examples](#configuration-examples)
9. [Troubleshooting](#troubleshooting)
10. [Performance Tuning](#performance-tuning)

---

## 🎯 Overview

Gap #4 extends the basic ALB configuration from Gap #3 with advanced features:

✅ **Path-Based Routing** - Route different API versions/endpoints to different services  
✅ **Canary Deployments** - Safely deploy new versions with weighted traffic distribution  
✅ **SSL/TLS Management** - HTTPS configuration with ACM certificates  
✅ **Advanced Monitoring** - Track performance metrics, errors, and traffic patterns  
✅ **Microservice Support** - Route requests to different backends based on URL patterns  
✅ **Health Check Customization** - Custom endpoints and thresholds per service  

### Key Components

```
┌─────────────────────────────────────────────┐
│     Application Load Balancer (Public)       │
│ - Listens on HTTP (80) & HTTPS (443)        │
│ - Terminates SSL/TLS connections           │
│ - Routes based on URL paths                 │
└─────────────────────────────────────────────┘
                    ↓
        ┌───────────────────────────┐
        │  Path-Based Routing Rules  │
        ├───────────────────────────┤
        │ /api/v1/* → Main TG (100%) │
        │ /api/v2/* → Canary TG (10%)│
        │ /admin/*  → Admin TG       │
        │ /health/* → Health TG      │
        └───────────────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │    Multiple ECS Task Definitions   │
    ├───────────────────────────────────┤
    │ - Main App (stable)               │
    │ - Canary App (new version)        │
    │ - Admin Service (if separate)     │
    └───────────────────────────────────┘
```

---

## 🏗️ Architecture

### ABL Components

**Listener:** Accepts incoming traffic
- Port 80 (HTTP) → Redirects to 443
- Port 443 (HTTPS) → Routes to target groups

**Target Groups:** Backend services
- Main TG: Production application (stable version)
- Canary TG: New version for testing
- Staging TG: Alternative deployments

**Routing Rules:** Path-based conditions
- `/api/v1/*` → Main TG (100% traffic)
- `/api/v2/*` → Canary TG (weighted: 90% main, 10% canary)
- `/admin/*` → Admin TG
- `/health/*` → Health check TG

### Traffic Flow Example

```
Request: GET https://api.example.com/api/v2/bookings
    ↓
ALB Listener (Port 443, HTTPS)
    ↓
Routing Rule: Path matches /api/v2/*
    ↓
Forward Action with Weighted Routing:
    - 90% of traffic → Main Target Group (stable version)
    - 10% of traffic → Canary Target Group (new version)
    ↓
ECS Task (Main or Canary) ← Selected based on weight
    ↓
Response returned to client
```

---

## 🛣️ Path-Based Routing

### Routing Rules

Path-based routing directs traffic to different target groups based on URL patterns:

#### Rule 1: API v1 (Stable)
```
Pattern: /api/v1/*
Target: Main Target Group (aws_lb_target_group.app)
Action: Forward 100% of traffic
```

**Use Case:** Stable API version, all traffic goes here by default

#### Rule 2: API v2 (Canary)
```
Pattern: /api/v2/*
Target: Weighted forward
  - 90% → Main Target Group
  - 10% → Canary Target Group
```

**Use Case:** New API version under testing. 10% live traffic for validation before full rollout.

#### Rule 3: Admin
```
Pattern: /admin/*
Target: Main Target Group (or separate admin TG)
Action: Forward all traffic with special routing header
```

**Use Case:** Admin panel, could be same or separate service

#### Rule 4: Health Checks
```
Pattern: /health/*, /api/v1/health/*
Target: Main Target Group
Action: Forward 100% of traffic
```

**Use Case:** Monitoring and load balancer health checks

### Configuring Path Patterns

In `terraform/environments/prod.tfvars`:

```hcl
# Enable path-based routing
enable_path_based_routing = true

# Define path patterns
api_v1_path_patterns = ["/api/v1/*"]
api_v2_path_patterns = ["/api/v2/*"]
admin_path_patterns = ["/admin/*"]
health_path_patterns = ["/health/*", "/api/v1/health/*"]

# Canary traffic distribution
enable_canary_deployments = true
canary_traffic_weight = 10  # 10% to canary, 90% to main
```

### Adding New Routing Rules

To add a new routing rule, modify the `load-balancing.tf` file:

```hcl
resource "aws_lb_listener_rule" "new_service" {
  listener_arn = aws_lb_listener.https[0].arn

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.new_service.arn
  }

  condition {
    path_pattern {
      values = ["/new-service/*"]
    }
  }
}
```

---

## 🚀 Weighted Deployments (Canary)

Canary deployments allow you to gradually roll out new versions with minimal risk.

### How It Works

1. **Initial State:**
   - 100% traffic → Main Target Group (stable version)
   - 0% traffic → Canary Target Group (new version)

2. **Canary Phase 1 (Testing Phase):**
   - 90% traffic → Main Target Group (v1.0)
   - 10% traffic → Canary Target Group (v1.1 beta)
   - Monitor metrics and errors from canary

3. **Canary Phase 2 (Increasing):**
   - 70% traffic → Main Target Group
   - 30% traffic → Canary Target Group
   - Continue monitoring

4. **Canary Phase 3 (Majority Testing):**
   - 50% traffic → Main Target Group
   - 50% traffic → Canary Target Group
   - Check for issues

5. **Rollout Complete:**
   - 0% traffic → Main Target Group
   - 100% traffic → Canary Target Group (promoted to main)
   - Old version decommissioned

### Implementing Canary Deployment

#### Step 1: Deploy New Version to Canary Target Group

```bash
# Push new version to ECR
docker tag hms:v1.1 $ECR_REPO:v1.1
docker push $ECR_REPO:v1.1

# Create new ECS task definition
aws ecs register-task-definition \
  --family hms-canary \
  --container-definitions "[{\"name\":\"hms\",\"image\":\"$ECR_REPO:v1.1\",...}]"

# Create or update ECS service for canary
aws ecs create-service \
  --cluster nephele-hms-cluster \
  --service-name nephele-hms-service-canary \
  --task-definition hms-canary \
  --desired-count 1 \
  --load-balancers "[{\"targetGroupArn\":\"$CANARY_TG_ARN\",...}]"
```

Or using Terraform:

```hcl
# Enable canary in tfvars
enable_canary_deployments = true
canary_traffic_weight = 10

# Deploy and apply
make tf-plan-prod
make tf-apply-prod
```

#### Step 2: Monitor Canary Health

```bash
# View canary target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:region:account:targetgroup/nephele-hms-tg-canary/xyz

# Check CloudWatch metrics for errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --dimensions Name=LoadBalancer,Value=app/nephele-hms-alb/xyz \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Sum
```

#### Step 3: Increase Traffic Gradually

```bash
# Update canary weight in tfvars
canary_traffic_weight = 30  # Increase to 30%

# Apply changes
make tf-plan-prod
make tf-apply-prod
```

#### Step 4: Rollout or Rollback

**To Complete Rollout:**
```bash
# Swap main and canary versions
# Update main task definition to use v1.1
# Set canary weight to 0
# Destroy canary service
```

**To Rollback:**
```bash
# Set canary weight to 0
# Keep canary service running for quick re-activation
# Optionally destroy canary
```

### Monitoring Canary Deployment

Key metrics to watch:

| Metric | Target | Action if Exceeded |
|--------|--------|-------------------|
| Error Rate (5xx) | < 1% | Rollback |
| Response Time | < 500ms | Investigate |
| CPU Utilization | < 80% | Check autoscaling |
| Memory Utilization | < 85% | Check task size |
| Unhealthy Hosts | 0 | Investigate & rollback |

---

## 🔒 SSL/TLS Configuration

### HTTPS Setup

#### Prerequisite: AWS Certificate Manager (ACM) Certificate

```bash
# Request a certificate (or import existing)
aws acm request-certificate \
  --domain-name api.yourdomain.com \
  --validation-method DNS

# Wait for certificate to be validated (via DNS CNAME)

# Get certificate ARN
CERT_ARN=$(aws acm list-certificates \
  --query 'CertificateSummaryList[0].CertificateArn' \
  --output text)

echo $CERT_ARN
```

#### Configure in Terraform

In `terraform/environments/prod.tfvars`:

```hcl
# HTTPS Configuration
alb_enable_https         = true
alb_certificate_arn      = "arn:aws:acm:us-east-1:123456789:certificate/xyz"

# Optional: Configure custom root redirect
# Currently redirects / to /api/v1/docs/
```

#### SSL Policy

Default SSL policy: `ELBSecurityPolicy-TLS-1-2-2017-01`

This policy requires:
- TLS 1.2 or higher
- Strong cipher suites
- Perfect forward secrecy

To change SSL policy, edit `terraform/compute.tf`:

```hcl
ssl_policy = "ELBSecurityPolicy-TLS-1-2-Ext-2018-06"  # Broader compatibility
ssl_policy = "ELBSecurityPolicy-FS-1-2-2019-08"       # Forward secrecy only
```

#### Certificate Renewal

ACM automatically renews certificates 30 days before expiration:

```bash
# Check certificate renewal status
aws acm describe-certificate --certificate-arn $CERT_ARN

# Manual renewal (if needed)
aws acm request-certificate \
  --domain-name api.yourdomain.com \
  --subject-alternative-names "*.yourdomain.com"
```

### HSTS (HTTP Strict Transport Security)

Add HSTS header in your Django application:

```python
# settings.py
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

Or via ALB header manipulation (advanced):

```hcl
action {
  type = "forward"
  target_group_arn = aws_lb_target_group.app.arn

  # Note: ALB doesn't directly support response header modification
  # Use Django middleware or CloudFront for this
}
```

---

## 📊 Advanced Monitoring

### CloudWatch Metrics

Automatically collected metrics:

**Request Metrics:**
- `RequestCount` - Total requests to ALB
- `HTTPCode_Target_2XX_Count` - Successful responses
- `HTTPCode_Target_4XX_Count` - Client errors
- `HTTPCode_Target_5XX_Count` - Server errors

**Performance Metrics:**
- `TargetResponseTime` - Time to complete response
- `ActiveConnectionCount` - Open connections
- `NewConnectionCount` - New connections per interval

**Health Metrics:**
- `HealthyHostCount` - Healthy targets
- `UnHealthyHostCount` - Unhealthy targets

### Pre-configured Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| High 5xx Errors | > 10/min | Page on-call |
| High Response Time | > 1 sec avg | Investigate performance |
| High 4xx Errors | > 100/5min | Check client code |
| No Traffic | < 1/5min | Investigate connectivity |
| Unhealthy Targets | > 0 | Check target health |

### Creating Custom Dashboard

```bash
# View CloudWatch metrics in AWS Console
aws cloudwatch list-metrics \
  --namespace "AWS/ApplicationELB" \
  --query 'Metrics[*].[MetricName,Dimensions[*].[Name,Value]]' \
  --output table
```

### Access Logs

Enable detailed ALB access logging:

In `terraform/environments/prod.tfvars`:

```hcl
enable_alb_detailed_logging = true
```

This logs every request with:
- Client IP and port
- Request time and duration
- HTTP method and URL
- Status code
- Bytes sent/received
- User-Agent
- SSL cipher and protocol

Log location: `s3://nephele-hms-alb-logs-{account-id}/`

### Analyzing Logs

```bash
# Query last hour of logs
aws athena start-query-execution \
  --query-string "SELECT * FROM alb_logs WHERE date = '2024-01-23'" \
  --query-execution-context Database=default \
  --result-configuration OutputLocation=s3://query-results/

# Download and analyze locally
aws s3 cp s3://nephele-hms-alb-logs-{account-id}/ ./logs/ --recursive
cat logs/* | grep -i error | wc -l  # Count errors
```

---

## 🔀 Microservice Patterns

### Pattern 1: API Versioning

```
/api/v1/* → Version 1 (stable)
/api/v2/* → Version 2 (canary, 10% traffic)
```

**Implementation:**

```hcl
# Version 1 routing
resource "aws_lb_listener_rule" "api_v1" {
  condition {
    path_pattern { values = ["/api/v1/*"] }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_v1.arn
  }
}

# Version 2 weighted routing
resource "aws_lb_listener_rule" "api_v2" {
  condition {
    path_pattern { values = ["/api/v2/*"] }
  }
  action {
    type = "forward"
    forward {
      target_group {
        arn    = aws_lb_target_group.app_v1.arn  # Keep v1 as stable
        weight = 90
      }
      target_group {
        arn    = aws_lb_target_group.app_v2.arn  # v2 under test
        weight = 10
      }
    }
  }
}
```

### Pattern 2: Microservice Separation

```
/api/properties/* → Property Service
/api/bookings/*   → Booking Service
/api/payments/*   → Payment Service
/api/users/*      → User Service
```

**Implementation:**

```hcl
# Each service has its own target group
resource "aws_lb_listener_rule" "properties_service" {
  condition {
    path_pattern { values = ["/api/properties/*"] }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.properties_service.arn
  }
}

# Similar rules for bookings, payments, users
```

### Pattern 3: Admin/Management Separation

```
/api/* → Main API (public)
/admin/* → Admin API (internal)
```

**Implementation:**

```hcl
# Admin goes to separate service/container
resource "aws_lb_listener_rule" "admin" {
  condition {
    path_pattern { values = ["/admin/*"] }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.admin_service.arn
  }
}
```

### Pattern 4: Static Content

```
/static/* → S3 (via CloudFront, not ALB)
/assets/* → CDN
```

**Implementation:** Use CloudFront instead of ALB for static content to save bandwidth

---

## ⚙️ Configuration Examples

### Development Environment (dev.tfvars)

```hcl
# Minimal load balancing setup
enable_path_based_routing     = false
enable_canary_deployments     = false
alb_enable_https              = false
alb_certificate_arn           = ""
enable_alb_detailed_logging   = false
```

### Staging Environment (staging.tfvars)

```hcl
# Enable advanced features for testing
enable_path_based_routing     = true
enable_canary_deployments     = true
alb_enable_https              = true
alb_certificate_arn           = "arn:aws:acm:us-east-1:123456789:certificate/staging-cert"
enable_alb_detailed_logging   = false
canary_traffic_weight         = 10
```

### Production Environment (prod.tfvars)

```hcl
# Full advanced load balancing
enable_path_based_routing     = true
enable_canary_deployments     = true
alb_enable_https              = true
alb_certificate_arn           = "arn:aws:acm:us-east-1:123456789:certificate/prod-cert"
enable_alb_detailed_logging   = true
canary_traffic_weight         = 10
```

---

## 🔧 Troubleshooting

### Issue 1: "Certificate Not Found"

**Error:** Resource not found for ARN

**Solution:**
```bash
# List available certificates
aws acm list-certificates

# Request new certificate
aws acm request-certificate --domain-name yourdomain.com

# Wait for validation and copy ARN to tfvars
```

### Issue 2: Unhealthy Targets

**Error:** ALB shows 0/2 healthy targets

**Solution:**
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxxxxx

# Verify health check path
aws elbv2 describe-target-groups --names nephele-hms-tg

# Check application logs
aws logs tail /ecs/nephele-hms --follow

# Manually test health check
curl -s http://<ECS_IP>:8000/api/v1/health/
```

### Issue 3: 502 Bad Gateway

**Error:** ALB returns 502 for external requests

**Common causes:**
1. Security group blocking traffic
2. Target group health checks failing
3. Application not listening on correct port
4. ECS task not started

**Solution:**
```bash
# 1. Verify security groups allow ALB → ECS traffic
aws ec2 describe-security-groups --group-ids sg-alb-id sg-ecs-id

# 2. Check target health
aws elbv2 describe-target-health --target-group-arn $TG_ARN

# 3. Test application directly
ECS_IP=$(aws ecs describe-tasks ... | jq '.tasks[0].containerInstanceArn')
curl -s http://$ECS_IP:8000/

# 4. Check ECS task status
aws ecs describe-tasks --cluster nephele-hms --tasks <task-id>
```

### Issue 4: High Latency

**Symptom:** ALB response time > 1 second

**Causes:**
1. Slow application (database queries)
2. Insufficient resources (CPU/memory)
3. Network latency

**Solution:**
```bash
# Check application performance
aws logs tail /ecs/nephele-hms --follow
# Look for slow requests

# Check resource utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=nephele-hms-service

# Trigger auto-scaling if needed
aws application-autoscaling put-scaling-policy \
  --policy-name scale-up \
  --service-namespace ecs \
  --resource-id service/nephele-hms/nephele-hms-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration ...
```

### Issue 5: Canary Deployment Not Working

**Symptom:** All traffic goes to main, none to canary

**Causes:**
1. Canary target group not registered
2. Canary tasks not healthy
3. Routing rule not properly configured

**Solution:**
```bash
# Verify target groups exist
aws elbv2 describe-target-groups \
  --load-balancer-arn $ALB_ARN

# Check canary target health
aws elbv2 describe-target-health \
  --target-group-arn $CANARY_TG_ARN

# Verify listener rules
aws elbv2 describe-rules \
  --listener-arn $HTTPS_LISTENER_ARN

# If rules missing, reapply Terraform
make tf-apply-prod
```

---

## ⚡ Performance Tuning

### Connection Settings

```hcl
# Idle timeout (seconds)
enable_deletion_protection = false  # ALB timeouts

# Application-level keep-alive
resource "aws_lb_target_group" "app" {
  # Session stickiness for stateful applications
  stickiness {
    type            = "lb_cookie"
    enabled         = false  # Disable by default for stateless apps
    cookie_duration = 86400
  }
}
```

### Health Check Optimization

```hcl
health_check {
  healthy_threshold   = 2
  unhealthy_threshold = 3
  timeout             = 5
  interval            = 30
  path                = "/api/v1/health/"
  matcher             = "200-299"
}
```

**Tuning Tips:**
- Increase `healthy_threshold` to avoid flapping
- Decrease `interval` for faster failure detection (production only)
- Use specific health check path, not root "/"

### Target Group Register/Deregister

```bash
# Graceful drain time (deregister delay)
aws elbv2 modify-target-group-attributes \
  --target-group-arn $TG_ARN \
  --attributes Key=deregistration_delay.timeout_seconds,Value=30
```

---

## 🎓 Best Practices

### Load Balancing

1. **Use path-based routing** for microservices
2. **Implement health checks** at /health endpoint
3. **Enable access logs** for debugging
4. **Use HTTPS everywhere** in production
5. **Implement canary deployments** for safe rollouts

### Security

1. **Enable WAF** for protection against attacks
2. **Use security groups** with least privilege
3. **Implement HSTS** headers
4. **Rotate certificates** regularly
5. **Monitor access logs** for suspicious traffic

### Performance

1. **Tune health check intervals** for quick failure detection
2. **Use connection draining** for graceful shutdowns
3. **Monitor response times** and track trends
4. **Implement caching** at application level
5. **Use Route53** for DNS health checks

---

## 📞 Support & Next Steps

### After Gap #4 Implementation

1. Deploy advanced ALB configuration: `make tf-apply-prod`
2. Test path-based routing with sample requests
3. Set up canary deployment for next release
4. Monitor ALB metrics and alarms

### Before Gap #5 (Auto-Scaling)

1. Verify ALB health checks are accurate
2. Test scaling policies under load
3. Establish baseline performance metrics
4. Prepare load testing script

---

**Gap #4 Status:** ✅ Complete  
**Next:** Gap #5 - Advanced Auto-Scaling & Performance Tuning
