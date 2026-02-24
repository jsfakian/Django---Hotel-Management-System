#!/bin/bash
# Automated Monitoring System Test Script
# 
# Tests Prometheus + Grafana + Alertmanager stack
# 
# Usage: ./monitoring/test_monitoring.sh
# Or:    bash monitoring/test_monitoring.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROMETHEUS_URL="http://localhost:9090"
ALERTMANAGER_URL="http://localhost:9093"
GRAFANA_URL="http://localhost:3000"
DJANGO_METRICS_URL="http://localhost:8000/metrics/"

# Test counters
PASSED=0
FAILED=0
TOTAL=0

# Functions
print_header() {
    echo -e "\n${BOLD}${BLUE}================================================================${NC}"
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BOLD}${BLUE}================================================================${NC}\n"
}

print_test() {
    local name=$1
    local status=$2
    local message=$3
    
    TOTAL=$((TOTAL + 1))
    
    if [ "$status" = "PASS" ]; then
        PASSED=$((PASSED + 1))
        echo -e "${GREEN}✅${NC} $name"
    else
        FAILED=$((FAILED + 1))
        echo -e "${RED}❌${NC} $name"
    fi
    
    if [ ! -z "$message" ]; then
        echo -e "   ${YELLOW}$message${NC}"
    fi
}

check_service() {
    local name=$1
    local url=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        print_test "Service: $name" "PASS" "Responding"
    else
        print_test "Service: $name" "FAIL" "Not responding or error"
    fi
}

# Main tests
main() {
    echo -e "${BOLD}NEPHELE MONITORING SYSTEM - AUTOMATED TEST SUITE${NC}"
    echo "Test started: $(date)"
    
    # Test 1: Service Availability
    print_header "1. SERVICE AVAILABILITY"
    check_service "Prometheus" "$PROMETHEUS_URL"
    check_service "Alertmanager" "$ALERTMANAGER_URL"
    check_service "Grafana" "$GRAFANA_URL"
    check_service "Django Metrics" "$DJANGO_METRICS_URL"
    
    # Test 2: Prometheus Health
    print_header "2. PROMETHEUS HEALTH"
    if curl -s -f "$PROMETHEUS_URL/-/healthy" > /dev/null 2>&1; then
        print_test "Prometheus Health Check" "PASS"
    else
        print_test "Prometheus Health Check" "FAIL"
    fi
    
    # Test 3: Prometheus Targets
    print_header "3. PROMETHEUS TARGETS"
    TARGETS=$(curl -s "$PROMETHEUS_URL/api/v1/targets" 2>/dev/null | grep -o '"health":"up"' | wc -l)
    if [ "$TARGETS" -gt 0 ]; then
        print_test "Prometheus Targets" "PASS" "$TARGETS targets UP"
    else
        print_test "Prometheus Targets" "FAIL" "No targets UP"
    fi
    
    # Test 4: Alert Rules
    print_header "4. ALERT RULES"
    RULES=$(curl -s "$PROMETHEUS_URL/api/v1/rules" 2>/dev/null | grep -o '"alert":' | wc -l)
    if [ "$RULES" -gt 10 ]; then
        print_test "Alert Rules Loaded" "PASS" "$RULES rules loaded"
    else
        print_test "Alert Rules Loaded" "FAIL" "Only $RULES rules (expected >10)"
    fi
    
    # Test 5: Metrics Collection
    print_header "5. METRICS COLLECTION"
    if curl -s "$DJANGO_METRICS_URL" 2>/dev/null | grep -q "django_http_requests_total"; then
        print_test "Django HTTP Metrics" "PASS"
    else
        print_test "Django HTTP Metrics" "FAIL"
    fi
    
    # Test 6: Alertmanager Health
    print_header "6. ALERTMANAGER HEALTH"
    if curl -s -f "$ALERTMANAGER_URL/-/healthy" > /dev/null 2>&1; then
        print_test "Alertmanager Health" "PASS"
    else
        print_test "Alertmanager Health" "FAIL"
    fi
    
    # Test 7: Grafana Dashboard Count
    print_header "7. GRAFANA DASHBOARDS"
    DASHBOARDS=$(curl -s "$GRAFANA_URL/api/search?query=" 2>/dev/null | grep -o '"title"' | wc -l)
    if [ "$DASHBOARDS" -gt 0 ]; then
        print_test "Grafana Dashboards" "PASS" "$DASHBOARDS dashboards found"
    else
        print_test "Grafana Dashboards" "FAIL"
    fi
    
    # Test 8: Docker Containers
    print_header "8. DOCKER CONTAINERS"
    
    # Check if docker-compose is available
    if command -v docker-compose &> /dev/null; then
        RUNNING=$(docker-compose ps --filter "status=running" 2>/dev/null | grep -c "Up" || echo "0")
        if [ "$RUNNING" -gt 0 ]; then
            print_test "Docker Containers Running" "PASS" "$RUNNING containers UP"
        else
            print_test "Docker Containers Running" "FAIL" "No containers running"
        fi
    else
        print_test "Docker Compose" "FAIL" "docker-compose not found"
    fi
    
    # Test 9: Exporters
    print_header "9. EXPORTER SERVICES"
    check_service "PostgreSQL Exporter" "http://localhost:9187/metrics"
    check_service "Redis Exporter" "http://localhost:9121/metrics"
    check_service "Node Exporter" "http://localhost:9100/metrics"
    
    # Summary
    print_header "TEST SUMMARY"
    PERCENTAGE=$((PASSED * 100 / TOTAL))
    
    echo -e "Passed: ${GREEN}$PASSED${NC}/$TOTAL"
    echo -e "Failed: ${RED}$FAILED${NC}/$TOTAL"
    echo -e "Pass Rate: $PERCENTAGE%"
    
    if [ "$FAILED" -eq 0 ]; then
        echo -e "\n${GREEN}${BOLD}✅ All monitoring services operational!${NC}"
        echo "Monitoring stack is ready for use."
        echo ""
        echo "Access points:"
        echo "  Prometheus:  $PROMETHEUS_URL"
        echo "  Alertmanager: $ALERTMANAGER_URL"
        echo "  Grafana:     $GRAFANA_URL (admin/admin123)"
        echo ""
        return 0
    else
        echo -e "\n${RED}${BOLD}❌ Some tests failed. Check services and logs.${NC}"
        return 1
    fi
}

# Run main
main
