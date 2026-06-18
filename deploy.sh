#!/bin/bash
set -e

echo "=== Deploying MiniPaaS to k3s ==="

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo "kubectl not found. Run k3s-setup.sh first."; exit 1; }

# Check GHCR secret
if ! kubectl get secret ghcr-secret -n minipaas >/dev/null 2>&1; then
  echo "GHCR secret not found. Create it:"
  echo "  kubectl create secret docker-registry ghcr-secret \\"
  echo "    --docker-server=ghcr.io \\"
  echo "    --docker-username=carbon14-48 \\"
  echo "    --docker-password=YOUR_GITHUB_TOKEN \\"
  echo "    -n minipaas"
  echo ""
  echo "Your GitHub token needs 'read:packages' scope."
  exit 1
fi

# Apply all manifests
echo "Applying manifests..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
./setup-secret.sh
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/registry/
kubectl apply -f k8s/rabbitmq/
kubectl apply -f k8s/auth-service/
kubectl apply -f k8s/app-management/
kubectl apply -f k8s/build-service/
kubectl apply -f k8s/deployment-service/
kubectl apply -f k8s/deployer-service/
kubectl apply -f k8s/monitoring-service/
kubectl apply -f k8s/registry-service/
kubectl apply -f k8s/security-scanner/
kubectl apply -f k8s/api-gateway/
kubectl apply -f k8s/frontend/

# Wait for infrastructure
echo "Waiting for postgres..."
kubectl rollout status -n minipaas statefulset/postgres --timeout=120s
echo "Waiting for registry..."
kubectl rollout status -n minipaas deployment/registry --timeout=60s

# Wait for services
echo "Waiting for services..."
for svc in auth-service app-management build-service deployment-service deployer-service monitoring-service registry-service security-scanner api-gateway frontend; do
  echo "  $svc..."
  kubectl rollout status -n minipaas "deployment/$svc" --timeout=120s || true
done

# Start port-forward
echo ""
echo "=== MiniPaaS ready! ==="
echo "Start port-forwards in another terminal:"
echo "  kubectl port-forward -n minipaas svc/frontend 8080:8080"
echo "  kubectl port-forward -n minipaas svc/api-gateway 8000:8000"
echo ""
echo "Then open http://localhost:8080"
echo ""
echo "To update after new CI build:"
echo "  kubectl rollout restart -n minipaas deployment --all"
