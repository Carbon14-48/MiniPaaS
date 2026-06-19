#!/bin/bash
set -e

SERVICES="auth-service app-management build-service deployment-service deployer-service monitoring-service registry-service security-scanner api-gateway frontend"
CTR="k3s ctr -a /run/k3s/containerd/containerd.sock -n k8s.io"

echo "=== Pulling images directly into k3s containerd from GHCR ==="
for svc in $SERVICES; do
  img="ghcr.io/carbon14-48/minipaas-${svc}:latest"
  echo "  Pulling $img ..."
  $CTR images pull "$img" 2>&1 | tail -1 || echo "  $img failed, continuing"
done

echo "=== Creating namespace first ==="
kubectl apply -f k8s/namespace.yaml

echo "=== Applying remaining manifests ==="
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pv.yaml 2>/dev/null || true
kubectl apply -f k8s/pvc.yaml 2>/dev/null || true
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/rabbitmq/
kubectl apply -f k8s/auth-service/
kubectl apply -f k8s/app-management/
kubectl apply -f k8s/build-service/
kubectl apply -f k8s/deployment-service/
kubectl apply -f k8s/deployer-service/
kubectl apply -f k8s/monitoring-service/
kubectl apply -f k8s/registry/
kubectl apply -f k8s/registry-service/
kubectl apply -f k8s/security-scanner/
kubectl apply -f k8s/api-gateway/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/ingress.yaml

echo "=== Restarting all deployments ==="
kubectl rollout restart -n minipaas deployment/api-gateway deployment/app-management deployment/auth-service deployment/build-service deployment/deployer-service deployment/deployment-service deployment/frontend deployment/monitoring-service deployment/registry-service deployment/security-scanner

echo "=== Waiting for rollouts ==="
for svc in $SERVICES; do
  echo "  $svc ..."
  kubectl rollout status -n minipaas "deployment/$svc" --timeout=300s 2>&1 | tail -1 || echo "  $svc timed out, continuing"
done

echo "=== Setting up port-forward to localhost:8080 ==="
kill $(lsof -t -i :8080 -sTCP:LISTEN 2>/dev/null) 2>/dev/null || true
setsid kubectl port-forward -n minipaas svc/frontend 8080:8080 &>/dev/null &
echo "  Port-forward running: localhost:8080 -> frontend:8080"

echo "=== Deploy complete ==="
