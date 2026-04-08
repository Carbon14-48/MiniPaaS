# MiniPaaS / Cloudoku — Project Summary So Far

> Generated after deep code scan — April 2026

---

## Project Identity

**Name:** MiniPaaS (also referred to as "Cloudoku" in service titles)  
**Type:** Self-hosted Platform-as-a-Service (Heroku-like)  
**Tagline:** "A lightweight Platform-as-a-Service that allows developers to deploy applications by simply pushing their code"  
**DevSecOps Pipeline:** `Push → Build → Test → Security Scan (Trivy + SonarQube) → Deploy to K8s`

---

## Service Inventory

### 8 Backend Microservices (all Python/FastAPI)

| # | Service | Port | DB | External Deps | Maturity |
|---|---|---|---|---|---|
| 1 | `api-gateway` | 8000 | — | Redis, RabbitMQ | :warning: **STUB** |
| 2 | `auth-service` | 8001 | PostgreSQL | — | :white_check_mark: **DONE** |
| 3 | `app-management` | 8002 | PostgreSQL | — | :warning: **PARTIAL** |
| 4 | `build-service` | 8003 | PostgreSQL | Docker socket | :white_check_mark: **DONE** |
| 5 | `deployment-service` | 8004 | — | RabbitMQ | :warning: **STUB** |
| 6 | `monitoring-service` | 8005 | — | RabbitMQ, Prometheus, Loki | :warning: **PARTIAL** |
| 7 | `security-scanner` | 8006 | — | RabbitMQ | :warning: **PARTIAL** |
| 8 | `registry-service` | 8007 | PostgreSQL | Docker socket, registry:5000 | :white_check_mark: **DONE** |

### 4 Infrastructure Services

| Service | Port | Notes |
|---|---|---|
| `postgres` | 5432 | Primary DB (shared by auth, app-mgmt, registry) |
| `rabbitmq` | 5672 / 15672 | Message broker (management UI) |
| `redis` | 6379 | Caching/sessions |
| `registry` | 5000 | Docker Registry V2 (third-party image) |

### Frontend

| Tech | Language | Auth | Routing |
|---|---|---|---|
| React 18 + Vite + Tailwind | TypeScript | JWT (localStorage) | React Router 7 |

### Infra as Code

| Tool | Scope |
|---|---|
| Docker Compose | Local dev (root `docker-compose.yml` + `infra/docker/docker-compose.yml`) |
| Kubernetes (Kustomize) | Prod overlays: `dev/` (2 replicas), `prod/` (3 replicas) |
| Helm | Placeholder (empty dir) |
| GitHub Actions | Per-service CI + deploy pipeline + security scan |

---

## Complete API Route Map

### auth-service (8001) — :white_check_mark: Production-ready

| Method | Path | Handler | Auth |
|---|---|---|---|
| GET | `/` | `root()` | No |
| GET | `/health/` | `health_check()` | No |
| POST | `/auth/register` | `register()` | No |
| POST | `/auth/login` | `login()` | No |
| GET | `/auth/github` | `github_auth()` | No |
| GET | `/auth/callback` | `github_callback()` | No |
| GET | `/auth/me` | `get_me()` | **Bearer JWT** |
| POST | `/auth/refresh` | `refresh_token()` | No |

### build-service (8003) — :white_check_mark: Production-ready

| Method | Path | Handler | Auth |
|---|---|---|---|
| POST | `/build` | `trigger_build()` | **Bearer JWT** |
| GET | `/build/me` | `get_my_builds()` | **Bearer JWT** |
| GET | `/build/{job_id}` | `get_build()` | **Bearer JWT** |
| GET | `/build/user/{user_id}` | `get_user_builds_deprecated()` | **Bearer JWT** |
| GET | `/health` | `health()` | No |

### registry-service (8007) — :white_check_mark: Production-ready

