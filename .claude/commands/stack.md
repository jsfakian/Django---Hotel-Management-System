Manage the HMS Docker Compose development stack. Usage: /stack [action]

Actions:
- `up` → `make up` — start all services (django, postgres, redis, celery, monitoring)
- `down` → `make down` — stop and remove containers
- `restart` → `make restart` — down then up
- `logs` → `make logs` — tail last 200 lines and follow
- `ps` → `make ps` — show container status and health
- `clean` → `make clean` — remove all containers AND volumes (destructive — ask for confirmation first)
- `health` → check all service health endpoints: Django /health/, Prometheus /-/healthy, Grafana /api/health

After `up`, verify all containers are healthy before reporting success. List any unhealthy services.
After `down`, confirm all containers are stopped.
For `clean`, always confirm with the user before proceeding as it destroys all data volumes.
