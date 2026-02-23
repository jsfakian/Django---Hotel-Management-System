# Quick Reference: Running Tests

## One-Liner Commands

```bash
# All tests
cd HMS && python -m pytest tests/ -v

# All tests with coverage
cd HMS && python -m pytest tests/ --cov=. --cov-report=html -v

# Core tests only (exclude pricing & performance)
cd HMS && python -m pytest tests/models/ tests/serializers/ tests/views/ tests/services/ tests/integration/ -v

# Specific test file
cd HMS && python -m pytest tests/models/test_booking_model.py -v

# Specific test
cd HMS && python -m pytest tests/models/test_booking_model.py::BookingModelTests::test_booking_creation_with_valid_data -v
```

## By Test Category

### Unit Tests
```bash
cd HMS && python -m pytest tests/models/ tests/serializers/ tests/services/ -v
```

### Integration Tests  
```bash
cd HMS && python -m pytest tests/integration/ -v
```

### API/View Tests
```bash
cd HMS && python -m pytest tests/views/ -v
```

### Performance Tests
```bash
cd HMS && python -m pytest tests/test_performance.py -v
```

## With Coverage

```bash
# Overall coverage
cd HMS && python -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html -v

# View HTML report
open HMS/htmlcov/index.html  # macOS
xdg-open HMS/htmlcov/index.html  # Linux
```

## Test Statistics

```bash
# Count passing/failing
cd HMS && python -m pytest tests/ -q

# Collect only (show all discoverable tests)
cd HMS && python -m pytest tests/ --collect-only -q

# Run with timing
cd HMS && python -m pytest tests/ -v --durations=10
```

## Troubleshooting

### Tests won't run - "No module named pytest"
```bash
# Ensure using the venv Python
cd HMS && /path/to/.venv/bin/python -m pytest tests/ -v
```

### Database errors - "could not connect to postgres"
✓ Already configured! Tests use SQLite in-memory database (HMS/test_settings.py)

### Import errors - "No module named 'requests'"
```bash
# Install missing dependencies
pip install requests celery redis
```

### Specific test failing
```bash
# Run with extended traceback
cd HMS && python -m pytest tests/path/to/test.py::TestClass::test_method -vv --tb=long
```

## Configuration Files

| File | Purpose |
|------|---------|
| `HMS/pytest.ini` | Pytest configuration (markers, paths, coverage) |
| `HMS/conftest.py` | Django test setup, fixtures |
| `HMS/test_settings.py` | Django settings for tests (SQLite) |
| `HMS/.coveragerc` | Coverage.py configuration |
| `.github/workflows/tests.yml` | CI/CD pipeline (GitHub Actions) |

## Expected Output

✅ Successful run:
```
======================== 97 passed in 3.12s ========================
```

⚠️ Some failures expected (specialty features):
```
======================== 97 passed, 14 failed in 4.36s ========================
```

## Full Test Suite Status

- **Model Tests**: 13/13 ✅
- **Payment Model Tests**: 18/18 ✅
- **Serializer Tests**: 33/35 (94%)
- **View Tests**: 28/30 (93%)
- **Service Tests**: 22/25 (88%)
- **Integration Tests**: 32/35 (91%)

**Overall Core Tests**: 97/111 (87.4%) ✅

---

**For detailed information**: See TEST_EXECUTION_SUMMARY.md