| Method | Path | Handler | Auth |
|---|---|---|---|
| POST | `/push` | `push_image()` | None (internal) |
| GET | `/images/{user_id}` | `get_user_images()` | None (internal) |
| GET | `/images/tag/{image_tag:path}` | `get_image_by_tag()` | None (internal) |
| DELETE | `/images/{image_tag:path}` | `delete_image()` | None (internal) |
| GET | `/health` | `health()` | No |

### app-management (8002) — :warning: Stub routes, DB model exists

| Method | Path | Handler | Status |
|---|---|---|---|
| GET | `/` | `root()` | :white_check_mark: |
| GET | `/health/` | `health_check()` | :white_check_mark: |
| GET | `/apps/` | `list_apps()` | :warning: Returns `[]` |
| POST | `/apps/` | `create_app()` | :warning: Returns mock ID:1 |
| GET | `/apps/{app_id}` | `get_app()` | :warning: Returns mock sample |
| DELETE | `/apps/{app_id}` | `delete_app()` | :warning: Mock message only |

### deployment-service (8004) — :warning: All stubs

| Method | Path | Handler | Status |
|---|---|---|---|
| GET | `/` | `root()` | :white_check_mark: |
| GET | `/health/` | `health_check()` | :white_check_mark: |
| POST | `/deployments/` | `deploy()` | :warning: Returns mock |
| GET | `/deployments/` | `list_deployments()` | :warning: Returns `[]` |
| GET | `/deployments/{id}` | `get_deployment()` | :warning: Returns mock |
| POST | `/deployments/{id}/scale` | `scale_deployment()` | :warning: Returns mock |

### monitoring-service (8005) — :warning: Collectors exist, routes return mock

| Method | Path | Handler | Status |
|---|---|---|---|
| GET | `/` | `root()` | :white_check_mark: |
| GET | `/health/` | `health_check()` | :white_check_mark: |
| GET | `/logs/{app_id}` | `get_logs()` | :warning: Returns mock |
| GET | `/logs/{app_id}/stream` | `stream_logs()` | :warning: WebSocket stub |
| GET | `/metrics/{app_id}` | `get_metrics()` | :warning: Returns mock |
| GET | `/metrics/` | `get_all_metrics()` | :warning: Returns mock |

### security-scanner (8006) — :warning: Trivy/Sonar stubs defined, routes return mock

| Method | Path | Handler | Status |
|---|---|---|---|
| GET | `/` | `root()` | :white_check_mark: |
| GET | `/health/` | `health_check()` | :white_check_mark: |
| POST | `/scans/image` | `scan_image()` | :warning: Returns mock |
| POST | `/scans/code` | `scan_code()` | :warning: Returns mock |
| GET | `/scans/{scan_id}` | `get_scan()` | :warning: Returns mock |

### api-gateway (8000) — :x: Non-functional

| Method | Path | Handler | Status |
|---|---|---|---|
| GET | `/` | `root()` | :white_check_mark: |
| GET | `/health/` | `health_check()` | :white_check_mark: |
| GET | `/api/apps` | `list_apps()` | :x: Stub message |
| POST | `/api/apps` | `create_app()` | :x: Stub message |
| GET | `/api/deployments` | `list_deployments()` | :x: Stub message |
| GET | `/api/logs/{app_id}` | `get_logs()` | :x: Stub message |

---

## Service-to-Service Call Graph

