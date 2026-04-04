# App Management Service

Handles application CRUD operations, metadata, and environment variable management.

## Endpoints

- `GET /apps` - List all apps
- `POST /apps` - Create a new app
- `GET /apps/{id}` - Get app details
- `DELETE /apps/{id}` - Delete an app
- `GET /health` - Health check

## Running locally

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```
