#!/bin/bash
set -e

echo "Creating minipaas-secret from .env files..."

# Load .env files if they exist
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Also try service-specific .env files
if [ -f services/auth-service/.env ]; then
  set -a
  source services/auth-service/.env
  set +a
fi

# Create the secret
kubectl create secret generic minipaas-secret \
  -n minipaas \
  --dry-run=client -o yaml | \
  kubectl apply -f -

kubectl create secret generic minipaas-secret \
  -n minipaas \
  --from-literal=DATABASE_URL="${DATABASE_URL:-postgresql://minipaas:minipaas@postgres:5432/minipaas}" \
  --from-literal=JWT_SECRET_KEY="${JWT_SECRET_KEY:-change-me-in-production}" \
  --from-literal=JWT_ALGORITHM="${JWT_ALGORITHM:-HS256}" \
  --from-literal=JWT_EXPIRATION_MINUTES="${JWT_EXPIRATION_MINUTES:-60}" \
  --from-literal=REFRESH_TOKEN_SECRET="${REFRESH_TOKEN_SECRET:-change-me-in-production-refresh}" \
  --from-literal=REFRESH_TOKEN_ALGORITHM="${REFRESH_TOKEN_ALGORITHM:-HS256}" \
  --from-literal=REFRESH_TOKEN_EXPIRATION_DAYS="${REFRESH_TOKEN_EXPIRATION_DAYS:-7}" \
  --from-literal=JWT_ACCESS_TOKEN_EXPIRATION_MINUTES="${JWT_ACCESS_TOKEN_EXPIRATION_MINUTES:-15}" \
  --from-literal=GITHUB_CLIENT_ID="${GITHUB_CLIENT_ID:-}" \
  --from-literal=GITHUB_CLIENT_SECRET="${GITHUB_CLIENT_SECRET:-}" \
  --from-literal=GITHUB_REDIRECT_URI="${GITHUB_REDIRECT_URI:-http://localhost:8080/oauth/github/callback}" \
  --from-literal=POSTGRES_USER="${POSTGRES_USER:-minipaas}" \
  --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-minipaas}" \
  --from-literal=POSTGRES_DB="${POSTGRES_DB:-minipaas}" \
  --dry-run=client -o yaml | \
  kubectl apply -f -

echo "Secret updated."