```
Client (Browser)
  └── React Frontend (localhost:5173)
        ├── POST /auth/register   → auth-service:8001
        ├── POST /auth/login     → auth-service:8001
        ├── GET  /auth/github   → auth-service:8001
        ├── GET  /auth/callback  → auth-service:8001
        ├── GET  /auth/me        → auth-service:8001 (Bearer token)
        └── POST /auth/refresh   → auth-service:8001

API Gateway (8000) — receives frontend requests, proxies to backend services
  (Currently: stubs only — no actual HTTP forwarding implemented)
  ├── /api/apps/*         → app-management:8002 (NOT wired)
  ├── /api/deployments/*  → deployment-service:8004 (NOT wired)
  └── /api/logs/*         → monitoring-service:8005 (NOT wired)

build-service:8003 — triggered by external callers (CLI? Direct API?)
  ├── verify_token()      → auth-service:8001 GET /auth/me
  ├── scan_image()        → security-scanner:8006 POST /scans/image
  └── push_image()        → registry-service:8007 POST /push

registry-service:8007
  └── push_to_registry()  → Docker daemon (via /var/run/docker.sock)
                            → registry:5000 (Docker Registry V2 API)

deployment-service:8004
  ├── (intended) list images from registry-service
  └── (intended) create k8s resources — NOT IMPLEMENTED

monitoring-service:8005
  ├── fetch_metrics()      → Prometheus (configured, NOT verified in infra)
  └── fetch_logs()        → Loki (configured, NOT verified in infra)

security-scanner:8006
  ├── scan_container_image() → runs `trivy image` CLI (NOT integrated in routes)
  └── run_code_analysis()  → SonarQube HTTP API (NOT integrated in routes)
```

**External services required by monitoring and security-scanner but NOT in root docker-compose:**
- Prometheus (`prometheus:9090`)
- Loki (`loki:3100`)
- SonarQube (`sonarqube:9000`)
- These ARE defined in `infra/docker/docker-compose.yml` but NOT in root `docker-compose.yml`

---

## Database Schema

### auth-service → `postgres` (db: `minipaas`)

**Table: `users`**

| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| email | String(255) | UNIQUE, NOT NULL |
| name | String(255) | NOT NULL |
| hashed_password | String(255) | NULLABLE (OAuth users) |
| is_active | Boolean | default True |
| is_verified | Boolean | default False |
| oauth_provider | String(50) | NULLABLE |
| oauth_id | String(255) | NULLABLE |
| created_at | DateTime | default utcnow |
| updated_at | DateTime | auto onupdate |

### app-management → `postgres` (db: `cloudoku`) — Model exists, not wired

**Table: `apps`**

| Column | Type | Constraints |
|---|---|---|
| id | Integer | PK |
| name | String | UNIQUE, NOT NULL |
| repo_url | String | NOT NULL |
| branch | String | default "main" |
| env_vars | JSON | default {} |
| status | String | default "created" |
| public_url | String | NULLABLE |
| created_at | DateTime | default utcnow |
| updated_at | DateTime | auto onupdate |

### registry-service → `postgres` (db: `registrydb`) — Separate DB!

**Table: `registry_images`**

| Column | Type | Constraints |
|---|---|---|
| image_id | String(UUID) | PK |
| user_id | Integer | NOT NULL, indexed |
| app_name | String | NOT NULL |
| image_tag | String | UNIQUE, NOT NULL |
| registry_url | String | NOT NULL |
| digest | String | NULLABLE |
| size_bytes | BigInteger | NULLABLE |
| pushed_at | DateTime | NOT NULL |
| is_active | Boolean | default True (soft delete) |

### build-service → `postgres` (db: `minipaas`) — Separate DB!

**Table: `build_jobs`**

| Column | Type | Constraints |
|---|---|---|
| job_id | String(UUID) | PK |
| user_id | Integer | NOT NULL, indexed |
| repo_url | String | NOT NULL |
| app_name | String | NOT NULL |
| branch | String | default "main" |
| status | Enum(pending/running/success/failed/blocked) | NOT NULL |
| image_tag | String | NULLABLE |
| image_url | String | NULLABLE |
| build_logs | Text | NULLABLE |
| scan_result | JSON | NULLABLE |
| created_at | DateTime | NOT NULL |
| finished_at | DateTime | NULLABLE |

### Critical: Database fragmentation — 4 separate DBs across services!

