# Makefile Migrations - Quick Reference

**Updated**: February 20, 2026  
**Status**: ✅ Ready to Use

## Overview

The Makefile has been updated with proper migration commands for Docker. All keys are configured and tested.

## Quick Commands

### Create Migrations (When Models Change)
```bash
make makemigrations
```
Creates new migration files from model changes (no database changes yet).

### Apply Migrations to Database
```bash
make migrate
```
Applies all pending migrations to the database.

### Combined: Create & Apply
```bash
make makemigrations  # Step 1
make migrate         # Step 2
```

### View Migration Status
```bash
docker compose exec django python manage.py showmigrations
docker compose exec django python manage.py showmigrations payments
```

## Full Workflow Example

### Step 1: Start Containers
```bash
make up
```

### Step 2: Create New Migrations (if needed)
```bash
make makemigrations app_name
```

### Step 3: Apply Migrations
```bash
make migrate
```

### Step 4: Bootstrap Metadata (first time only)
```bash
make bootstrap
```

### Step 5: Create Admin User
```bash
make create-admin
```

## Current Migration Status

**Payments App**:
```
✓ 0001_initial              [Applied]
✓ 0002_add_mydata_fields    [Applied] ← MyData Integration
```

## All Available Database Commands

| Command | Purpose |
|---------|---------|
| `make makemigrations` | Create migration files from model changes |
| `make migrate` | Apply pending migrations to database |
| `make bootstrap` | Initialize metadata tables |
| `make create-admin` | Create superuser admin account |
| `make check` | Run Django system checks |

## Makefile Help

View all available commands:
```bash
make help
```

## Examples

### Create Migration for Invoices
```bash
# 1. Modify invoice model in HMS/payments/models.py
# 2. Create migration
make makemigrations

# 3. Apply migration
make migrate

# 4. Verify
docker compose exec django python manage.py showmigrations payments
```

### Apply All Pending Migrations
```bash
make migrate
```

### Check for Migration Issues
```bash
make check
```

## Behind the Scenes

The Makefile rules use docker compose to run Django management commands inside the container:

```makefile
makemigrations:
    $(COMPOSE) exec django python manage.py makemigrations

migrate:
    $(COMPOSE) exec django python manage.py migrate --noinput

bootstrap:
    $(COMPOSE) exec django python manage.py bootstrap_metadata

create-admin:
    $(COMPOSE) exec django bash -c "python manage.py shell <<'PY'..."
```

## Troubleshooting

### Containers Not Running
```bash
make up
```

### See Detailed Migration Info
```bash
docker compose exec django python manage.py migrate --plan
```

### Rollback Last Migration
```bash
docker compose exec django python manage.py migrate app_name 0001
```

### Force Specific Migration
```bash
docker compose exec django python manage.py migrate app_name 0002
```

## Tips

1. **Always run migrations after pulling code**: `make migrate`
2. **Create migrations with descriptive names**: Django auto-names them usually
3. **Check migration syntax**: `make check`
4. **Never manually edit migration files** (unless you know what you're doing)
5. **Test migrations locally first** before production

## Integration with Invoice Changes

When you modify the Invoice model:

```python
# 1. Make model changes in HMS/payments/models.py
class Invoice(models.Model):
    # ... add new fields here ...
    mydata_new_field = models.CharField(...)

# 2. Create migration
$ make makemigrations
# Creates: payments/migrations/0003_invoice_mydata_new_field.py

# 3. Apply migration
$ make migrate
# Updates database with new field

# 4. Update forms (if needed)
# HMS/payments/forms.py - add field to InvoiceForm

# 5. Test in browser
# Go to /portal/invoices/create/ to verify
```

## Reference

- **Makefile Location**: `/home/jsfakian/Documents/src/Django---Hotel-Management-System/Makefile`
- **Django Docs**: https://docs.djangoproject.com/en/4.2/topics/migrations/
- **Current Project**: HMS (Hotel Management System)
- **Database**: PostgreSQL 15 (in container)

---

✅ **All migration commands working via Makefile**
