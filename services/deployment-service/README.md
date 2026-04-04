# Deployment Service

Deploys containers to Kubernetes, manages scaling, and exposes services via public URLs.

## Endpoints

- `POST /deployments` - Deploy an app
- `GET /deployments` - List all deployments
- `GET /deployments/{id}` - Get deployment details
- `POST /deployments/{id}/scale` - Scale a deployment
- `GET /health` - Health check

## Running locally

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```