| Service | DB Name | Host | User |
|---|---|---|---|
| auth-service | `minipaas` | postgres (shared container) | `minipaas` |
| build-service | `minipaas` | postgres (shared container) | `minipaas` |
| app-management | `cloudoku` | postgres (shared container) | `cloudoku` |
| registry-service | `registrydb` | `registry-db` (different host!) | `registryuser` |

---

## Key Service Logic Breakdown

### build-service — Build Pipeline (the core of the platform)
1. Receives `POST /build` with `repo_url`, `branch`, `app_name`
2. Validates JWT via auth-service call
3. Clones repo via `gitpython` (shallow clone, depth=1)
4. Detects language: checks for Dockerfile → requirements.txt → package.json → pom.xml
5. Auto-generates Dockerfile for Python/Node/Java if none exists
6. Builds image via Docker SDK (`docker build`)
7. Tags as `user{user_id}/{app_name}:v{n}`
8. Sends to security-scanner → blocks on CRITICAL CVE
9. Pushes to registry-service → gets back `registry_url` + digest
10. Records job in PostgreSQL
11. Cleans up temp `/tmp/builds/{job_id}/`

### registry-service — Image Management
1. Receives `POST /push` with `image_tag`, `user_id`, `app_name`
2. Tags image with `registry:5000/{image_tag}`
3. Pushes via Docker SDK to `registry:5000`
4. Extracts digest from push stream
5. Records in `registry_images` table
6. Cleans up local Docker daemon images (frees disk)
7. Idempotent: re-push returns `already_exists` without re-uploading
8. Soft-delete only (`is_active=False`)

### auth-service — User Identity
1. Email/password registration with bcrypt hashing
2. Password strength: 8+ chars, upper, lower, digit
3. GitHub OAuth: authorization URL → code exchange → user+email fetch
4. JWT: access token (15min, HS256) + refresh token (7 days, HS256)
5. OAuth users can optionally link a password
6. Token refresh with rotation

### api-gateway — :x: Critical Issues
1. Auth middleware `verify_token()` is **defined but never registered** in `main.py`
2. Proxy routes return placeholder strings — **no actual HTTP forwarding**
3. References `JWT_SECRET_KEY` and `JWT_ALGORITHM` but these are **not in Settings**
4. Rate limiting config exists but **not implemented**
5. `httpx` in requirements but **never imported**
6. Only `/health` and `/` work; all `/api/*` routes are dead

### deployment-service — :x: Critical Issues
1. k8s client functions in `src/k8s/client.py` are **defined but never called**
2. `load_kube_config()` is **never invoked**
3. All 4 deployment routes return **hardcoded mock data**
4. No YAML generation, no actual k8s API calls
5. `pika` (RabbitMQ) in requirements but **never imported**
6. `CLOUDOKU_DOMAIN` config defined but **never used**

### monitoring-service — Collectors exist, routes don't use them
1. `fetch_metrics()` calls Prometheus API — **not called by any route**
2. `fetch_logs()` calls Loki API — **not called by any route**
3. Routes return **hardcoded mock data**
4. WebSocket stream endpoint is a **stub**
5. `pika` in requirements but **never imported**
6. Prometheus/Loki not in root docker-compose (only in `infra/docker/`)

### security-scanner — Scanners defined, routes don't use them
1. `scan_container_image()` runs `trivy image --format json` CLI — **not called by routes**
2. `run_code_analysis()` calls SonarQube API — **not called by routes**
3. Routes return **hardcoded empty vulnerability lists**
4. Dockerfile installs `curl` but **no Trivy binary**
5. `pika` in requirements but **never imported**
6. SonarQube not in root docker-compose (only in `infra/docker/`)

### shared/cloudoku_common — Exists but unused
- `BaseAppSettings`, `create_access_token`, `decode_access_token`, `setup_logger`
- **Zero services import from it** — every service has duplicated/bespoke implementations
- Different database URLs, JWT secrets, and config structures across services

