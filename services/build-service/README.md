# Build Service

Build service for MiniPaaS. It turns source code repositories into container images, runs a security scan, and publishes successful images to the registry.

## Responsibilities

- Validate end-user identity via auth-service (`GET /auth/me` with Bearer token)
- Clone repository and checkout branch
- Detect or generate `Dockerfile`
- Build image with Docker daemon
- Scan built image via security-scanner
- Push safe images via registry-service
- Persist build jobs and statuses

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/build` | Trigger full build pipeline |
| `GET` | `/build/{job_id}` | Get one build status/details (owner only) |
| `GET` | `/build/me` | List current user's build history |
| `GET` | `/build/user/{user_id}` | Legacy endpoint; allowed only for same authenticated user |
| `GET` | `/health` | Health check |

## Auth Contract (Service-to-Service)

This service does **not** decode JWT locally. It delegates token validation to auth-service:

- Request to auth-service:
  - `GET /auth/me`
  - Header: `Authorization: Bearer <access_token>`
- Expected success payload: JSON containing at least `id`

If token is invalid/expired, build-service returns `401`.

## Build Pipeline

1. Validate bearer token via auth-service
2. Create build job row (`running`)
3. Clone repo (`repo_url`, `branch`)
4. Prepare `Dockerfile` (custom or generated)
5. Build image tag `user{user_id}/{app_name}:v{build_number}`
6. Security scan image
7. If critical CVE: mark job `blocked`
8. Else push to registry-service and mark `success`
9. Cleanup temp workspace

## Configuration

Use `.env` (see `.env.example`):

```env
AUTH_SERVICE_URL=http://auth-service:8001
SCANNER_SERVICE_URL=http://security-scanner:8006
REGISTRY_SERVICE_URL=http://registry-service:8005
DATABASE_URL=postgresql://minipaas:minipaas@postgres:5432/minipaas
BUILD_WORKDIR=/tmp/builds
MAX_BUILD_TIMEOUT=300
ENV=development
```

Notes:
- `ENV=development` enables startup `create_all()` convenience.
- In non-development environments, use Alembic migrations and disable implicit table creation.

## Local Run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8003
```

## Security Notes

- `GET /build/{job_id}` and history endpoints are owner-restricted.
- Legacy route `/build/user/{user_id}` is kept for compatibility but enforces same-user access.
- Avoid exposing Docker socket in untrusted environments.
