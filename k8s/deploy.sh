#!/usr/bin/env bash
# Deploy the HMS stack to Kubernetes.
# Prerequisites: kubectl configured, image built and pushed to a registry,
#                KUBECONFIG pointing at your cluster.
set -euo pipefail

DJANGO_REGISTRY="${DJANGO_REGISTRY:-hms-django}"    # override: DJANGO_REGISTRY=myregistry.io/hms-django
FRONTEND_REGISTRY="${FRONTEND_REGISTRY:-hms-frontend}"  # override: FRONTEND_REGISTRY=myregistry.io/hms-frontend
IMAGE_TAG="${IMAGE_TAG:-latest}"
NAMESPACE="hms"

# ── 1. Build & push images ───────────────────────────────────────────────────
echo ">>> Building Django image ${DJANGO_REGISTRY}:${IMAGE_TAG}"
docker build -t "${DJANGO_REGISTRY}:${IMAGE_TAG}" .

VITE_API_BASE_URL="${VITE_API_BASE_URL:-/api/v1}"
echo ">>> Building Frontend image ${FRONTEND_REGISTRY}:${IMAGE_TAG} (VITE_API_BASE_URL=${VITE_API_BASE_URL})"
docker build --target nginx \
  --build-arg "VITE_API_BASE_URL=${VITE_API_BASE_URL}" \
  -t "${FRONTEND_REGISTRY}:${IMAGE_TAG}" ./frontend

# Uncomment if pushing to a remote registry:
# docker push "${DJANGO_REGISTRY}:${IMAGE_TAG}"
# docker push "${FRONTEND_REGISTRY}:${IMAGE_TAG}"

# ── 2. Populate Prometheus & Alertmanager config from local files ────────────
echo ">>> Creating/updating Prometheus ConfigMap"
kubectl create configmap prometheus-config \
  --from-file=prometheus.yml=monitoring/prometheus.yml \
  --from-file=alerts.yml=monitoring/alerts.yml \
  -n "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

echo ">>> Creating/updating Alertmanager ConfigMap"
kubectl create configmap alertmanager-config \
  --from-file=alertmanager.yml=monitoring/alertmanager.yml \
  -n "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# ── 3. Populate Grafana provisioning from local files ────────────────────────
echo ">>> Creating/updating Grafana provisioning ConfigMaps"
kubectl create configmap grafana-provisioning-datasources \
  --from-file=monitoring/grafana-provisioning/datasources/ \
  -n "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap grafana-provisioning-dashboards \
  --from-file=monitoring/grafana-provisioning/dashboards/ \
  -n "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# ── 4. Apply all manifests ───────────────────────────────────────────────────
echo ">>> Applying manifests"
kubectl apply -k k8s/

# ── 5. Update image tag in deployments ──────────────────────────────────────
for deploy in django celery celery-beat; do
  kubectl set image deployment/"${deploy}" \
    "${deploy}=${DJANGO_REGISTRY}:${IMAGE_TAG}" -n "${NAMESPACE}"
done

kubectl set image deployment/frontend \
  frontend="${FRONTEND_REGISTRY}:${IMAGE_TAG}" -n "${NAMESPACE}"

echo ">>> Waiting for rollout"
for deploy in postgres redis django frontend celery celery-beat prometheus alertmanager grafana; do
  kubectl rollout status deployment/"${deploy}" -n "${NAMESPACE}" --timeout=120s || true
done

echo ">>> HMS deployed to Kubernetes namespace '${NAMESPACE}'"
echo ""
echo "    Frontend:     http://<node-ip>:30080"
echo "    Django API:   http://<node-ip>:30800"
echo "    Prometheus:   http://<node-ip>:30909"
echo "    Alertmanager: http://<node-ip>:30903"
echo "    Grafana:      http://<node-ip>:30301"