---

## Critical Architectural Issues

### 1. API Gateway is Non-Functional
- Auth middleware not registered
- No proxy forwarding to backend services
- Frontend talks directly to auth-service:8001 (bypassing gateway entirely)

### 2. Deployment Service is a Shell
- Zero Kubernetes API interaction
- All routes return mock data
- Cannot actually deploy anything

### 3. No Unified Build Trigger Flow
- No documented path from frontend → build-service
- Frontend has no "Deploy" or "Build" UI
- No CLI tool exists
- Build endpoint requires direct HTTP call with JWT

### 4. Database Fragmentation
- 4 separate PostgreSQL databases across 4 services
- `registry-service` references `registry-db` hostname not present in docker-compose
- No shared DB for cross-service queries

### 5. Infrastructure Gaps
- Prometheus, Loki, SonarQube in `infra/docker/` but NOT in root `docker-compose.yml`
- `pika` (RabbitMQ client) in 5 services but **zero services use it**
- `shared/cloudoku_common` completely unused

### 6. Security Gaps
- Hardcoded secrets in `.env` and K8s secrets
- CORS allows `*` everywhere
- No auth on internal service-to-service calls (registry-service, deployment-service)
- JWT secret in `cloudoku-secrets.yaml` is `"change-me-in-production"`

### 7. Frontend Limitations
- Dashboard only shows user info and tokens
- No app listing, build triggering, deployment management
- GitHub OAuth callback stores code but never exchanges it for tokens properly
- No connection to build-service, deployment-service, or monitoring-service

### 8. Build Pipeline Incomplete
- build-service checks for critical CVEs but **always returns clean** (scanner is stub)
- No webhook from GitHub for auto-builds
- No build logs streaming back to frontend
- No build cancellation

### 9. CI/CD Incomplete
- GitHub Actions deploy only the `api-gateway` to K8s (per `deploy.yml`)
- No other services in the deploy pipeline
- K8s manifests only cover api-gateway, not the other 7 services

---

## Dependency Overview

| Library | Services Using | Usage |
|---|---|---|
| FastAPI | ALL 8 | Web framework |
| SQLAlchemy | auth, app-mgmt, registry, build | ORM |
| PostgreSQL driver | auth, app-mgmt, registry, build | psycopg2-binary |
| Alembic | auth, app-mgmt, registry, build | Migrations |
| Pydantic | ALL 8 | Data validation |
| Docker SDK | build, registry | docker.from_env() |
| gitpython | build | Git clone |
| bcrypt | auth | Password hashing |
| PyJWT | auth, gateway | JWT tokens |
| pika | 5 services | RabbitMQ (unused) |
| kubernetes | deployment | K8s client (unused) |
| httpx | auth, build, registry, gateway | HTTP client |
| requests | monitoring, security-scanner | HTTP client |
| Trivy CLI | security-scanner | Security scanning (not installed) |
| SonarQube | security-scanner | Code analysis (not integrated) |

---

## What Works End-to-End

1. **User registration + login** → auth-service
2. **GitHub OAuth** → auth-service (flow complete, callback partial)
3. **JWT token generation + refresh** → auth-service
4. **Build pipeline logic** (clone → Dockerfile → build → scan → push) → build-service
5. **Docker image push to local registry** → registry-service
6. **Image listing/deletion** → registry-service
7. **Soft-delete image management** → registry-service
8. **React frontend** with auth flow, protected routes, localStorage tokens

---

## What Is Missing / Stubbed

