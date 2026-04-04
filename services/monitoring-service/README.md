# Monitoring Service

Collects logs from running containers, tracks metrics (CPU, memory, response time), and displays data in dashboard.

## Endpoints

- `GET /logs/{app_id}` - Get app logs
- `GET /logs/{app_id}/stream` - Stream logs (WebSocket)
- `GET /metrics/{app_id}` - Get app metrics
- `GET /metrics` - Get all metrics
- `GET /health` - Health check

## Running locally

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```
