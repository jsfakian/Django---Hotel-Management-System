Run code quality checks and formatting for the HMS project. Usage: /lint [action]

Actions:
- (none) or `check` → run `make lint` (flake8 + pylint, report issues without fixing)
- `format` → run `make format` (black + isort, auto-fix formatting)
- `all` → run `make format` then `make lint`

After running, summarise:
- Number of flake8 violations (if any)
- Number of pylint warnings/errors (if any)
- Files reformatted by black (if format was run)
- Files with import order changes by isort (if format was run)

If there are violations, list the top 5 most impactful ones with file paths and line numbers.
