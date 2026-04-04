# API Gateway

Entry point for all Cloudoku client requests. Handles routing, rate limiting, and request validation.

## Endpoints

- `GET /health` - Health check
- `GET /api/apps` - List apps (proxied)
- `POST /api/apps` - Create app (proxied)
- `GET /api/deployments` - List deployments (proxied)
- `GET /api/logs/{app_id}` - Get app logs (proxied)

## Running locally

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```
