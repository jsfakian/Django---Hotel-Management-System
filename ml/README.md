# ML packaging (pricing & forecasting)

| Path | Role |
|------|------|
| `algorithms/` | Training scripts, predictors, saved model artifacts |
| `data/` | Small synthetic CSVs + download helpers for experiments |

Django loads models from `ml/algorithms/models/pricing/` via `bookings/pricing_service.py`. Celery training tasks run scripts under `algorithms/` (`bookings/tasks.py`).

Import CSVs into Django:

```bash
cd nephele && python manage.py import_task3_data --data-dir ../ml/data
```

Large downloaded datasets under `data/real-data/` / `data/real_data/` are gitignored.