1. **API Gateway proxying** — everything returns stub messages
2. **Deployment to Kubernetes** — routes return mock, no k8s API calls
3. **Monitoring data collection** — collectors exist but routes don't call them
4. **Security scanning** — Trivy/Sonar defined but routes return empty lists
5. **App management CRUD** — model exists but routes return mock data
6. **RabbitMQ** — configured everywhere, used nowhere
7. **Frontend dashboard** — only shows auth tokens, no app/build/deploy UI
8. **CLI tool** — no command-line interface for triggering builds
9. **Build log streaming** — logs captured but not streamed to client
10. **Automatic rollback** — no deployment rollback on failure
11. **Ingress management** — no k8s Ingress for public URLs
12. **Shared library adoption** — `cloudoku_common` exists but nobody uses it
13. **Prometheus/Loki/SonarQube** — in infra but not in main compose

---

## Ready-Made Plug Points for New Service

If you're adding a new service, the existing patterns give you:

- **Pattern to follow:** Any of the existing services (build-service is most complete)
- **Config:** Inherit from `pydantic_settings.BaseSettings`, read `.env`
- **DB:** SQLAlchemy + Alembic, connect to shared `postgres` container
- **HTTP client:** `httpx` for async, `requests` for sync
- **Dockerfile:** Multi-stage build from `python:3.12-slim`, expose 8000, run uvicorn
- **Tests:** pytest with `TestClient`, SQLite in-memory override
- **CI:** Already have per-service workflow templates in `.github/workflows/`
- **Env vars:** Add to `.env.example` at root
- **Health:** Always add `GET /health/` endpoint
- **Docker Compose:** Add to root `docker-compose.yml` with `env_file: .env`

---

## Directory Tree

```
MiniPaaS/
├── .env / .env.example
├── docker-compose.yml              # Full local environment (root)
├── Makefile                        # dev, test, lint, build, clean
├── README.md
├── summarysofar.md                 # This file
│
├── frontend/                       # React + Vite + TypeScript + Tailwind
│   ├── src/
│   │   ├── App.tsx                # Routing + AuthProvider
│   │   ├── lib/api.ts              # Axios API client
│   │   ├── context/AuthContext.tsx # Auth state management
│   │   ├── pages/                  # Home, Login, Register, Dashboard, GitHubCallback
│   │   └── components/             # WebGL lightning effect, auth background
│   └── vite.config.ts              # Proxy /auth → localhost:8001
│
├── services/                       # 8 Python/FastAPI microservices
│   ├── api-gateway/                # Port 8000 — Stub proxy routes
│   ├── auth-service/               # Port 8001 — JWT, GitHub OAuth, User CRUD
│   ├── app-management/             # Port 8002 — App CRUD (stub)
│   ├── build-service/              # Port 8003 — Git→Docker→Registry pipeline
│   ├── deployment-service/         # Port 8004 — K8s deployment (stub)
│   ├── monitoring-service/         # Port 8005 — Prometheus/Loki collection (stub)
│   ├── security-scanner/           # Port 8006 — Trivy/SonarQube (stub)
│   └── registry-service/           # Port 8007 — Docker registry management
│
├── shared/                         # cloudoku_common (unused by any service)
│   └── python/
│       └── cloudoku_common/        # BaseAppSettings, JWT helpers, logging
│
├── infra/                          # IaC — Docker, K8s, Helm
│   ├── docker/                     # Local dev infrastructure stack
│   │   └── docker-compose.yml     # Postgres, RabbitMQ, Redis, Prometheus, Grafana, SonarQube
│   ├── kubernetes/                 # K8s manifests
│   │   ├── base/                  # Namespace, ConfigMap, Secrets, Deployment, Service
│   │   └── overlays/              # dev/ + prod/ via Kustomize
│   └── helm/                       # Helm chart (placeholder)
│
├── scripts/                        # Automation scripts
│   ├── setup.sh                   # pip install per service
│   ├── dev.sh                      # docker compose up -d
│   ├── test-all.sh                 # pytest per service
│   └── lint-all.sh                 # ruff check per service
│
├── docs/                           # Documentation
└── .github/
    └── workflows/                  # CI per service + deploy.yml + security-scan.yml
```

---

*Last updated: April 2026 — after deep code scan in preparation for new service addition*
