# Deployment Guide

## Local (Docker Compose)

```bash
docker compose up -d
```

## Kubernetes

```bash
# Development
kubectl apply -k infra/kubernetes/overlays/dev/

# Production
kubectl apply -k infra/kubernetes/overlays/prod/
```

## CI/CD

Pushing to `main` triggers:
1. Build all services
2. Run tests
3. Security scan (Trivy + SonarQube)
4. Deploy to Kubernetes
