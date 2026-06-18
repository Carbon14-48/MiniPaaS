#!/bin/bash
set -e

echo "=== Setting up k3s for MiniPaaS ==="

# Check Docker
if ! command -v docker &>/dev/null; then
  echo "Docker not found. Install Docker first:"
  echo "  curl -fsSL https://get.docker.com | sh"
  exit 1
fi

# Install k3s
if ! command -v k3s &>/dev/null; then
  echo "Installing k3s..."
  curl -sfL https://get.k3s.io | sh -
  echo "k3s installed. Waiting for node to be ready..."
  sleep 10
else
  echo "k3s already installed."
fi

# Wait for k3s
echo "Waiting for k3s..."
sudo k3s kubectl wait --for=condition=Ready node --all --timeout=60s 2>/dev/null || true

# Set up kubectl config
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
chmod 600 ~/.kube/config

# Create namespace
kubectl create namespace minipaas 2>/dev/null || true

echo ""
echo "=== k3s Ready! ==="
echo "Create GHCR secret before deploying:"
echo "  1. Create a GitHub PAT at https://github.com/settings/tokens"
echo "     (needs 'read:packages' scope)"
echo ""
echo "  2. Run:"
echo "    kubectl create secret docker-registry ghcr-secret \\"
echo "      --docker-server=ghcr.io \\"
echo "      --docker-username=Carbon14-48 \\"
echo "      --docker-password=YOUR_PAT \\"
echo "      -n minipaas"
echo ""
echo "  3. Deploy:"
echo "    ./deploy.sh"
