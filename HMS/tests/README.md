# HMS Test Suite Guide

Complete testing infrastructure for Django Hotel Management System

## Overview

This test suite implements comprehensive testing coverage across:
- **Unit Tests**: Models, Serializers, Views, Services (70%)
- **Integration Tests**: Multi-component workflows (20%)
- **E2E Tests**: Complete user journeys (5%)
- **Performance Tests**: Load and stress testing (5%)

## Test Coverage Targets

| Test Type | Backend | Target |
|-----------|---------|--------|
| Unit Tests | 85%+ | MODELS, SERIALIZERS |
| Integration | 60%+ | WORKFLOWS, APIS |
| E2E Tests | 40% of flows | CRITICAL PATHS |
| Performance | Load tested | < 200ms p95 |

## Directory Structure

```
HMS/
├── tests/
│   ├── __init__.py
│   ├── models/                    # Model unit tests
│   │   ├── test_room_model.py
│   │   ├── test_booking_model.py
│   │   ├── test_account_models.py
│   │   └── test_payment_models.py
│   ├── serializers/               # Serializer tests
│   │   └── test_serializers.py
│   ├── views/                     # API endpoint tests
│   │   └── test_views.py
│   ├── services/                  # Business logic tests
│   │   └── test_services.py
│   ├── integration/               # Workflow tests
│   │   └── test_workflows.py
│   ├── e2e_base.py               # E2E test base classes
│   └── test_performance.py        # Load/performance tests
├── conftest.py                    # Pytest configuration
├── pytest.ini                     # Pytest settings
└── .coveragerc                    # Coverage settings
```

## Running Tests

### Prerequisites

```bash
# Install testing dependencies
pip install pytest pytest-django pytest-cov

# For E2E tests (Selenium-based)
pip install selenium

# For performance tests
pip install locust
```

### Run All Tests

```bash
# Run all tests with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -v

# Run specific test file
pytest HMS/tests/models/test_room_model.py

# Run specific test class
pytest HMS/tests/models/test_room_model.py::RoomModelTests

# Run specific test method
pytest HMS/tests/models/test_room_model.py::RoomModelTests::test_room_creation_with_valid_data
```

### Run Tests by Category

```bash
# Unit tests only
pytest HMS/tests/models/ HMS/tests/serializers/ HMS/tests/views/

# Integration tests
pytest HMS/tests/integration/

# E2E tests
pytest HMS/tests/e2e_base.py

# Performance tests
pytest HMS/tests/test_performance.py

# Marked tests
pytest -m unit              # Run unit tests
pytest -m integration       # Run integration tests
pytest -m e2e              # Run E2E tests
pytest -m performance      # Run performance tests
pytest -m "not slow"       # Skip slow tests
```

### Continuous Integration

```bash
# Run tests with CI settings
pytest --junitxml=test-results.xml --cov=. --cov-report=xml

# Generate HTML coverage report
pytest --cov=. --cov-report=html
  # Open: htmlcov/index.html in browser
```

## Test Categories

### Unit Tests (70% of pyramid)

Tests for individual components in isolation.

**Models** (`HMS/tests/models/`)
- Room creation and properties
- Booking validation and status transitions
- Guest information and preferences
- Payment and Invoice calculations

**Serializers** (`HMS/tests/serializers/`)
- Valid data serialization
- Required field validation
- Nested object handling
- JSON field serialization

**Views** (`HMS/tests/views/`)
- GET /api/bookings/ - list, filtering, paging
- POST /api/bookings/ - create with validation
- PUT /api/bookings/{id}/ - update
- DELETE /api/bookings/{id}/ - delete
- Authentication and permissions

**Services** (`HMS/tests/services/`)
- BookingService: availability checking, price calculation
- PaymentService: payment processing, refunds
- NotificationService: event routing
- PricingService: dynamic pricing logic

### Integration Tests (20% of pyramid)

Tests for workflows involving multiple components.

**Booking Workflow** (`tests/integration/test_workflows.py`)
1. Search available rooms
2. Create booking
3. Verify booking created
4. Process payment
5. Generate invoice
6. Send confirmation

