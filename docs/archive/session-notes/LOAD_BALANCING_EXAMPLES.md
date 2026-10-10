# Load Balancing Configuration Examples
## Real-World Scenarios for ALB Path-Based Routing

This file contains practical examples of different ALB routing configurations you can use with Gap #4.

---

## 📐 Scenario 1: API Versioning with Canary Deployments

**Use Case:** Safely roll out new API version to small subset of users

```hcl
# Terraform configuration

# Target groups
resource "aws_lb_target_group" "api_v1" {
  name        = "hms-api-v1"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/api/v1/health/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }
}

resource "aws_lb_target_group" "api_v2_beta" {
  name        = "hms-api-v2-beta"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/api/v2/health/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }
}

# Routing: /api/v1/* goes to stable v1 (100%)
resource "aws_lb_listener_rule" "api_v1_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 1

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_v1.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/*"]
    }
  }
}

# Routing: /api/v2/* goes to weighted targets (90% v1, 10% v2 beta)
resource "aws_lb_listener_rule" "api_v2_canary_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 2

  action {
    type = "forward"

    forward {
      target_group {
        arn    = aws_lb_target_group.api_v1.arn
        weight = 90  # 90% to stable v1 for backward compatibility
      }

      target_group {
        arn    = aws_lb_target_group.api_v2_beta.arn
        weight = 10  # 10% to new v2 for testing
      }
    }
  }

  condition {
    path_pattern {
      values = ["/api/v2/*"]
    }
  }
}
```

**Deployment:**

```bash
# Step 1: Deploy v2 to beta target group
docker tag hms:latest $ECR_REPO:v2-beta
docker push $ECR_REPO:v2-beta

aws ecs register-task-definition \
  --family hms-api-v2 \
  --container-definitions '[{"name":"hms","image":"'$ECR_REPO':v2-beta","port":8000}]'

# Step 2: Apply Terraform to create routing
make tf-apply-prod

# Step 3: Monitor metrics
watch -n 5 'aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --start-time $(date -u -d "5 min ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum'

# Step 4: Increase canary weight
# Edit prod.tfvars: canary_traffic_weight = 25
make tf-apply-prod

# Step 5: Promote to full rollout
# Edit prod.tfvars: canary_traffic_weight = 100
make tf-apply-prod

# Step 6: Decommission old version
# Remove v1 from target group
```

---

## 🏢 Scenario 2: Microservice Architecture

**Use Case:** Different backend services for different API endpoints

```hcl
# Target groups for each microservice

resource "aws_lb_target_group" "bookings_service" {
  name        = "hms-bookings-service"
  port        = 8001
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path = "/health/"
  }
}

resource "aws_lb_target_group" "properties_service" {
  name        = "hms-properties-service"
  port        = 8002
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path = "/health/"
  }
}

resource "aws_lb_target_group" "payments_service" {
  name        = "hms-payments-service"
  port        = 8003
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path = "/health/"
  }
}

resource "aws_lb_target_group" "users_service" {
  name        = "hms-users-service"
  port        = 8004
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path = "/health/"
  }
}

# Routing rules for each service

resource "aws_lb_listener_rule" "bookings_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.bookings_service.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/bookings/*"]
    }
  }
}

resource "aws_lb_listener_rule" "properties_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 11

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.properties_service.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/properties/*"]
    }
  }
}

resource "aws_lb_listener_rule" "payments_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 12

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.payments_service.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/payments/*"]
    }
  }
}

resource "aws_lb_listener_rule" "users_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 13

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.users_service.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/users/*"]
    }
  }
}
```

**Deployment:**

```bash
# Each service deployed independently
docker build -f Dockerfile.bookings -t bookings:latest .
docker tag bookings:latest $ECR_REPO/bookings:latest
docker push $ECR_REPO/bookings:latest

# Create ECS service for bookings
aws ecs create-service \
  --cluster nephele-hms-cluster \
  --service-name hms-bookings-service \
  --task-definition hms-bookings:1 \
  --desired-count 2 \
  --load-balancers targetGroupArn=$BOOKINGS_TG_ARN,containerName=bookings,containerPort=8001

# Repeat for other services...
```

