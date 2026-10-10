# DB Schema Reconciliation Plan (Task 4)

Date: 2026-02-20

## Scope

Align the live Django schema in `HMS/db.sqlite3` with:
- `task4_design_schema.sql`
- current Django models in `HMS/*/models.py`

## Current Baseline (Verified)

### Applied migrations
- Applied app migrations are only:
  - `accounts: 0001_initial`
  - `analytics: 0001_initial`
  - `hotel: 0001_initial`
  - `notifications: 0001_initial`
  - `properties: 0001_initial`

### Missing critical migration application
- Not applied at all:
  - `properties: 0002_travelagency`
  - all `room` migrations (`0001`, `0002`, `0003`)
  - all `payments` migrations (`0001`)
  - all `bookings` migrations (`0001`)

### Live table inventory highlights
- Present legacy/partial tables:
  - `accounts_guest`, `accounts_employee`, `accounts_task`
  - `bookings_pricinghistory`, `bookings_demandforecast`, `bookings_competitorprice`
  - `custom_report`
  - `dashboard_executive_metrics`, `dashboard_operational_status`, `dashboard_revenue_metrics`, `dashboard_guest_analytics`
- Missing Task 4 analytics/reporting/forecasting tables:
  - `scheduled_reports`, `report_executions`, `report_delivery_tracking`
  - `occupancy_forecasts`, `revenue_forecasts`, `cancellation_predictions`, `noshow_predictions`, `forecasting_model_metrics`
- Missing core room/payment tables expected by current models:
  - `room_room`, `room_booking`
  - `payments_payment`, `payments_invoice`, etc.

## Root Causes

1. Major migration drift: model code evolved, but migrations were not consistently generated/applied.
2. Historical schema from old app versions remains in DB.
3. Naming mismatch between Task 4 SQL and Django default table naming (`users` vs `auth_user`, `bookings` vs `room_booking`, `pricing_history` vs `bookings_pricinghistory`).

## Reconciliation Strategy

Use a two-track plan:

### Track A (recommended for development/staging): deterministic reset

Fastest, lowest-risk path to a coherent schema if legacy data does not need to be preserved.

1) Backup DB
- Copy `HMS/db.sqlite3` to `HMS/db.sqlite3.bak-2026-02-20`.

2) Implement missing forward migrations before running migrate
- Add `accounts` schema-alignment migration (new file `accounts/migrations/0002_schema_alignment.py`) to:
  - introduce `Role` table if required by product scope
  - evolve `accounts_guest` from old `phoneNumber/user_id` shape to current fields (`email`, `first_name`, `last_name`, etc.)
  - evolve `accounts_employee` and `accounts_task` to current model fields
- Add `analytics` follow-up migration (new file `analytics/migrations/0002_forecasting_and_reporting_alignment.py`) to:
  - create missing tables: `scheduled_reports`, `report_executions`, `report_delivery_tracking`, `occupancy_forecasts`, `revenue_forecasts`, `cancellation_predictions`, `noshow_predictions`, `forecasting_model_metrics`
  - ensure dashboard tables match current models
- Add `bookings` alignment migration (new file `bookings/migrations/0002_task4_table_naming.py`) to decide naming strategy:
  - Option 1: keep Django default names
  - Option 2: set `PricingHistory.Meta.db_table = 'pricing_history'` and migrate/rename

3) Apply full migration graph from clean DB
- Delete `HMS/db.sqlite3`
- Run migrations in normal order via `python manage.py migrate`

4) Seed minimal reference data
- Create admin user
- Seed baseline `PaymentMethod`, `Role`, `Property`, `TravelAgency` records

5) Verify schema post-migrate
- Confirm presence of all required tables and indexes from Task 4 scope.

### Track B (data-preserving): staged in-place transformation

Use only if existing DB data must be preserved.

1) Add explicit `RunSQL`/`RunPython` migrations per app to transform in place.
2) Convert/rename old columns (`phoneNumber` -> modern profile fields, room legacy fields to new schema).
3) Backfill new non-null fields with safe defaults.
4) Create missing reporting/forecasting tables and foreign keys.
5) Validate referential integrity and then enforce stronger constraints.

This track is significantly more complex and should be executed with test fixtures and rollback rehearsals.

## Task 4 SQL Naming Alignment Decisions (Required)

You must choose one naming policy:

1) **Django-native naming (recommended)**
- Keep `auth_user`, `room_booking`, `bookings_pricinghistory` etc.
- Treat `task4_design_schema.sql` as conceptual.
- Optionally add compatibility SQL views named `users`, `bookings`, `pricing_history` for analytics tooling.

2) **Task 4 physical naming strict mode**
- Migrate Django models to `db_table` names exactly matching Task 4 (`users`, `bookings`, `pricing_history`, ...).
- Requires careful migration scripting and broader regression testing.

## Exact Migration Execution Order

If using Track A with reset:

1. Create/adjust migrations:
   - `properties` (use existing `0002_travelagency`)
   - `room` (existing `0001`, `0002`, `0003`)
   - `payments` (existing `0001`)
   - `accounts` (new `0002_schema_alignment`)
   - `analytics` (new `0002_forecasting_and_reporting_alignment`)
   - `bookings` (new `0002_task4_table_naming` if enforcing naming)
2. Recreate DB and run `migrate`
3. Run schema verification checks

## Verification Checklist

- `scheduled_reports`, `report_executions`, `report_delivery_tracking` exist.
- `occupancy_forecasts`, `revenue_forecasts`, `cancellation_predictions`, `noshow_predictions`, `forecasting_model_metrics` exist.
- `room_room`, `room_booking`, `payments_payment`, `payments_invoice` exist and are queryable.
- `properties_travelagency` exists and FKs resolve.
- No model import raises missing table errors.

## Risks

- Existing data loss (Track A).
- FK and nullability issues during in-place backfill (Track B).
- Naming strict-mode changes may break existing serializers/querysets/admin assumptions.

## Recommended Next Action

Proceed with Track A first in a disposable environment, then decide whether strict Task 4 table names are truly required or if compatibility views are sufficient.
