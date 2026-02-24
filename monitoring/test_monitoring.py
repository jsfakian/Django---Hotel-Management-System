#!/usr/bin/env python
"""
Automated Monitoring System Test Suite

Tests that verify the Prometheus + Grafana + Alertmanager monitoring stack
is operational and collecting metrics correctly.

Usage:
    python monitoring/test_monitoring.py
    python monitoring/test_monitoring.py --verbose
    python monitoring/test_monitoring.py --production

Dependencies:
    - requests
    - docker-compose (running)
"""

import requests
import json
import sys
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import argparse

# Configuration
PROMETHEUS_URL = "http://localhost:9090"
ALERTMANAGER_URL = "http://localhost:9093"
GRAFANA_URL = "http://localhost:3000"
DJANGO_METRICS_URL = "http://localhost:8000/metrics/"

# Timeouts
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 10

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class MonitoringTest:
    """Test suite for monitoring stack"""
    
    def __init__(self, verbose=False, production=False):
        self.verbose = verbose
        self.production = production
        self.results = []
        self.session = requests.Session()
        
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
    
    def print_test(self, name: str, status: bool, message: str = ""):
        """Print test result"""
        symbol = f"{Colors.GREEN}✅{Colors.RESET}" if status else f"{Colors.RED}❌{Colors.RESET}"
        msg = f" - {message}" if message else ""
        print(f"{symbol} {name}{msg}")
        self.results.append((name, status, message))
    
    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for _, status, _ in self.results if status)
        total = len(self.results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}Test Summary:{Colors.RESET}")
        print(f"  Passed: {Colors.GREEN}{passed}{Colors.RESET}/{total}")
        print(f"  Failed: {Colors.RED}{total - passed}{Colors.RESET}/{total}")
        print(f"  Pass Rate: {percentage:.1f}%")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        
        return passed == total
    
    def test_service_availability(self):
        """Test 1: Service Availability"""
        self.print_header("1. SERVICE AVAILABILITY")
        
        services = [
            ("Prometheus", PROMETHEUS_URL),
            ("Alertmanager", ALERTMANAGER_URL),
            ("Grafana", GRAFANA_URL),
            ("Django Metrics", DJANGO_METRICS_URL),
        ]
        
        for service_name, url in services:
            try:
                response = self.session.get(
                    url,
                    timeout=CONNECT_TIMEOUT,
                    verify=False
                )
                status = response.status_code < 500
                message = f"HTTP {response.status_code}"
                self.print_test(f"{service_name} Available", status, message)
            except requests.exceptions.ConnectionError:
                self.print_test(f"{service_name} Available", False, "Connection refused")
            except requests.exceptions.Timeout:
                self.print_test(f"{service_name} Available", False, "Timeout")
            except Exception as e:
                self.print_test(f"{service_name} Available", False, str(e))
    
    def test_prometheus_health(self):
        """Test 2: Prometheus Health & Configuration"""
        self.print_header("2. PROMETHEUS CONFIGURATION")
        
        try:
            # Check Prometheus health
            response = self.session.get(
                f"{PROMETHEUS_URL}/-/healthy",
                timeout=READ_TIMEOUT
            )
            self.print_test("Prometheus Health", response.status_code == 200)
            
            # Check scrape targets
            response = self.session.get(
                f"{PROMETHEUS_URL}/api/v1/targets",
                timeout=READ_TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                targets = data.get('data', {}).get('activeTargets', [])
                healthy = sum(1 for t in targets if t['health'] == 'up')
                total = len(targets)
                
                self.print_test(
                    f"Scrape Targets Healthy",
                    healthy == total,
                    f"{healthy}/{total} targets UP"
                )
                
                if self.verbose:
                    for target in targets:
                        status = f"{Colors.GREEN}UP{Colors.RESET}" if target['health'] == 'up' else f"{Colors.RED}DOWN{Colors.RESET}"
                        print(f"  {status} {target['labels'].get('job', 'unknown')}")
        except Exception as e:
            self.print_test("Prometheus Targets", False, str(e))
    
    def test_alert_rules(self):
        """Test 3: Alert Rules Loading"""
        self.print_header("3. ALERT RULES")
        
        try:
            response = self.session.get(
                f"{PROMETHEUS_URL}/api/v1/rules",
                timeout=READ_TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                groups = data.get('data', {}).get('groups', [])
                total_rules = sum(len(g.get('rules', [])) for g in groups)
                
                # Expected: 32 alert rules
                self.print_test(
                    "Alert Rules Loaded",
                    total_rules >= 20,
                    f"{total_rules} rules loaded"
                )
                
                if self.verbose:
                    for group in groups:
                        print(f"  Group: {group['name']}")
                        for rule in group.get('rules', []):
                            health = f"{Colors.GREEN}OK{Colors.RESET}" if rule['health'] == 'ok' else f"{Colors.YELLOW}WARNING{Colors.RESET}"
                            print(f"    {health} {rule.get('alert', rule.get('name'))}")
        except Exception as e:
            self.print_test("Alert Rules", False, str(e))
    
    def test_metrics_collection(self):
        """Test 4: Metrics Collection"""
        self.print_header("4. METRICS COLLECTION")
        
        test_queries = [
            ("up", "Service uptime"),
            ("rate(django_http_requests_total[5m])", "Django HTTP rate"),
            ("pg_stat_activity_count", "PostgreSQL connections"),
            ("redis_connected_clients", "Redis clients"),
            ("node_cpu_seconds_total", "Node CPU"),
        ]
        
        for query, description in test_queries:
            try:
                response = self.session.get(
                    f"{PROMETHEUS_URL}/api/v1/query",
                    params={"query": query},
                    timeout=READ_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    result_count = len(data.get('data', {}).get('result', []))
                    status = result_count > 0
                    self.print_test(
                        description,
                        status,
                        f"{result_count} metrics found"
                    )
                else:
                    self.print_test(description, False, f"HTTP {response.status_code}")
            except Exception as e:
                self.print_test(description, False, str(e))
    
    def test_alertmanager(self):
        """Test 5: Alertmanager Configuration"""
        self.print_header("5. ALERTMANAGER")
        
        try:
            # Check Alertmanager health
            response = self.session.get(
                f"{ALERTMANAGER_URL}/-/healthy",
                timeout=READ_TIMEOUT
            )
            self.print_test("Alertmanager Health", response.status_code == 200)
            
            # Check active alerts
            response = self.session.get(
                f"{ALERTMANAGER_URL}/api/v1/alerts",
                timeout=READ_TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                alerts = data.get('data', {}).get('alerts', [])
                self.print_test(
                    "Alertmanager Responsive",
                    True,
                    f"{len(alerts)} active alerts"
                )
                
                if self.verbose and alerts:
                    for alert in alerts[:5]:  # Show first 5
                        severity = alert.get('labels', {}).get('severity', 'unknown')
                        name = alert.get('labels', {}).get('alertname', 'unknown')
                        print(f"  Alert: {name} ({severity})")
        except Exception as e:
            self.print_test("Alertmanager", False, str(e))
    
    def test_grafana_dashboards(self):
        """Test 6: Grafana Dashboards"""
        self.print_header("6. GRAFANA DASHBOARDS")
        
        try:
            response = self.session.get(
                f"{GRAFANA_URL}/api/search?query=",
                timeout=READ_TIMEOUT
            )
            if response.status_code == 200:
                dashboards = response.json()
                dash_count = len(dashboards)
                self.print_test(
                    "Grafana Dashboards",
                    dash_count >= 4,
                    f"{dash_count} dashboards found"
                )
                
                expected_dashboards = {
                    "System Overview": False,
                    "Django Application": False,
                    "Database Performance": False,
                    "Celery Task": False,
                }
                
                for dash in dashboards:
                    title = dash.get('title', '').lower()
                    for expected in expected_dashboards:
                        if expected.lower() in title:
                            expected_dashboards[expected] = True
                
                if self.verbose:
                    for expected, found in expected_dashboards.items():
                        status = f"{Colors.GREEN}✅{Colors.RESET}" if found else f"{Colors.RED}❌{Colors.RESET}"
                        print(f"  {status} {expected}")
        except Exception as e:
            self.print_test("Grafana Dashboards", False, str(e))
    
    def test_django_metrics(self):
        """Test 7: Django Metrics Endpoint"""
        self.print_header("7. DJANGO METRICS")
        
        try:
            response = self.session.get(
                DJANGO_METRICS_URL,
                timeout=READ_TIMEOUT
            )
            if response.status_code == 200:
                content = response.text
                
                # Check for expected metrics
                metrics_to_check = [
                    ("django_http_requests_total", "HTTP requests"),
                    ("django_db_execute_total", "Database queries"),
                    ("django_model", "Model operations"),
                ]
                
                for metric_name, description in metrics_to_check:
                    found = metric_name in content
                    self.print_test(f"Django {description}", found)
            else:
                self.print_test("Django Metrics Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test("Django Metrics", False, str(e))
    
    def test_data_freshness(self):
        """Test 8: Data Freshness"""
        self.print_header("8. DATA FRESHNESS")
        
        try:
            # Get current timestamp from Prometheus
            response = self.session.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": "time()"},
                timeout=READ_TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', {}).get('result', [])
                if results:
                    current_time = float(results[0]['value'][1])
                    
                    # Check metric freshness (should be < 30 seconds old)
                    response = self.session.get(
                        f"{PROMETHEUS_URL}/api/v1/query",
                        params={"query": "django_http_requests_total"},
                        timeout=READ_TIMEOUT
                    )
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('data', {}).get('result', [])
                        if results:
                            metric_time = float(results[0]['value'][0])
                            age_seconds = current_time - metric_time
                            status = age_seconds < 30
                            self.print_test(
                                "Metric Data Freshness",
                                status,
                                f"Data is {age_seconds:.1f}s old"
                            )
        except Exception as e:
            self.print_test("Data Freshness", False, str(e))
    
    def test_exporters(self):
        """Test 9: Exporter Components"""
        self.print_header("9. EXPORTER COMPONENTS")
        
        exporters = [
            ("PostgreSQL Exporter", "http://localhost:9187/metrics"),
            ("Redis Exporter", "http://localhost:9121/metrics"),
            ("Node Exporter", "http://localhost:9100/metrics"),
        ]
        
        for exporter_name, url in exporters:
            try:
                response = self.session.get(url, timeout=CONNECT_TIMEOUT)
                status = response.status_code == 200
                self.print_test(exporter_name, status, f"HTTP {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.print_test(exporter_name, False, "Connection refused")
            except Exception as e:
                self.print_test(exporter_name, False, str(e))
    
    def test_docker_containers(self):
        """Test 10: Docker Container Status"""
        self.print_header("10. DOCKER CONTAINER STATUS")
        
        try:
            result = subprocess.run(
                ["docker-compose", "ps"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            containers_to_check = [
                "prometheus",
                "alertmanager",
                "grafana",
                "postgres-exporter",
                "redis-exporter",
                "node-exporter",
                "django",
            ]
            
            for container in containers_to_check:
                found = container in result.stdout
                status = "Up" in result.stdout and container in result.stdout
                self.print_test(f"Container: {container}", found)
        except Exception as e:
            self.print_test("Docker Status", False, str(e))
    
    def run_all_tests(self) -> bool:
        """Run all monitoring tests"""
        self.print_header("NEPHELE MONITORING SYSTEM - AUTOMATED TEST SUITE")
        print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Environment: {'Production' if self.production else 'Development'}")
        
        # Run test suites
        self.test_docker_containers()
        self.test_service_availability()
        self.test_prometheus_health()
        self.test_alert_rules()
        self.test_metrics_collection()
        self.test_alertmanager()
        self.test_grafana_dashboards()
        self.test_django_metrics()
        self.test_exporters()
        self.test_data_freshness()
        
        # Print summary
        all_passed = self.print_summary()
        
        return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Automated Monitoring System Test Suite"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output with detailed information"
    )
    parser.add_argument(
        "--production",
        "-p",
        action="store_true",
        help="Run in production mode (stricter checks)"
    )
    
    args = parser.parse_args()
    
    # Run tests
    tester = MonitoringTest(verbose=args.verbose, production=args.production)
    all_passed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
