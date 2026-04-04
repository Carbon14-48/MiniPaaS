# Build Service

Pulls source code from GitHub, builds Docker images, and pushes to container registry.

## Endpoints

- `POST /builds` - Trigger a new build
- `GET /builds` - List all builds
- `GET /builds/{id}` - Get build status
- `GET /health` - Health check

## Running locally

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```