**Benefits:**
- Independent scaling per service
- Independent deployments (no monolith lockstep)
- Separate team ownership
- Fault isolation (one service down doesn't affect others)

---

## 🎯 Scenario 3: Admin & Public API Separation

**Use Case:** Admin panel on same ALB but with different backends

```hcl
# Public API target group
resource "aws_lb_target_group" "public_api" {
  name        = "hms-public-api"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
}

# Admin API target group (different container, same code)
resource "aws_lb_target_group" "admin_api" {
  name        = "hms-admin-api"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
}

# Routing rules

resource "aws_lb_listener_rule" "admin_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 1

  action {
    type = "forward"

    forward {
      target_group {
        arn = aws_lb_target_group.admin_api.arn
      }
    }
  }

  condition {
    path_pattern {
      values = ["/admin/*"]
    }
  }
}

resource "aws_lb_listener_rule" "public_api_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100  # Lower priority, matches /api/*

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.public_api.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
```

**In Django Application:**

```python
# Detect if request is for admin
def get_allowed_models(request):
    if request.path.startswith('/admin/'):
        # Admin API - return all models
        return ['properties', 'bookings', 'payments', 'users']
    else:
        # Public API - return limited models
        return ['properties', 'bookings']

# Or use separate Django services entirely:
# - hms-api (public) - limited models exposed
# - hms-admin (admin) - full models exposed
```

---

## 🚀 Scenario 4: Feature Flags with Load Balancing

**Use Case:** Test new features with subset of users using ALB routing

```hcl
# Target group for users with feature X enabled
resource "aws_lb_target_group" "feature_x_enabled" {
  name        = "hms-feature-x-enabled"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
}

# Target group for users without feature X (default)
resource "aws_lb_target_group" "feature_x_disabled" {
  name        = "hms-feature-x-disabled"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
}

# Route based on custom header or hostname
# Note: ALB supports header-based routing with conditions

resource "aws_lb_listener_rule" "feature_x_test" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 1

  action {
    type = "forward"

    forward {
      target_group {
        arn    = aws_lb_target_group.feature_x_enabled.arn
        weight = 5  # 5% of traffic
      }

      target_group {
        arn    = aws_lb_target_group.feature_x_disabled.arn
        weight = 95  # 95% of traffic
      }
    }
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }

  # Optional: Route only specific users
  # condition {
  #   http_header {
  #     http_header_name = "X-Feature-Group"
  #     values           = ["beta-testers"]
  #   }
  # }
}
```

---

## 📊 Scenario 5: Monitoring & Analytics

**Use Case:** Route analytics requests to dedicated service

```hcl
resource "aws_lb_target_group" "analytics_api" {
  name        = "hms-analytics-api"
  port        = 8005
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path = "/health/"
    # Slower health check for analytics service
    interval = 60
  }
}

resource "aws_lb_listener_rule" "analytics_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 5

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.analytics_api.arn
  }

  condition {
    path_pattern {
      values = ["/api/v1/analytics/*", "/api/v1/reports/*"]
    }
  }
}

# Separate monitoring from main application
# Benefits:
# - Heavy analytics queries don't slow down main API
# - Can scale analytics service independently
# - Can use different compute resources
```

---

## 🔄 Scenario 6: Blue-Green Deployment

**Use Case:** Zero-downtime deployments by swapping entire environments

```bash
# Blue environment (current production)
BLUE_TG_ARN="arn:aws:elasticloadbalancing:..."

# Green environment (new version, prepared in parallel)
GREEN_TG_ARN="arn:aws:elasticloadbalancing:..."

# Current routing: 100% to blue
weight_blue=100
weight_green=0

# Test green (100% to green for internal testing)
weight_blue=0
weight_green=100

# If green passes all tests, swap permanently
# Update Terraform:
```

```hcl
resource "aws_lb_listener_rule" "blue_green" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 1

  action {
    type = "forward"

    forward {
      target_group {
        arn    = aws_lb_target_group.blue_production.arn
        weight = 100  # Change to 0 for full green
      }

      target_group {
        arn    = aws_lb_target_group.green_staging.arn
        weight = 0    # Change to 100 for full green
      }
    }
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}
```

**Deployment Steps:**

```bash
# 1. Deploy new version to green environment
# 2. Run smoke tests against green (internal routing)
# 3. Swap weights: blue=0, green=100
# 4. Monitor production traffic
# 5. If issues, swap back: blue=100, green=0
# 6. Once stable, clean up blue
```

---

## 📱 Scenario 7: Mobile API vs Web API

**Use Case:** Different response formats and endpoints for mobile vs web

```hcl
resource "aws_lb_target_group" "web_api" {
  name        = "hms-web-api"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
}

resource "aws_lb_target_group" "mobile_api" {
  name        = "hms-mobile-api"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
}

# Route based on User-Agent header
# Note: ALB doesn't support User-Agent header matching directly
# Alternative: Use separate domains or query parameters

resource "aws_lb_listener_rule" "mobile_api_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 1

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.mobile_api.arn
  }

  condition {
    path_pattern {
      values = ["/api/mobile/*"]
    }
  }
}

resource "aws_lb_listener_rule" "web_api_route" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 2

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web_api.arn
  }

  condition {
    path_pattern {
      values = ["/api/web/*"]
    }
  }
}
```

---

## 🏗️ Implementation Checklist

After choosing your routing scenario:

- [ ] Define target groups in Terraform
- [ ] Create listener rules with correct priorities
- [ ] Deploy backends to respective target groups
- [ ] Test each routing path
- [ ] Set up monitoring and alarms
- [ ] Document routing architecture
- [ ] Train team on deployment procedures
- [ ] Test failover/recovery scenarios

---

## 📚 Related Documentation

- [LOAD_BALANCING_GUIDE.md](LOAD_BALANCING_GUIDE.md) - Complete ALB guide
- [TERRAFORM_GUIDE.md](TERRAFORM_GUIDE.md) - Terraform configuration
- [terraform/load-balancing.tf](terraform/load-balancing.tf) - ALB Terraform code

---

**Need help?** Review the LOAD_BALANCING_GUIDE.md troubleshooting section or check CloudWatch logs:

```bash
aws logs tail /ecs/nephele-hms --follow
```
