#!/bin/bash
set -e

SERVICES="auth-service app-management build-service deployment-service deployer-service monitoring-service registry-service security-scanner api-gateway frontend"

echo "=== Logging in to GHCR ==="
echo "$GHCR_TOKEN" | docker login ghcr.io -u carbon14-48 --password-stdin

echo "=== Pulling latest images from GHCR ==="
for svc in $SERVICES; do
  img="ghcr.io/carbon14-48/minipaas-${svc}:latest"
  echo "  Pulling $img ..."
  docker pull "$img" 2>&1 | tail -1
  echo "  Importing into k3s ..."
  docker save "$img" | k3s ctr -a /run/k3s/containerd/containerd.sock -n k8s.io images import - 2>&1 | tail -1 || echo "  (already in containerd, continuing)"
done

echo "=== Applying manifests ==="
kubectl apply -f k8s/

echo "=== Restarting all deployments ==="
kubectl rollout restart -n minipaas deployment/api-gateway deployment/app-management deployment/auth-service deployment/build-service deployment/deployer-service deployment/deployment-service deployment/frontend deployment/monitoring-service deployment/registry-service deployment/security-scanner

echo "=== Waiting for rollouts ==="
for svc in $SERVICES; do
  echo "  $svc ..."
  kubectl rollout status -n minipaas "deployment/$svc" --timeout=300s 2>&1 | tail -1 || echo "  $svc timed out, continuing"
done

echo "=== Setting up port-forward to localhost:8080 ==="
kill $(lsof -t -i :8080 -sTCP:LISTEN 2>/dev/null) 2>/dev/null || true
nohup kubectl port-forward -n minipaas svc/frontend 8080:8080 &>/dev/null &
disown
echo "  Port-forward running: localhost:8080 -> frontend:8080"

echo "=== Deploy complete ==="