**Payment Processing**
1. Create payment record
2. Call payment gateway
3. Verify transaction ID
4. Update booking status
5. Send receipt
6. Reconcile with accounting

**Notification Integration**
1. Create booking (trigger event)
2. System creates notification
3. Email service queues message
4. Background task sends email
5. Track delivery status

### E2E Tests (5% - Critical Paths)

Complete user journeys through the system.

**Guest Booking Journey** (`HMS/tests/e2e_base.py`)
1. User registers account
2. Search for available rooms
3. View room details
4. Create booking
5. Enter guest information
6. Select payment method
7. Complete booking
8. Receive confirmation

**Manager Dashboard**
1. Login as manager
2. View KPIs dashboard
3. Check occupancy calendar
4. Update room rates
5. Generate revenue report
6. View guest feedback

**Receptionist Check-in**
1. Login as receptionist
2. Search guest by reservation
3. View check-in form
4. Collect guest information
5. Process payment if needed
6. Issue room access
7. Complete check-in

### Performance Tests

Load and stress testing scenarios.

**Normal Load**: 100 concurrent users
- Target response time: 200ms (p95)
- Acceptable: 500ms

**Peak Load**: 500 concurrent users
- Target response time: 500ms (p95)
- Acceptable: 1000ms

**Stress Test**: Gradually increase until failure
- Identify breaking point
- Analyze bottlenecks
- Optimize as needed

**Metrics Monitored**:
- Response time (p50, p95, p99)
- Throughput (requests/second)
- Error rate
- CPU usage
- Memory usage

## Coverage Report

Generate coverage report:

```bash
# Terminal report
pytest --cov=. --cov-report=term-missing

# HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov=. --cov-report=xml
```

## Test Data

Test fixtures and factories in `HMS/fixtures/`:
- Users and authentication
- Properties and rooms
- Bookings and payments
- Sample data for testing

## Common Test Patterns

### Model Test Template

```python
from django.test import TestCase
from myapp.models import MyModel

class MyModelTests(TestCase):
    def setUp(self):
        """Create test data"""
        self.obj = MyModel.objects.create(...)
    
    def test_object_creation(self):
        """Test creating object with valid data"""
        self.assertEqual(self.obj.name, 'test')
    
    def test_field_validation(self):
        """Test field constraints"""
        with self.assertRaises(Exception):
            MyModel.objects.create(invalid_data)
```

### API Test Template

```python
from rest_framework.test import APITestCase
from rest_framework import status

class MyViewSetTests(APITestCase):
    def setUp(self):
        """Create test data and client"""
        self.client = APIClient()
    
    def test_list_endpoint(self):
        """Test GET /api/resource/"""
        response = self.client.get('/api/resource/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

### Integration Test Template

```python
from django.test import TransactionTestCase

class WorkflowTests(TransactionTestCase):
    def test_complete_workflow(self):
        """Test complete business process"""
        # Step 1: Create initial data
        # Step 2: Perform operation
        # Step 3: Verify result
        # Step 4: Check side effects
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.10
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest --junitxml=test-results.xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Debugging Tests

### Run with Debugging

```bash
# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Verbose output
pytest -vv
```

### Common Issues

**Test Isolation**
- Use TransactionTestCase for tests that need transaction support
- Clear cache between tests
- Use setUp/tearDown properly

**Flaky Tests**
- Avoid time-dependent assertions
- Use freeze_gun for time mocking
- Ensure test data independence

**Performance**
- Use --durations=10 to find slow tests
- Mark slow tests with @pytest.mark.slow
- Use fixtures to share expensive setup

## Best Practices

1. **Test Independence**: Each test should be independent
2. **Clear Names**: Use descriptive test names
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **DRY**: Use setUp/fixtures to avoid duplication
5. **Fast**: Unit tests should run quickly
6. **Isolated**: Mock external dependencies
7. **Comprehensive**: Test happy path AND error cases
8. **Documented**: Comment complex test logic

## Maintenance

- Review and update tests when requirements change
- Keep test coverage above 80%
- Refactor tests as code evolves
- Archive/remove obsolete tests
- Monitor test execution time

## Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [Django REST Framework Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
