Run the project test suite. Usage: /test [scope]

Scope options:
- (none) → `make test` — full suite
- `unit` → `make test-unit`
- `integration` → `make test-integration`
- `e2e` → `make test-e2e`
- `cov` → `make test-cov` (with coverage report, target 82%+)
- `gdpr` → `make test-gdpr`
- `monitoring` → `make test-monitoring`
- `fast` → `make test-fast` (skip slow/performance)
- `failed` → `make test-failed` (re-run last failures)
- `all` → `make test-all` (pytest + GDPR + monitoring)

Run the appropriate make target based on the scope argument. After the run, report: total tests, passed, failed, and coverage percentage if available. If tests fail, show the failure summary.
