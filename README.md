# MiniPaaS — DevSecOps Platform for Microservices

A lightweight Platform-as-a-Service (PaaS) that deploys applications from GitHub
repositories onto Docker or K3s, built as a demonstration of DevSecOps principles
applied to a microservice architecture.

This document serves as both the platform reference and the foundation for the
report "DevSecOps for Microservices". Part 1 describes the MiniPaaS platform
itself — its architecture, services, and business logic. Part 2 describes the
DevSecOps lifecycle that builds, tests, scans, deploys, and monitors MiniPaaS
as a software project.

---

## Table of Contents

### Part 1 — MiniPaaS Platform (Business Logic)

1.  What is MiniPaaS?
2.  Architecture Overview
3.  Service Topology & Communication
4.  Service Deep Dives
    4.1  API Gateway
    4.2  Auth Service
    4.3  App Management
    4.4  Build Service
    4.5  Deployer Service
    4.6  Deployment Service
    4.7  Monitoring Service
    4.8  Registry Service
    4.9  Security Scanner
5.  Database Schema
6.  Authentication & Authorization
7.  End-to-End Deployment Flow
8.  Frontend Architecture
9.  Security Scanner Internals
10. Monitoring & Observability

### Part 2 — DevSecOps Lifecycle of MiniPaaS

11. Development Workflow
12. CI/CD Pipeline Overview
13. Secret Scanning (Gitleaks)
14. Code Quality & Static Analysis
15. Testing Strategy
16. Dockerfile Security & Linting
17. Container Vulnerability Management
18. Image Registry & Artifact Management
19. Kubernetes Deployment (K3s)
20. Production Monitoring Stack
21. Security Architecture (Defense in Depth)
22. Risk Acceptance & Vulnerability Management
23. Complete GitOps Flow

---

# Part 1 — MiniPaaS Platform (Business Logic)

---

## 1. What is MiniPaaS?

MiniPaaS is a lightweight Platform-as-a-Service that allows users to deploy
applications directly from GitHub repositories. It is built as a demonstration
of DevSecOps practices applied to a real microservice architecture.

**Core capabilities:**

- Deploy any GitHub repository as a running Docker container with one click
- Automatic language detection and Dockerfile generation (Python, Node.js, Java)
- Multi-layer security scanning before any image is deployed
- Real-time container monitoring (CPU, memory, network, logs)
- GitHub OAuth integration for repository access
- JWT-based authentication with access and refresh tokens
- Runs on Docker Compose (development) or K3s Kubernetes (production)

**Technology stack:**

| Layer          | Technology                                     |
|----------------|------------------------------------------------|
| Backend        | Python 3.11/3.12, FastAPI, Pydantic            |
| Frontend       | React 18, TypeScript, Vite, Tailwind CSS       |
| Database       | PostgreSQL 16 (Alpine)                         |
| Message Queue  | None (RabbitMQ was removed as unused)          |
| Cache          | None (Redis was removed as unused)             |
| Container      | Docker, Docker Compose, K3s (Kubernetes)       |
| Monitoring     | Prometheus, Grafana, kube-state-metrics        |
| CI/CD          | GitHub Actions, SonarCloud, Trivy, Dockle      |
| Registry       | GitHub Container Registry (GHCR)               |
| Secrets        | GitHub Secrets, Kubernetes Secrets             |

---

## 2. Architecture Overview

MiniPaaS follows a microservice architecture with 9 backend services, a React
frontend, shared PostgreSQL, and a Docker registry. Every service is stateless
(except PostgreSQL and the Docker registry, which have persistent volumes).

```
                    ┌─────────────┐
                    │   Browser   │
                    └──────┬──────┘
                           │ HTTP :5173 / :30080
                           ▼
                    ┌─────────────┐
                    │   Frontend   │  (Nginx SPA + React)
                    │  :8080       │
                    └──────┬──────┘
                           │ /auth/* /deployments/* /repos/* /monitoring/*
                           ▼
                    ┌─────────────┐
                    │ API Gateway  │  (Proxy + JWT middleware)
                    │  :8000       │
                    └──┬──┬──┬──┬─┘
                       │  │  │  │
          ┌────────────┘  │  │  └──────────────┐
          ▼               ▼  ▼                  ▼
   ┌──────────┐   ┌──────────┐   ┌─────────────────┐
   │   Auth   │   │  Build   │   │    Deployer      │
   │ :8001    │   │ :8003    │   │  :8008           │
   └────┬─────┘   └──┬──┬───┘   └──┬──┬──┬──┬──┬───┘
        │            │  │          │  │  │  │  │
        │            │  └────┐     │  │  │  │  │
        │            ▼       ▼     │  │  │  │  │
        │     ┌────────┐ ┌──────┐  │  │  │  │  │
        │     │Scanner │ │Registry│ │  │  │  │  │
        │     │:8006   │ │Service │  │  │  │  │  │
        │     └────────┘ │:8007  │  │  │  │  │  │
        │                └───────┘  │  │  │  │  │
        │                           │  │  │  │  │
        ▼                           ▼  ▼  ▼  ▼  ▼
   ┌──────────┐              ┌──────────────────────┐
   │ App Mgmt │              │   Monitoring Service │
   │ :8002    │              │   :8005              │
   └──────────┘              └──┬───────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
             ┌──────────┐           ┌───────────────┐
             │PostgreSQL│           │   Prometheus   │
             │ :5432    │           │   :9090        │
             └──────────┘           └───────┬───────┘
                                            │
                                     ┌──────┴──────┐
                                     │   Grafana    │
                                     │   :30300     │
                                     └─────────────┘
```

**Key architectural decisions:**

- **API Gateway as single entry point**: All external requests go through the
  API Gateway, which handles JWT verification and proxies to backend services.
- **Docker socket sharing**: 5 services mount the Docker socket for direct
  daemon access (build, deploy, monitor, scan, registry operations).
- **No message broker**: RabbitMQ was initially included but never used by any
  service — all inter-service communication is synchronous HTTP.
- **Independent token verification**: Every service independently verifies JWTs
  by calling the Auth Service, not trusting the API Gateway's middleware.

---

## 3. Service Topology & Communication

### Port Mapping

| Service             | Internal Port | Docker Host Port | K8s Service Port | Type         |
|---------------------|---------------|------------------|------------------|--------------|
| Frontend            | 8080          | 5173             | 8080 (NP 30080)  | NodePort     |
| API Gateway         | 8000          | 8000             | 8000             | ClusterIP    |
| Auth Service        | 8000          | 8001             | 8000             | ClusterIP    |
| App Management      | 8000          | 8002             | 8000             | ClusterIP    |
| Build Service       | 8002          | 8003             | 8002             | ClusterIP    |
| Deployment Service  | 8000          | 8004             | 8000             | ClusterIP    |
| Deployer Service    | 8000          | 8008             | 8000             | ClusterIP    |
| Registry Service    | 8005          | 8007             | 8005             | ClusterIP    |
| Monitoring Service  | 8006          | 8005             | 8006             | ClusterIP    |
| Security Scanner    | 8000          | 8006             | 8000             | ClusterIP    |
| PostgreSQL          | 5432          | 5432             | 5432             | ClusterIP    |
| Docker Registry     | 5000          | 5000             | 5000             | ClusterIP    |
| Prometheus          | 9090          | —                | 9090             | ClusterIP    |
| Grafana             | 3000          | —                | 3000 (NP 30300)  | NodePort     |

NP = NodePort. Services without a host port are only accessible inside K8s.

### Inter-Service Dependencies

```
auth-service
  └─ depends on: postgres
  └─ called by: ALL services (token verification)

build-service
  └─ depends on: postgres, auth-service
  └─ called by: deployer-service (trigger build)
  └─ calls: auth-service (verify token), security-scanner (scan image),
            registry-service (push image)

deployer-service
  └─ depends on: postgres, auth-service, build-service, registry-service
  └─ called by: api-gateway (all deployment/repo operations)
  └─ calls: auth-service (verify token, get GitHub token), build-service
            (trigger build), registry-service (image lookup),
            monitoring-service (cleanup on delete)

monitoring-service
  └─ depends on: postgres
  └─ called by: api-gateway, Grafana (via Prometheus scraping)
  └─ calls: auth-service (verify token)

security-scanner
  └─ depends on: Docker daemon (Trivy, ClamAV, YARA, TruffleHog, Dockle)
  └─ called by: build-service (scan image after build)

registry-service
  └─ depends on: postgres, registry:2
  └─ called by: build-service (push after scan), deployer-service (image lookup)

app-management
  └─ depends on: postgres
  └─ called by: api-gateway

deployment-service
  └─ (standalone stub, only health endpoint)
```

---

## 4. Service Deep Dives

### 4.1 API Gateway

**Purpose**: Single entry point for all external requests. Handles JWT
verification, CORS, and reverse-proxies to backend services.

**Port**: 8000 (internal), 8000 (host)

**Configuration** (`src/config.py`):

```python
AUTH_SERVICE_URL = "http://auth-service:8000"
APP_MANAGEMENT_SERVICE_URL = "http://app-management:8000"
BUILD_SERVICE_URL = "http://build-service:8002"
DEPLOYMENT_SERVICE_URL = "http://deployment-service:8000"
DEPLOYER_SERVICE_URL = "http://deployer-service:8000"
MONITORING_SERVICE_URL = "http://monitoring-service:8006"
SECURITY_SCANNER_URL = "http://security-scanner:8000"
REGISTRY_SERVICE_URL = "http://registry-service:8005"
```

**Endpoints**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | Root health |
| GET | `/health` | No | Health check |
| ANY | `/{service}/{path:path}` | Yes* | Reverse proxy to backend |

\* Public paths: `/`, `/health`, `/health/`, `/docs`, `/openapi.json`,
`/auth/register`, `/auth/login`, `/auth/github`, `/auth/callback`

**Business logic**:

- Maintains a `SERVICE_URLS` dictionary mapping URL prefix to backend URL.
- Uses `httpx.AsyncClient` for proxying — builds and deployments get a 600s
  timeout, all others 30s.
- JWT middleware (`src/middleware/auth.py`) intercepts every request and
  verifies the `Authorization: Bearer <token>` header by decoding the JWT
  locally using PyJWT. Public paths bypass this check.
- CORS is wide open (`ALLOWED_ORIGINS: list[str] = ["*"]`) for development.

**Key design note**: The API Gateway decodes JWTs locally rather than calling
the Auth Service. This differs from all other services, which call
`auth-service:8000/auth/me` for verification.

---

### 4.2 Auth Service

**Purpose**: User authentication, JWT token management, GitHub OAuth
integration.

**Port**: 8001 (host), 8000 (internal)

**Database**: `users` table in PostgreSQL

**Endpoints**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Register with email + password |
| POST | `/auth/login` | No | Login, returns JWT pair |
| GET | `/auth/github` | No | Get GitHub OAuth authorization URL |
| GET | `/auth/callback?code=` | No | GitHub OAuth callback |
| GET | `/auth/me` | Bearer | Get current user profile |
| GET | `/auth/github-token` | Bearer | Get user's stored GitHub access token |
| POST | `/auth/refresh` | No | Refresh access token using refresh token |

**Registration flow**:

1. Validates password strength: minimum 8 characters, at least one uppercase
   letter, one lowercase letter, one digit.
2. Hashes password with bcrypt.
3. Creates user record in PostgreSQL.
4. Returns JWT access token (15-minute expiry) + refresh token (7-day expiry).

**Login flow**:

1. Looks up user by email.
2. Verifies password with bcrypt.
3. Returns JWT access + refresh tokens.

**GitHub OAuth flow**:

1. `GET /auth/github` returns a GitHub authorization URL with scopes
   `repo,user:email,read:user`.
2. User authorizes on GitHub and is redirected to `/auth/callback?code=...`.
3. Auth Service exchanges the code for a GitHub access token.
4. Creates or links the GitHub account to a local user record.
5. Stores the GitHub access token in the database for later use by the
   Deployer Service (to clone private repos and list repositories).
6. Returns JWT access + refresh tokens.

**Token verification**:

- All other services call `GET /auth/me` with the Bearer token to verify.
- The Auth Service decodes the JWT locally and returns the user profile.
- This creates a synchronous dependency: every service-to-service call that
  needs auth goes through the Auth Service.

---

### 4.3 App Management

**Purpose**: Application lifecycle management (CRUD for user applications).

**Port**: 8002 (host), 8000 (internal)

**Status**: STUB SERVICE — route handlers return static/mock data. The database
model for `apps` is defined but the full CRUD implementation is not wired up
to production routes.

**Endpoints**:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/apps/` | List all apps (returns empty list) |
| POST | `/apps/` | Create a new app (mock response) |
| GET | `/apps/{app_id}` | Get app by ID (mock response) |
| DELETE | `/apps/{app_id}` | Delete an app (mock response) |

**Database model**: `apps` table with columns `id`, `name`, `repo_url`,
`branch`, `env_vars`, `status`, `public_url`.

The service layer has `generate_public_url(app_name)` returning
`https://{app_name}.cloudoku.app` as the URL pattern.

---

### 4.4 Build Service

**Purpose**: The core build pipeline — clones repositories, builds Docker
images, triggers security scanning, and pushes approved images to the
registry.

**Port**: 8003 (host), 8002 (internal)

**Dependencies**: PostgreSQL, Auth Service, Security Scanner, Registry Service

**Database**: `build_jobs` table

**Endpoints**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/build` | Bearer | Trigger full build pipeline |
| GET | `/build/me` | Bearer | List user's build history |
| GET | `/build/{job_id}` | Bearer | Get build status and details |

**Full build pipeline** (`POST /build`):

```
1. Extract JWT from Authorization header
2. Verify token via auth-service:8000/auth/me
3. Create BuildJob record (status: "running")
4. Clone repository to /tmp/builds/<job_id>/
   ├─ Uses stored GitHub token for private repos
   └─ Retry logic on clone failure
5. Detect language and generate Dockerfile if needed
   ├─ Checks for existing Dockerfile in repo root
   ├─ If absent, detects Python (requirements.txt), Node.js (package.json),
   │  Java (pom.xml), or Go (go.mod)
   └─ Writes an appropriate Dockerfile
6. Build Docker image via Docker SDK
   ├─ Tag format: user{user_id}/{app_name}:v{build_number}
   └─ Streams build logs
7. Scan image via security-scanner:8006/scans/image
   ├─ Waits for scan result (all 5 scanners run in parallel)
   └─ Parses verdict: PASS, WARN, or BLOCKED
8. If BLOCKED: mark build_job as "blocked", return scan result
9. If PASSED: push image via registry-service:8005/push
   ├─ docker tag + docker push to registry:5000
   └─ Save image metadata in registry DB
10. Save build result in build_jobs table
11. Cleanup: remove cloned repo directory
```

**Internal services**:

- `auth_client.py` — HTTP client for `auth-service:8000/auth/me`
- `git_service.py` — Repository cloning with retry and cleanup
- `docker_service.py` — Language detection, Dockerfile generation, image building
- `scanner_client.py` — HTTP client for security-scanner scan API
- `registry_client.py` — HTTP client for registry-service push API

**Language detection logic** (`docker_service.py`):

| File found | Language | Generated base image |
|-----------|----------|---------------------|
| `requirements.txt` | Python | `python:3.11-slim` |
| `package.json` | Node.js | `node:20-alpine` |
| `pom.xml` | Java | `eclipse-temurin:17-jdk` |
| `go.mod` | Go | `golang:1.21-alpine` |
| None | Unknown | Returns error, requires manual Dockerfile |

---

### 4.5 Deployer Service

**Purpose**: Orchestrates the full deployment lifecycle — creates deployments,
manages Docker containers, and proxies GitHub API for repository listing.

**Port**: 8008 (host), 8000 (internal)

**Dependencies**: PostgreSQL, Auth Service, Build Service, Registry Service,
Docker daemon

**Database**: `deployments` table

**Endpoints**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/deployments/` | Bearer | Create new deployment (build + run) |
| GET | `/deployments/` | Bearer | List user's active deployments |
| GET | `/deployments/{id}` | Bearer | Get deployment details |
| DELETE | `/deployments/{id}` | Bearer | Stop + delete deployment |
| POST | `/deployments/{id}/stop` | Bearer | Stop a running deployment |
| POST | `/deployments/{id}/start` | Bearer | Start a stopped deployment |
| POST | `/deployments/{id}/restart` | Bearer | Restart a deployment |
| GET | `/deployments/{id}/logs` | Bearer | Get deployment logs |
| GET | `/repos/` | Bearer | List user's GitHub repositories |
| GET | `/repos/{owner}/{repo}/branches` | Bearer | List branches for a repo |

**Deployment flow** (`POST /deployments/`):

```
1. Verify JWT via auth-service:8000/auth/me
2. Create Deployment record (status: "building")
3. Fetch GitHub access token from auth-service:8000/auth/github-token
4. Call build-service:8003/build to trigger the build pipeline
5. Check build result:
   ├─ If "blocked" or "failed": update deployment, return error
   └─ If "success": proceed to run container
6. Run Docker container via DockerRunner:
   ├─ Container name: minipaas-{userId}-{appName}
   ├─ Port allocation: dynamic from range 30000-40000
   ├─ Labels: { minipaas: "true", user_id: ..., app_name: ... }
   ├─ Image detection: try local first → registry:5000
   └─ Healthcheck: process-based
7. Update deployment status to "running"
8. Return deployment with public URL and port
```

**Container management** (`docker_runner.py`):

- `run_container()` — Creates and starts container with port mapping, labels,
  restart policy, resource limits.
- `stop_container()` — Stops container gracefully (30s timeout), then kills.
- `remove_container()` — Force-removes container.
- `get_container_status()` — Returns running/stopped/failed status.
- `get_container_logs()` — Streams last N log lines.
- `port_allocation()` — Scans for free port in 30000-40000 range.

**GitHub integration** (`github_client.py`):

- Lists repositories for the authenticated user via GitHub API v3.
- Lists branches for a given repository.
- Uses the user's stored GitHub access token (fetched from Auth Service).

---

### 4.6 Deployment Service

**Purpose**: Intended to manage Kubernetes deployments for user applications.
Currently a stub/minimal service.

**Port**: 8004 (host), 8000 (internal)

**Status**: STUB SERVICE. Only has a health endpoint. The original design
intended this service to create Kubernetes Deployments and Services for user
apps, but that functionality was never implemented. The Deployer Service
handles container deployment via Docker instead.

**Endpoints**:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root health |
| GET | `/health/` | Health check |

---

### 4.7 Monitoring Service

**Purpose**: Passively collects container metrics (CPU, memory, network) and
logs from Docker containers, stores them in PostgreSQL, and exposes them via
REST API and Prometheus endpoint.

**Port**: 8005 (host), 8006 (internal)

**Dependencies**: PostgreSQL, Docker daemon (read-only)

**Database**: `container_metrics` and `log_entries` tables

**Endpoints**:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/metrics/user/{user_id}` | Bearer | All metrics for user's apps |
| GET | `/metrics/summary` | Bearer | Latest metric per app |
| GET | `/metrics/{app_id}` | Bearer | Metrics for a specific app |
| GET | `/metrics` | No | Prometheus exposition format |
| GET | `/logs/user/{user_id}` | Bearer | Logs for all user apps |
| GET | `/logs/{app_id}` | Bearer | Logs for a specific app (from DB) |
| GET | `/logs/{app_id}/live` | Bearer | Live logs directly from Docker |
| POST | `/logs/{app_id}/collect` | Bearer | Force immediate log collection |
| GET | `/health` | No | DB + Docker health |
| GET | `/health/{app_id}` | Bearer | Health for specific app |
| GET | `/health/containers/all` | Bearer | All monitored containers status |

**Background scheduler** (APScheduler, runs every 30 seconds):

1. **collect_metrics_job**: Iterates all Docker containers with label
   `minipaas=true` or name matching `minipaas_*` / `minipaas-*`. Collects
   CPU percentage, memory usage/limit/percentage, network RX/TX bytes.
   Stores in `container_metrics` table.

2. **collect_logs_job**: For each monitored container, collects the last 20
   log lines. Stores in `log_entries` table with detected log level
   (INFO/WARN/ERROR/DEBUG).

3. **cleanup_old_metrics_job**: Runs every hour. Deletes metrics and logs
   older than the retention period (default 7 days).

**Prometheus endpoint** (`GET /metrics`):

Exposes 6 metric families usable by Prometheus scraping:

```
minipaas_container_cpu_percent{app_id="...", user_id="...", container="..."}
minipaas_container_memory_usage_bytes{...}
minipaas_container_memory_percent{...}
minipaas_container_network_rx_bytes{...}
minipaas_container_network_tx_bytes{...}
```

---

### 4.8 Registry Service

**Purpose**: Manages Docker images in the local registry — push after build,
list, and delete operations.

**Port**: 8007 (host), 8005 (internal)

**Dependencies**: PostgreSQL, Docker daemon, Docker Registry (registry:2)

**Database**: `registry_images` table

**Endpoints**:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/push` | Push image to local registry (called by build-service) |
| GET | `/images/{user_id}` | List all active images for a user |
| GET | `/images/tag/{image_tag:path}` | Get image details by tag |
| DELETE | `/images/{image_tag:path}` | Soft-delete an image |

**Push flow** (`POST /push`):

```
1. Check if image already exists in registry DB (idempotent)
2. Verify image exists locally on Docker daemon
3. docker tag local-image registry:5000/user{user_id}/{app_name}:v{build}
4. docker push registry:5000/...
5. Extract digest and size from push output
6. Cleanup local images (free disk space)
7. Save metadata in registry_images table
```

The response MUST contain a `url` field (not `registry_url`) because the
Build Service expects `result.get("url")`.

**Health check**: Verifies both PostgreSQL connectivity and registry:5000 V2
API availability.

---

### 4.9 Security Scanner

**Purpose**: The most complex single service. Runs 5 parallel security scanners
on a built Docker image and makes a policy decision: PASS, WARN, or BLOCKED.

**Port**: 8006 (host), 8000 (internal)

**Dependencies**: Docker daemon, Trivy binary, ClamAV, YARA-python,
TruffleHog binary, Dockle binary

**Endpoints**:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Root with version |
| GET | `/health/` | Health check |
| GET | `/health/tools` | Check availability of all scanning tools |
| POST | `/scans/image` | Run full security scan on a Docker image |

**Scan pipeline** (`POST /scans/image`):

```
1. Extract image filesystem:
   ├─ docker create <image> (creates container from image)
   └─ docker cp <container>:/ <extract-dir> (copies filesystem)

2. Run 5 scanners in parallel (concurrent.futures.ThreadPoolExecutor):

   [a] TrivyScanner (CVEs)
       ├─ CLI: trivy image --scanners vuln --format json <image>
       ├─ Parses OS packages (Debian, Alpine) and language deps (pip, npm)
       └─ Returns list of vulnerabilities with severity, package, version

   [b] ClamavScanner (Malware)
       ├─ CLI: clamscan --recursive --infected <extract-dir>
       ├─ Signature-based virus/malware detection
       └─ Returns list of infected files with malware type

   [c] YaraScanner (Custom rules)
       ├─ Python YARA module matches rules against extracted files
       ├─ Rules detect: hardcoded passwords, crypto keys, config leaks
       └─ Returns list of matched rules with descriptions

   [d] TruffleHogScanner (Secrets)
       ├─ CLI: trufflehog filesystem --directory <extract-dir>
       ├─ Detects AWS keys, GitHub tokens, private keys, .env files
       ├─ Fallback: regex scanner for .pem, .key, .env, config patterns
       └─ Returns list of detected secrets with file paths

   [e] DockleScanner (Misconfigurations)
       ├─ CLI: dockle --exit-code 1 --format json <image>
       ├─ CIS Docker benchmark checks:
           • USER directive (should not be root)
           • sudo usage (should not be installed)
           • ADD vs COPY (prefer COPY)
           • Secrets in environment variables
           • Healthcheck present
       └─ Returns list of CIS violations

3. Base Image Checker:
   ├─ Checks if the image's base image is in the approved list
   ├─ Approved: python, node, golang, openjdk, ruby, php, rust,
   │  distroless, alpine, debian, ubuntu, nginx, httpd, scratch
   └─ Warns if using an unapproved base image

4. Result Aggregator (services/result_aggregator.py):
   ├─ Merges all 5 scanner results + base image check
   └─ Computes severity breakdown (critical/high/medium/low)

5. Policy Engine (services/policy_engine.py):
   ├─ Evaluates against 4 configurable policies:
   │  [a] BLOCK_ON_MALWARE (default: True)
   │      → Block if any malware detected
   │  [b] BLOCK_ON_SECRETS (default: True)
   │      → Block if any secrets/credentials detected
   │  [c] BLOCK_ON_HIGH_CVES (default: True)
   │      → Block if >50 critical CVEs or >500 high CVEs
   │  [d] BLOCK_ON_ROOT_USER (default: True)
   │      → Block if container runs as root
   └─ Returns verdict: PASS (all policies pass), WARN (policies pass but
      warnings exist), or BLOCKED (policy violation)

6. Response:
   {
     "status": "PASS" | "WARN" | "BLOCKED",
     "verdict": "All security checks passed" | "...",
     "severity_breakdown": { "critical": 0, "high": 2, ... },
     "block_reason": "..." | null,
     "policy_passed": true | false,
     "warnings": [...],
     "details": { "vulnerabilities": [...], "secrets": [...], ... }
   }
```

**Dockerfile details**:

The Security Scanner has the most complex Dockerfile in the project, using
a multi-stage build:

- Stage 1 (builder): Python 3.12 slim + build dependencies for YARA Python
  (`build-essential`, `libssl-dev`, `libffi-dev`, `python3-dev`).
- Stage 2 (runtime): Python 3.12 slim + ClamAV + Trivy (via official GPG
  repo) + TruffleHog (downloaded from GitHub releases) + YARA (from builder).

---

## 5. Database Schema

MiniPaaS uses a single PostgreSQL 16 database with 6 tables spread across
4 service owners. All tables live in the default `public` schema.

### `users` (owned by auth-service)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, GENERATED ALWAYS AS IDENTITY |
| email | VARCHAR | NOT NULL, UNIQUE |
| name | VARCHAR | |
| hashed_password | VARCHAR | |
| is_active | BOOLEAN | DEFAULT true |
| is_verified | BOOLEAN | DEFAULT false |
| oauth_provider | VARCHAR | |
| oauth_id | VARCHAR | |
| github_access_token | TEXT | |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

### `apps` (owned by app-management)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, GENERATED ALWAYS AS IDENTITY |
| name | VARCHAR | |
| repo_url | VARCHAR | |
| branch | VARCHAR | DEFAULT 'main' |
| env_vars | JSONB | DEFAULT '{}' |
| status | VARCHAR | DEFAULT 'pending' |
| public_url | VARCHAR | |
| created_at | TIMESTAMP | DEFAULT NOW() |

### `build_jobs` (owned by build-service)

| Column | Type | Constraints |
|--------|------|-------------|
| job_id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() |
| user_id | INTEGER | |
| repo_url | TEXT | |
| app_name | VARCHAR | |
| branch | VARCHAR | DEFAULT 'main' |
| status | VARCHAR | DEFAULT 'pending' |
| image_tag | VARCHAR | |
| image_url | VARCHAR | |
| build_logs | TEXT | |
| scan_result | JSONB | |
| created_at | TIMESTAMP | DEFAULT NOW() |
| finished_at | TIMESTAMP | |

`status` enum: `pending`, `running`, `success`, `failed`, `blocked`

### `deployments` (owned by deployer-service)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, GENERATED ALWAYS AS IDENTITY |
| user_id | INTEGER | NOT NULL |
| app_name | VARCHAR | NOT NULL |
| repo_url | TEXT | |
| branch | VARCHAR | DEFAULT 'main' |
| status | VARCHAR | DEFAULT 'pending' |
| build_job_id | UUID | |
| image_tag | VARCHAR | |
| image_url | VARCHAR | |
| container_id | VARCHAR | |
| container_port | INTEGER | |
| host_port | INTEGER | |
| container_url | VARCHAR | |
| build_logs | TEXT | |
| deploy_logs | TEXT | |
| error_message | TEXT | |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |
| started_at | TIMESTAMP | |
| stopped_at | TIMESTAMP | |

`status` enum: `pending`, `building`, `deploying`, `running`, `stopped`,
`failed`, `blocked`

### `container_metrics` (owned by monitoring-service)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, GENERATED ALWAYS AS IDENTITY |
| app_id | INTEGER | |
| user_id | INTEGER | |
| container_name | VARCHAR | |
| container_id | VARCHAR | |
| cpu_percent | FLOAT | |
| memory_usage_bytes | BIGINT | |
| memory_limit_bytes | BIGINT | |
| memory_percent | FLOAT | |
| network_rx_bytes | BIGINT | |
| network_tx_bytes | BIGINT | |
| status | VARCHAR | |
| collected_at | TIMESTAMP | DEFAULT NOW() |

### `log_entries` (owned by monitoring-service)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY, GENERATED ALWAYS AS IDENTITY |
| app_id | INTEGER | |
| user_id | INTEGER | |
| container_id | VARCHAR | |
| container_name | VARCHAR | |
| level | VARCHAR | |
| message | TEXT | |
| log_timestamp | TIMESTAMP | |
| collected_at | TIMESTAMP | DEFAULT NOW() |

### `registry_images` (owned by registry-service)

| Column | Type | Constraints |
|--------|------|-------------|
| image_id | INTEGER | PRIMARY KEY, GENERATED ALWAYS AS IDENTITY |
| user_id | INTEGER | |
| app_name | VARCHAR | |
| image_tag | VARCHAR | |
| registry_url | VARCHAR | |
| digest | VARCHAR | |
| size_bytes | BIGINT | |
| pushed_at | TIMESTAMP | DEFAULT NOW() |
| is_active | BOOLEAN | DEFAULT true |

---

## 6. Authentication & Authorization

MiniPaaS uses a JWT-based authentication system with two token types and
optional GitHub OAuth.

### Token Architecture

- **Access token**: Short-lived (15 minutes), signed with HS256, contains
  `sub` (user ID), `email`, `exp` (expiration), `iat` (issued at).
- **Refresh token**: Long-lived (7 days), signed with a separate secret,
  contains `sub` (user ID), `type: "refresh"`, `exp`, `iat`.

### Authentication Flow

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│  Client  │         │   Auth   │         │   Auth   │
│ (browser)│         │ Gateway  │         │ Service  │
└────┬─────┘         └────┬─────┘         └────┬─────┘
     │                    │                    │
     │  POST /auth/login  │                    │
     │───────────────────>│───────────────────>│
     │                    │                    │
     │  {access_token,    │                    │
     │   refresh_token}   │                    │
     │<───────────────────│<───────────────────│
     │                    │                    │
     │  GET /deployments  │                    │
     │  Authorization:    │                    │
     │  Bearer <access>   │                    │
     │───────────────────>│                    │
     │                    │  Decode JWT locally│
     │                    │  (API Gateway)     │
     │                    │                    │
     │                    │  Forward to        │
     │                    │  deployer-service  │
     │                    │───────────────────>│
     │                    │                    │
     │                    │  Verify token      │
     │                    │  via auth-service  │
     │                    │<───────────────────│
     │                    │                    │
     │<───────────────────│<───────────────────│
```

### Token Refresh Flow

When the access token expires (401 response), the client uses the refresh
token to get a new access token without requiring re-authentication:

```
1. Client receives 401 from any API call
2. Client sends POST /auth/refresh with refresh_token in body
3. Auth Service validates refresh token:
   ├─ Checks signature with REFRESH_TOKEN_SECRET
   ├─ Checks expiry (7 days)
   └─ Issues new access token (15 min) + new refresh token (7 days)
4. Client retries original request with new access token
```

This is handled transparently by the frontend's Axios interceptor.

### GitHub OAuth

Users can authenticate via GitHub OAuth:

1. Frontend redirects to `GET /auth/github` which returns a GitHub
   authorization URL.
2. User authorizes on GitHub.
3. GitHub redirects to `GET /auth/callback?code=...`.
4. Auth Service exchanges the code for a GitHub access token.
5. The token is stored in the `users.github_access_token` column.
6. The Deployer Service fetches this token when it needs to clone private
   repositories or list GitHub repos.

---

## 7. End-to-End Deployment Flow

This is the primary user journey — deploying a GitHub repository as a running
container.

```
┌─────────┐    ┌──────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐
│ Browser  │    │ Deployer │   │  Build   │   │ Scanner │   │ Registry │
│ (React)  │    │ Service  │   │ Service  │   │ Service │   │ Service  │
└────┬─────┘    └────┬─────┘   └────┬─────┘   └────┬────┘   └────┬─────┘
     │               │              │               │             │
     │ ① POST /deployments/         │               │             │
     │──────────────>│              │               │             │
     │               │ ② Verify JWT │               │             │
     │               │──> auth-svc │               │             │
     │               │              │               │             │
     │               │ ③ Create deployment record                │
     │               │  (status: building)                       │
     │               │              │               │             │
     │               │ ④ Get GitHub token                       │
     │               │──> auth-svc │               │             │
     │               │              │               │             │
     │               │ ⑤ POST /build              │             │
     │               │─────────────>│              │             │
     │               │              │ ⑥ Clone repo │             │
     │               │              │  (GitPython) │             │
     │               │              │              │             │
     │               │              │ ⑦ Detect lang│             │
     │               │              │  / gen Dockerfile          │
     │               │              │              │             │
     │               │              │ ⑧ Docker build│            │
     │               │              │  (Docker SDK)│             │
     │               │              │              │             │
     │               │              │ ⑨ POST /scans/image       │
     │               │              │─────────────>│             │
     │               │              │              │             │
     │               │              │              │⑩ 5 scanners│
     │               │              │              │  in parallel│
     │               │              │              │  ┌────────┐│
     │               │              │              │  │ Trivy  ││
     │               │              │              │  │ ClamAV ││
     │               │              │              │  │ YARA   ││
     │               │              │              │  │TruffleH││
     │               │              │              │  │ Dockle ││
     │               │              │              │  └────────┘│
     │               │              │              │  Policy    │
     │               │              │              │  Engine    │
     │               │              │              │─────────────│
     │               │              │ ⑪ Scan result│            │
     │               │              │<─────────────│             │
     │               │              │              │             │
     │               │              │ ⑫ If PASS:   │            │
     │               │              │    POST /push│────────────>│
     │               │              │<─────────────│             │
     │               │              │              │             │
     │               │ ⑬ Build result             │             │
     │               │<─────────────│              │             │
     │               │              │               │             │
     │               │ ⑭ Docker run (port 30000-40000)           │
     │               │  Container: minipaas-{uid}-{app}           │
     │               │  Labels: minipaas=true                     │
     │               │              │               │             │
     │               │ ⑮ Update status: "running"                │
     │<──────────────│              │               │             │
     │               │              │               │             │
     │ ⑯ Monitoring begins (every 30s via monitoring-service)    │
     │    CPU / Memory / Network / Logs collected                 │
```

**Step-by-step**:

| Step | Action | Service | Detail |
|------|--------|---------|--------|
| 1 | Create deployment | Browser → Deployer | POST /deployments/ with repo URL, app name, branch |
| 2 | Verify JWT | Deployer → Auth | GET /auth/me validates the access token |
| 3 | Create record | Deployer → DB | Insert into `deployments` table, status "building" |
| 4 | Get GitHub token | Deployer → Auth | GET /auth/github-token for private repo access |
| 5 | Trigger build | Deployer → Build | POST /build with repo URL, app name, branch |
| 6 | Clone repo | Build | GitPython clones to /tmp/builds/<job_id>/ |
| 7 | Detect lang | Build | Check for Dockerfile → requirements.txt → package.json → ... |
| 8 | Build image | Build | Docker SDK builds and tags image |
| 9 | Scan image | Build → Scanner | POST /scans/image with image tag |
| 10 | 5 scanners | Scanner | Trivy, ClamAV, YARA, TruffleHog, Dockle run in parallel |
| 11 | Scan result | Scanner → Build | PASS/WARN/BLOCKED verdict with details |
| 12 | Push image | Build → Registry | POST /push if policy passes, image pushed to registry:5000 |
| 13 | Build result | Build → Deployer | Build status, image tag, logs |
| 14 | Run container | Deployer | Docker SDK: port allocation, create + start container |
| 15 | Update status | Deployer → DB | Deployment status → "running" |
| 16 | Monitoring | Monitoring (background) | APScheduler collects stats every 30s |

---

## 8. Frontend Architecture

**Tech stack**: React 18, TypeScript, Vite, Tailwind CSS, React Router v6,
Axios, Recharts, Framer Motion.

### Pages

| Route | Component | Auth | Description |
|-------|-----------|------|-------------|
| `/` | Home | No | Landing page with Login/Register links |
| `/login` | Login | No | Email/password + GitHub OAuth button |
| `/register` | Register | No | Email/password registration form |
| `/oauth/github/callback` | GitHubCallback | No | Handles GitHub OAuth redirect |
| `/dashboard` | Dashboard | Yes | Stats (deployments count, active, failed), quick actions |
| `/deployments` | Deployments | Yes | Table with auto-refresh (5s), status badges |
| `/repos` | Repositories | Yes | GitHub repo browser for selection |
| `/deploy/new` | NewDeployment | Yes | Form: select repo, branch, app name |
| `/monitoring` | Monitoring | Yes | Real-time metrics table (15s auto-refresh) |

### API Layer (`lib/api.ts`)

- `authApi`: register, login, githubAuthUrl, githubCallback, getMe,
  refreshToken, health.
- `deployerApiService`: getRepos, getBranches, getDeployments, getDeployment,
  createDeployment, stopDeployment, startDeployment, restartDeployment,
  deleteDeployment, getDeploymentLogs.
- Axios interceptors: on 401 response, automatically attempts token refresh,
  then retries the original request.

### Auth Context (`context/AuthContext.tsx`)

- Stores access token and refresh token in localStorage.
- Provides `login()`, `register()`, `logout()`, `refreshAccessToken()`,
  `completeGitHubLogin()` functions.
- `ProtectedRoute` wrapper redirects unauthenticated users to `/login`.

### Nginx Reverse Proxy

The frontend's Nginx serves static files on port 8080 and proxies API calls
to the API Gateway:

```
location /auth/          { proxy_pass http://api-gateway:8000/auth/; }
location /deployments/   { proxy_pass http://api-gateway:8000/deployments/; }
location /repos/         { proxy_pass http://api-gateway:8000/repos/; }
location /builds/        { proxy_pass http://api-gateway:8000/builds/; }
location /monitoring/    { proxy_pass http://api-gateway:8000/monitoring/; }
location /scanner/       { proxy_pass http://api-gateway:8000/scanner/; }
location /registry/      { proxy_pass http://api-gateway:8000/registry/; }
location = /health       { proxy_pass http://api-gateway:8000/health; }
location /                { try_files $uri $uri/ /index.html; }
```

All other paths serve `index.html` for SPA routing.

---

## 9. Security Scanner Internals

The Security Scanner is the most complex service. It orchestrates 5 scanning
tools and a policy engine.

### Scanner Architecture

```
POST /scans/image { image_tag, user_id, app_name }
                │
                ▼
        ┌───────────────┐
        │  Extract image │  docker create → docker cp
        │  filesystem    │
        └───────┬───────┘
                │
        ┌───────┴───────────────────────┐
        │       ThreadPoolExecutor      │
        │  (parallel execution)         │
        │                               │
        │  ┌──────────┐  ┌──────────┐  │
        │  │  Trivy   │  │  ClamAV  │  │
        │  │  (CVEs)  │  │ (Malware)│  │
        │  └──────────┘  └──────────┘  │
        │  ┌──────────┐  ┌──────────┐  │
        │  │  YARA    │  │TruffleHog│  │
        │  │(Secrets) │  │(Secrets) │  │
        │  └──────────┘  └──────────┘  │
        │  ┌──────────┐                │
        │  │ Dockle   │                │
        │  │(BestPrac)│                │
        │  └──────────┘                │
        └───────┬───────────────────────┘
                │
                ▼
        ┌───────────────┐
        │   Aggregator  │  Merge results, compute severity
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │     Policy    │  Evaluate against thresholds
        │    Engine     │
        └───────┬───────┘
                │
                ▼
        { status: "PASS"|"WARN"|"BLOCKED", ... }
```

### Scanner Details

**TrivyScanner** (`scanners/trivy_scanner.py`):

- Runs `trivy image --scanners vuln --format json <image>`.
- Parses the JSON output for vulnerabilities grouped by target (OS packages,
  Python packages, npm packages, Go binaries).
- Extracts: vulnerability ID, severity, package name, installed version,
  fixed version, title, URL.
- The Trivy DB is cached via a Docker volume (`trivy_cache`) to avoid
  re-downloading on every scan.

**ClamavScanner** (`scanners/clamav_scanner.py`):

- Runs `clamscan --recursive --infected --no-summary <extract-dir>`.
- The ClamAV daemon (`clamd`) runs in the container background.
- A `freshclam` cron job updates virus definitions.
- Returns list of infected files with malware type names.

**YaraScanner** (`scanners/yara_scanner.py`):

- Uses the Python `yara` module to compile and match rules against every
  file in the extracted filesystem.
- Rules detect: hardcoded passwords, cryptographic keys, configuration
  file leaks, secret patterns.
- YARA rules are stored in `src/scanners/rules/`.

**TruffleHogScanner** (`scanners/trufflehog_scanner.py`):

- Primary: runs `trufflehog filesystem --directory <extract-dir>`.
- Fallback (if TruffleHog binary unavailable or fails): regex-based scanner
  that checks for `.env`, `.pem`, `.key`, SSH keys, AWS access keys,
  GitHub tokens in extracted files.
- Returns list of detected secrets with file paths and match context.

**DockleScanner** (`scanners/dockle_scanner.py`):

- Runs `dockle --exit-code 1 --format json <image>`.
- Checks CIS Docker benchmarks:
  - `CIS-DI-0001`: Container should not run as root (`USER` directive).
  - `DKL-DI-0005`: sudo should not be installed.
  - `DKL-DI-0006`: Prefer COPY over ADD.
  - `CIS-DI-0010`: Sensitive environment variables.
  - `CIS-DI-0005`: Healthcheck should be present.

### Policy Engine (`services/policy_engine.py`)

Configurable via environment variables (set in `k8s/configmap.yaml`):

| Policy | Default | Threshold |
|--------|---------|-----------|
| `BLOCK_ON_MALWARE` | True | Any malware finding → BLOCKED |
| `BLOCK_ON_SECRETS` | True | Any secret finding → BLOCKED |
| `BLOCK_ON_HIGH_CVES` | True | >50 critical OR >500 high → BLOCKED |
| `BLOCK_ON_ROOT_USER` | True | USER is root → BLOCKED |

Additional warnings (do not block, but recorded):

| Warning | Threshold |
|---------|-----------|
| High CVEs count | >10 and ≤500 |
| Medium CVEs count | >50 |
| Low CVEs count | >100 |
| Unapproved base image | Not in approved list |

---

## 10. Monitoring & Observability

### Container Metrics Collection (Monitoring Service)

The Monitoring Service runs an APScheduler with 3 periodic jobs:

**collect_metrics_job** (every `COLLECT_INTERVAL_SECONDS`, default 30s):

```
For each container with label "minipaas=true" or name matching "minipaas_*":
  stats = container.stats(stream=False)
  cpu_percent = calculate_cpu(stats)
  memory_usage = stats['memory_stats']['usage']
  memory_limit = stats['memory_stats']['limit']
  network = stats['networks']
  INSERT INTO container_metrics (...)
```

**collect_logs_job** (every 30s):

```
For each monitored container:
  logs = container.logs(tail=20, timestamps=True)
  Parse log level (INFO/WARN/ERROR/DEBUG) from each line
  INSERT INTO log_entries (...)
```

**cleanup_old_metrics_job** (every hour):

```
DELETE FROM container_metrics WHERE collected_at < NOW() - INTERVAL '7 days'
DELETE FROM log_entries WHERE collected_at < NOW() - INTERVAL '7 days'
```

### Prometheus Exposition

The Monitoring Service exposes a `/metrics` endpoint in Prometheus text format
with 5 metric families:

```
# HELP minipaas_container_cpu_percent CPU usage percentage
# TYPE minipaas_container_cpu_percent gauge
minipaas_container_cpu_percent{app_id="1",user_id="1",container="minipaas-1-myapp"} 12.5

# HELP minipaas_container_memory_usage_bytes Memory usage in bytes
# TYPE minipaas_container_memory_usage_bytes gauge
minipaas_container_memory_usage_bytes{app_id="1",user_id="1",container="minipaas-1-myapp"} 41943040

# HELP minipaas_container_memory_percent Memory usage percentage
# TYPE minipaas_container_memory_percent gauge
minipaas_container_memory_percent{app_id="1",user_id="1",container="minipaas-1-myapp"} 25.0

# HELP minipaas_container_network_rx_bytes Network received bytes
# TYPE minipaas_container_network_rx_bytes counter
minipaas_container_network_rx_bytes{app_id="1",user_id="1",container="minipaas-1-myapp"} 1024000

# HELP minipaas_container_network_tx_bytes Network transmitted bytes
# TYPE minipaas_container_network_tx_bytes counter
minipaas_container_network_tx_bytes{app_id="1",user_id="1",container="minipaas-1-myapp"} 512000
```

### Grafana Dashboards

Two dashboards are provisioned via ConfigMap in the K8s monitoring stack:

**K3s Cluster Overview**:
- Node CPU gauge
- Node Memory gauge
- Node Disk gauge
- Total pod count
- CPU by namespace (bar gauge)
- Memory by namespace (bar gauge)
- Top 10 pods by CPU
- Top 10 pods by Memory
- Deployment availability (desired vs available)
- Container restarts (last 1 hour)

**MiniPaaS Service Detail**:
- Running vs failed pods (stat)
- CPU timeseries per pod
- Memory timeseries per pod
- Container restarts (bar gauge)
- Network I/O per pod (rx/tx)

### Prometheus Scrape Jobs

Prometheus is configured with 7 scrape jobs:

| Job | Target | Port |
|-----|--------|------|
| prometheus | Self | 9090 |
| node-exporter | All nodes (via Service) | 9100 |
| kube-state-metrics | kube-state-metrics | 8080 |
| kubernetes-nodes | kubelet /metrics | 10250 |
| kubernetes-nodes-cadvisor | kubelet /metrics/cadvisor | 10250 |
| kubernetes-service-endpoints | Any service with annotation prometheus.io/scrape=true | varies |
| kubernetes-pods | Any pod with annotation prometheus.io/scrape=true | varies |

---

# Part 2 — DevSecOps Lifecycle of MiniPaaS

---

## 11. Development Workflow

### Local Setup

The project provides a Makefile and scripts directory for local development:

```bash
# Initial setup: copy .env, install dependencies
make setup

# Start all services via Docker Compose
make dev

# Run all tests
make test

# Lint all code
make lint

# Build all Docker images
make build

# Stop and clean up
make stop
make clean
```

The `scripts/` directory contains the implementation of each Makefile target:

| Script | Purpose | Makefile target |
|--------|---------|-----------------|
| `scripts/setup.sh` | Copy `.env.example` → `.env`, pip install all service deps | `setup` |
| `scripts/dev.sh` | `docker compose up -d`, print service URLs | `dev` |
| `scripts/test-all.sh` | Iterate services, run `pytest tests/ -v` in each | `test` |
| `scripts/lint-all.sh` | Run ruff on all services, ESLint + tsc on frontend | `lint` |
| `scripts/e2e-test.sh` | Full end-to-end test: register → login → deploy bad app (expect block) → deploy good app → check monitoring | (manual) |

### Environment Configuration

Environment variables are managed through:

- `.env.example` — documented template with all required variables.
- `.env` — local overrides (gitignored).
- Service-specific `.env` files in each `services/*/` directory.
- Kubernetes ConfigMap + Secret for production deployment.

### Git Workflow

- Single `main` branch.
- All commits pushed to `main` trigger the full CI/CD pipeline.
- Pull requests also trigger CI (without deployment).
- Commit history is linear with descriptive messages.

---

## 12. CI/CD Pipeline Overview

The CI/CD pipeline is defined in `.github/workflows/lint.yml` and consists
of 8 sequential jobs. Each job must pass before the next can start.

```
Push/PR to main
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Job 1: Secret Scan (gitleaks)                                      │
│  Scans full git history for leaked secrets                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Job 2: Python Lint (ruff)                                         │
│  Fast Rust-based linter on all services/ Python code               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Job 3: Frontend Quality (ESLint + tsc)                            │
│  ESLint with --max-warnings=0 + TypeScript type checking           │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Job 4: Tests                                                      │
│  ├─ Frontend: Vitest (20 tests)                                   │
│  └─ Python: pytest per service (83 tests)                         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Job 5: SonarCloud Analysis                                        │
│  Static analysis + coverage (async quality gate)                   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Job 6: Docker Lint (Hadolint + Checkov)                           │
│  Lint all Dockerfiles + IaC security scanning                      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Job 7: Build, Scan & Push                                         │
│  ├─ docker compose build                                          │
│  ├─ Trivy vulnerability scan (HIGH/CRITICAL, --exit-code 1)       │
│  ├─ Dockle best-practices scan                                    │
│  └─ Push images to ghcr.io/carbon14-48/ (latest + commit SHA)    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Job 8: Deploy to K3s (self-hosted runner)                         │
│  ├─ Pull images directly into k3s containerd                       │
│  ├─ Apply all 42 K8s manifests                                    │
│  ├─ Inject GitHub OAuth secrets                                    │
│  └─ Rollout restart + wait for all deployments                     │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                      ┌─────────────────────┐
                      │  Production K3s      │
                      │  (13+ pods running)  │
                      └─────────────────────┘
```

**Timeline**: ~20-30 minutes end-to-end.
**Trigger**: Push or PR to `main` branch.
**Runner**: GitHub-hosted (jobs 1-7), self-hosted K3s node (job 8).
**Permissions**: `contents: read`, `packages: write`.

---

## 13. Secret Scanning (Gitleaks)

**Job**: `gitleaks` (Job 1, first line of defense)

**Tool**: [Gitleaks](https://github.com/gitleaks/gitleaks-action) v2 via
GitHub Action.

**Configuration**:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0    # Scan entire git history, not just HEAD
- uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**What it detects**:

- API keys (AWS, Google, GitHub, Slack, etc.)
- Private keys (RSA, DSA, EC, PGP)
- Authentication tokens (Bearer, Basic)
- Database connection strings
- High-entropy strings that look like secrets
- Password fields in configuration files

**Why first**: Secret leaks are the most damaging security incidents.
Catching them first prevents accidental credential exposure from entering
the container images or Kubernetes cluster.

**CI enforcement**: If Gitleaks finds any secret in any commit, the pipeline
stops immediately — no code is tested, built, or deployed.

---

## 14. Code Quality & Static Analysis

### Python Lint — Ruff (Job 2)

**Tool**: [Ruff](https://github.com/astral-sh/ruff-action) — a fast Python
linter written in Rust (1000x faster than Flake8).

**Scope**: All Python files in `services/` directory.

**Configuration**: Default Ruff rules (includes pycodestyle, pyflakes, isort).

**CI enforcement**: Any lint error fails the job. Zero-warning policy.

### Frontend Quality — ESLint + TypeScript (Job 3)

**Tools**:
- ESLint with `typescript-eslint` for code quality and style.
- TypeScript Compiler (`tsc --noEmit`) for type safety.

**Scope**: All files in `frontend/src/`.

**CI enforcement**:

```yaml
- run: npx eslint src/ --max-warnings=0
- run: npx tsc --noEmit
```

`--max-warnings=0` means even a single warning fails the build.
`tsc --noEmit` catches type errors without generating output files.

### SonarCloud Static Analysis (Job 5)

**Tool**: [SonarCloud](https://sonarcloud.io) — cloud-based static analysis
platform.

**Configuration** (`sonar-project.properties`):

```properties
sonar.projectKey=Carbon14-48_MiniPaaS
sonar.organization=carbon14-48
sonar.host.url=https://sonarcloud.io
sonar.sources=frontend/src,services
sonar.tests=frontend/tests
sonar.javascript.lcov.reportPaths=frontend/coverage/lcov.info
sonar.python.coverage.reportPaths=coverage.xml
```

**What it analyzes**:
- **JavaScript/TypeScript**: Code quality, test coverage (from Vitest/LCOV),
  duplicated code, code smells, security hotspots.
- **Python**: Test coverage (from pytest-cov/coverage.xml), code quality,
  potential bugs, security vulnerabilities.

**Coverage collection**:

```yaml
# Frontend coverage
- run: npm run test:coverage
  working-directory: frontend

# Python coverage
- run: |
    pytest services/ \
      --cov=services/ \
      --cov-report=xml:coverage.xml \
      --ignore=services/security-scanner/tests \
      || echo "Some python tests failed, continuing for coverage"
```

**Quality gate**: `sonar.qualitygate.wait=false` — the CI does not block on
SonarCloud quality gate failures, but they are reported for review.

---

## 15. Testing Strategy

### Frontend Tests (Vitest)

**Framework**: Vitest (Vite-native test runner, Jest-compatible API).

**Environment**: jsdom (browser-like environment for React component testing).

**Test count**: 20 tests across 4 test files.

**Technologies**: `@testing-library/react` for component rendering and
interaction simulation.

**CI execution**:

```yaml
- run: npm ci
  working-directory: frontend
- run: npm run test
  working-directory: frontend
```

### Python Tests (pytest)

**Framework**: pytest with coverage plugins.

**Architecture**: Tests are organized per-service, each in its own
`services/<name>/tests/` directory.

**Test count**: 83 tests across 6 services (security-scanner tests are
excluded from CI because they require Docker daemon access).

**CI execution**:

```yaml
- run: |
    python -m venv /tmp/venv
    . /tmp/venv/bin/activate
    for req in services/*/requirements.txt; do
      pip install --quiet -r "$req" 2>/dev/null || true
    done
    pip install --quiet pytest
    failed=0
    for svc in services/*/; do
      svc_name=$(basename "$svc")
      [ "$svc_name" = "security-scanner" ] && continue
      [ -d "$svc/tests" ] || continue
      echo "=== $svc_name ==="
      pytest "$svc/tests" --tb=short -v || failed=1
    done
    exit $failed
```

**Key design decisions**:

- **Per-service loop**: Each service's tests run in isolation. A failure in
  one service does not block the others from running, but the overall job
  fails.
- **Security Scanner skip**: The security-scanner tests require Docker socket
  access (they build and scan actual images), which is not available in the
  GitHub Actions runner.
- **`pip install --quiet -r "$req" 2>/dev/null || true`**: Dependency
  installation failures are tolerated — a service's tests will fail only if
  its dependencies are actually needed and missing.

### End-to-End Tests (manual)

The `scripts/e2e-test.sh` script performs a full end-to-end test:

1. Start all services via Docker Compose.
2. Register a test user (`e2e@test.com` / `TestPass123`).
3. Login to get JWT tokens.
4. Deploy a known-bad repository — expects BLOCKED by security scanner.
5. Deploy a known-good repository — expects RUNNING.
6. Query monitoring endpoints to verify metrics collection.

This test is not part of CI because it requires a running Docker Compose
environment.

---

## 16. Dockerfile Security & Linting

### Dockerfile Patterns

MiniPaaS uses consistent Dockerfile patterns across all services:

**Multi-stage builds** (used by api-gateway, app-management, auth-service,
deployment-service, security-scanner, frontend):

```dockerfile
# Stage 1: Build/dependency stage
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: --prefix=/install -r requirements.txt

# Stage 2: Runtime stage (minimal)
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
EXPOSE 8000
USER nobody
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import socket;s=socket.socket();s.connect(('localhost',8000));s.close()" || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Security practices applied**:

| Practice | Implementation |
|----------|---------------|
| Minimal base images | `python:3.12-slim` (Debian-based, ~120MB) |
| Non-root user | `USER nobody` or `USER nginx` |
| Multi-stage builds | Build deps removed from final image |
| `--only-binary :all:` | No source compilation in runtime |
| Healthcheck | TCP socket check on service port |
| No cache layers | `--no-cache-dir` for pip |
| Frontend | `nginxinc/nginx-unprivileged` (non-root nginx) |

**Services requiring root** (for Docker socket access): build-service,
deployer-service, registry-service, monitoring-service, security-scanner.
These suppress the `CKV_DOCKER_3` Checkov rule.

### Hadolint (Job 6a)

**Tool**: [Hadolint](https://github.com/hadolint/hadolint) — Dockerfile
linter that checks for best practices.

**Scope**: All 10 Dockerfiles (9 services + frontend).

**CI execution**:

```yaml
- name: Hadolint
  run: |
    for f in services/*/Dockerfile frontend/Dockerfile; do
      echo "=== $f ==="
      docker run --rm -i ghcr.io/hadolint/hadolint < "$f"
    done
```

**What it checks**:
- `FROM` pinning (using specific tags, not `latest`)
- `RUN` layer count (prefer chaining with `&&`)
- `COPY` vs `ADD` (prefer COPY for local files)
- `USER` directive (should not default to root)
- `EXPOSE` presence
- `WORKDIR` usage
- Apt-get best practices (`-y`, `--no-install-recommends`, clean after install)
- Pipefail usage in `RUN` commands

### Checkov (Job 6b)

**Tool**: [Checkov](https://github.com/bridgecrewio/checkov-action) —
infrastructure-as-code security scanner.

**Scope**: All Dockerfiles in the repository.

**Mode**: `quiet: true` — only displays failures.

**What it checks** (Dockerfile-specific):
- `CKV_DOCKER_1`: Ensure `ADD` is not used for remote URLs.
- `CKV_DOCKER_2`: Ensure `HEALTHCHECK` is defined.
- `CKV_DOCKER_3`: Ensure `USER` is not root.
- `CKV_DOCKER_4`: Ensure `COPY` is used instead of `ADD` for local files.
- `CKV_DOCKER_5`: Ensure `apt-get` uses `--no-install-recommends`.
- `CKV_DOCKER_6`: Ensure `apt-get` cleans up after install.
- `CKV2_DOCKER_17`: Ensure ClamAV password authentication is enabled
  (suppressed for security-scanner).

---

## 17. Container Vulnerability Management

### Trivy Vulnerability Scanning (Job 7)

**Tool**: [Trivy](https://github.com/aquasecurity/trivy) by Aqua Security —
comprehensive vulnerability scanner for containers.

**Scope**: All 10 Docker images built by `docker compose build`.

**Severity threshold**: HIGH and CRITICAL only.

**Exit code**: `--exit-code 1` — any finding fails the build.

**CI execution**:

```yaml
- name: Trivy scan all images
  run: |
    failed=0
    for img in $(docker images --format "{{.Repository}}" | grep minipaas); do
      echo "=== Scanning $img ==="
      docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
        -v /tmp/trivy-cache:/root/.cache/trivy \
        -v $PWD/.trivyignore:/.trivyignore \
        aquasec/trivy image \
        --severity HIGH,CRITICAL \
        --exit-code 1 \
        --ignorefile /.trivyignore \
        "$img" || failed=1
    done
    [ "$failed" -eq 0 ] || exit 1
```

**What Trivy detects**:
- **OS vulnerabilities**: Debian/Alpine package-level CVEs (apt, apk).
- **Language-specific vulnerabilities**:
  - Python (pip packages from requirements.txt)
  - Node.js (npm packages from package.json)
  - Go binaries (embedded dependencies)

**Trivy DB**: Downloaded on first run, cached in `/tmp/trivy-cache` volume
for subsequent scans.

### Dockle Best-Practices Scan (Job 7)

**Tool**: [Dockle](https://github.com/goodwithtech/dockle) — container image
linter for CIS benchmark compliance.

**Scope**: All 10 Docker images.

**CI execution**:

```yaml
- name: Dockle scan all images
  run: |
    failed=0
    for img in $(docker images --format "{{.Repository}}" | grep minipaas); do
      ignore_flags=""
      case "$img" in
        *frontend|*deployment-service|*auth-service|*app-management|*api-gateway)
          ;;
        *)
          ignore_flags="--ignore CIS-DI-0001"
          ;;
      esac
      docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
        goodwithtech/dockle \
        --exit-code 1 \
        --accept-key KEY_SHA512 \
        --ignore DKL-DI-0005 \
        --ignore DKL-DI-0006 \
        --ignore CIS-DI-0010 \
        $ignore_flags \
        "$img" || failed=1
    done
    [ "$failed" -eq 0 ] || exit 1
```

**What Dockle checks**:
- `CIS-DI-0001`: Image should not run as root (—ignored for services that
  mount Docker socket).
- `DKL-DI-0005`: sudo should not be installed.
- `DKL-DI-0006`: Prefer COPY over ADD.
- `CIS-DI-0010`: Sensitive environment variables should not be in image.
- `KEY_SHA512`: Accept SHA512 key trust level.

### Vulnerability Management Policy

The `.trivyignore` file tracks all accepted CVEs with documented rationale:

```
# OS-level CVEs with no fix available yet (Debian/Alpine package maintainers)
CVE-2026-5773
CVE-2026-6276
...
(28 CVEs + 1 GHSA)

# libexpat1 CVEs - no fix available from Debian yet
CVE-2025-59375
CVE-2026-25210
CVE-2026-45186

# starlette CVEs - requires fastapi upgrade to >0.116.x for starlette>=0.49.1
CVE-2024-47874
CVE-2025-62727
CVE-2026-48818
CVE-2026-54283

# PyJWT CVE - requires upgrade to pyjwt>=2.13.0
CVE-2026-48526

# containerd CVEs in Debian base image + embedded trivy binary (not our code)
CVE-2026-53488
CVE-2026-53489
CVE-2026-53492
```

**Categories of accepted risk**:

1. **OS package CVEs with no fix** — Debian/Alpine maintainers haven't
   released patched packages. These are tracked and periodically reviewed.
2. **Transitive dependency CVEs** — e.g., Starlette CVEs that require a
   FastAPI upgrade. Tracked with a plan to upgrade when feasible.
3. **Infrastructure CVEs** — e.g., containerd CVEs in the base image or
   embedded tools (Trivy binary itself). Not in the application code.
4. **All accepted CVEs are documented with reasons**. This is not a blanket
   ignore — each has a specific justification and tracking context.

---

## 18. Image Registry & Artifact Management

### GitHub Container Registry (GHCR)

All Docker images are pushed to `ghcr.io/carbon14-48/`:

```
ghcr.io/carbon14-48/minipaas-api-gateway:latest
ghcr.io/carbon14-48/minipaas-api-gateway:<commit-sha>
ghcr.io/carbon14-48/minipaas-auth-service:latest
ghcr.io/carbon14-48/minipaas-auth-service:<commit-sha>
...
(10 images total)
```

**Tagging strategy**:
- `:latest` — always points to the most recent successful build on `main`.
- `:<commit-sha>` — pinned to the exact Git commit for traceability.

**Authentication**: GitHub Actions uses the built-in `GITHUB_TOKEN` with
`packages: write` permission. The self-hosted deploy runner uses a separate
`ghcr-secret` Kubernetes secret (created manually).

**Push flow** (only on push to main, not PR):

```yaml
- name: Push images to GHCR
  if: github.event_name == 'push'
  run: |
    for img in $(docker images --format "{{.Repository}}" | grep minipaas); do
      docker tag "$img:latest" "ghcr.io/carbon14-48/$img:latest"
      docker tag "$img:latest" "ghcr.io/carbon14-48/$img:${{ github.sha }}"
      docker push "ghcr.io/carbon14-48/$img:latest"
      docker push "ghcr.io/carbon14-48/$img:${{ github.sha }}"
    done
```

### Python Dependency Pinning

All `requirements.txt` files use exact version pinning:

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.5
pydantic-settings==2.7.1
```

This ensures reproducible builds: every build uses the same dependency
versions regardless of when it runs.

### Build Caching

- Docker layer caching via GitHub Actions cache.
- Trivy vulnerability DB cached via Docker volume `trivy_cache`.
- npm dependencies cached via GitHub Actions `actions/setup-node` cache.

---

## 19. Kubernetes Deployment (K3s)

### Cluster Architecture

MiniPaaS deploys to a lightweight K3s Kubernetes cluster running on a single
node (a Lenovo ThinkCentre mini-PC). K3s is a CNCF-certified Kubernetes
distribution packaged as a single binary.

**Cluster setup** (`k3s-setup.sh`):

```bash
# Install K3s
curl -sfL https://get.k3s.io | sh -

# Wait for node to be ready
kubectl wait node --all --for=condition=Ready --timeout=60s

# Copy kubeconfig
cp /etc/rancher/k3s/k3s.yaml ~/.kube/config

# Create namespace
kubectl create namespace minipaas
```

### Namespace Structure

| Namespace | Purpose | Resources |
|-----------|---------|-----------|
| `minipaas` | Application services | 10 deployments + 10 services + postgres + registry + ingress + configs |
| `monitoring` | Observability stack | Prometheus + Grafana + kube-state-metrics + node-exporter |

### Manifest Organization

```
k8s/
├── namespace.yaml              # minipaas Namespace
├── configmap.yaml              # 39 configuration keys
├── secret.yaml                 # 8 sensitive values (placeholders)
├── ingress.yaml                # Traefik Ingress → frontend:8080
├── postgres/                   # PostgreSQL 16 StatefulSet + Service
├── registry/                   # Docker registry:2 Deployment + Service + PVC
├── frontend/                   # React SPA Deployment + Service + Nginx ConfigMap
├── api-gateway/
├── auth-service/
├── app-management/
├── build-service/
├── deployment-service/
├── deployer-service/
├── registry-service/
├── monitoring-service/
├── security-scanner/
└── monitoring/
    ├── namespace.yaml
    ├── prometheus/             # Deployment + Service + ConfigMap + RBAC
    ├── grafana/                # Deployment + Service (NodePort 30300) + ConfigMap
    ├── kube-state-metrics/     # Deployment + Service + RBAC
    └── node-exporter/          # DaemonSet + Service
```

### Configuration Injection

All deployments use the same `envFrom` pattern to inject configuration:

```yaml
envFrom:
  - configMapRef:
      name: minipaas-config
  - secretRef:
      name: minipaas-secret
```

This means every service gets ALL configuration keys and ALL secret values
as environment variables. Services read only what they need from their own
`config.py` using `pydantic-settings`.

### Service Discovery

Kubernetes DNS-based service discovery is used for all inter-service
communication. Each service connects to others using the service name:

```python
# Example: deployer-service connecting to auth-service
AUTH_SERVICE_URL = "http://auth-service:8000"
BUILD_SERVICE_URL = "http://build-service:8002"
REGISTRY_SERVICE_URL = "http://registry-service:8005"
```

All services in the same namespace (`minipaas`) use the short DNS name
`<service-name>:<port>`.

### Deployment Flow (Job 8)

**Script**: `deploy-from-ghcr.sh`

**Steps**:

```
1. Pull images into k3s containerd (no Docker daemon needed):
   k3s ctr images pull ghcr.io/carbon14-48/minipaas-<service>:latest

2. Apply manifests in dependency order:
   ├─ namespace.yaml → configmap.yaml → secret.yaml
   ├─ postgres/ (StatefulSet + Service)
   ├─ auth-service → app-management → build-service → deployment-service
   ├─ deployer-service → monitoring-service
   ├─ registry/ → registry-service → security-scanner
   ├─ api-gateway → frontend
   └─ monitoring/ (Prometheus → Grafana → kube-state-metrics → node-exporter)

3. Inject GitHub OAuth credentials into the existing secret:
   kubectl patch secret minipaas-secret \
     -p "{\"stringData\":{\"GITHUB_CLIENT_ID\":\"...\",\"GITHUB_CLIENT_SECRET\":\"...\"}}"

4. Rollout restart all deployments:
   kubectl rollout restart -n minipaas deployment/...

5. Wait for all rollouts to complete (300s timeout per service).
```

### CI/CD Self-Hosted Runner

The deployment job runs on a **self-hosted GitHub Actions runner** installed
on the same machine as the K3s cluster. The runner:

- Has `kubectl` access to the local K3s cluster.
- Has `k3s ctr` access for direct image pulling.
- Does NOT have Docker daemon (images are pulled directly into containerd).
- Runs as a systemd service for automatic restart.

---

## 20. Production Monitoring Stack

MiniPaaS deploys a complete monitoring stack alongside the application.

### Components

| Component | Version | Purpose | Port |
|-----------|---------|---------|------|
| Prometheus | v2.55.1 | Metrics collection and storage | 9090 (ClusterIP) |
| Grafana | v11.4.0 | Metrics visualization and dashboards | 3000 (NodePort 30300) |
| kube-state-metrics | v2.15.0 | Kubernetes object metrics | 8080 (ClusterIP) |
| node-exporter | v1.8.2 | Node-level hardware/OS metrics | 9100 (ClusterIP) |

### Prometheus Configuration

**7 scrape jobs** defined in `prometheus/configmap.yaml`:

**Job 1 — prometheus**: Scrapes itself (up metrics, storage stats).

**Job 2 — node-exporter**: Discovers node-exporter DaemonSet pods via
Kubernetes service discovery, filtered to `monitoring` namespace, service
name `node-exporter`.

**Job 3 — kube-state-metrics**: Discovers kube-state-metrics pods in
`monitoring` namespace.

**Job 4 — kubernetes-nodes**: Scrapes kubelet `/metrics` endpoint on each
node for node-level metrics (CPU, memory, disk, network).

**Job 5 — kubernetes-nodes-cadvisor**: Scrapes kubelet `/metrics/cadvisor`
endpoint for container-level metrics (per-container CPU, memory, filesystem,
network).

**Job 6 — kubernetes-service-endpoints**: Auto-discovers any Service in any
namespace (except `monitoring`) annotated with `prometheus.io/scrape: "true"`.
Supports custom scheme, path, and port via annotations. This allows the
MiniPaaS Monitoring Service to be auto-discovered when it adds the annotation.

**Job 7 — kubernetes-pods**: Auto-discovers any Pod annotated with
`prometheus.io/scrape: "true"`.

**Storage**: 7-day retention (`--storage.tsdb.retention.time=7d`).

### Grafana Configuration

**Provisioning**: Datasources and dashboards are auto-provisioned at startup.

**Datasource**: Prometheus at `http://prometheus:9090` (default).

**Dashboard 1 — K3s Cluster Overview**:

```
Row 1: Node CPU gauge | Node Memory gauge | Node Disk gauge | Pod count
Row 2: CPU by namespace (bar gauge) | Memory by namespace (bar gauge)
Row 3: Top 10 pods by CPU | Top 10 pods by Memory
Row 4: Deployment availability | Container restarts (last 1h)
```

**Dashboard 2 — MiniPaaS Service Detail**:

```
Row 1: Running vs Failed pods | Total pods
Row 2: CPU timeseries by pod | Memory timeseries by pod
Row 3: Container restarts (bar gauge) | Network I/O by pod
```

**Access**: Grafana is exposed on NodePort 30300 with anonymous access enabled
(admin/admin credentials for configuration).

### Node Exporter (DaemonSet)

Runs on every node in the cluster, collecting:
- CPU usage (user, system, iowait, idle)
- Memory usage (total, free, available, cached, buffers)
- Disk usage (read/write bytes, I/O operations)
- Network usage (bytes/packets in/out, errors, drops)
- Filesystem usage (size, used, available, inodes)

Uses `hostNetwork: true` and `hostPID: true` for host-level metrics.

### Kube State Metrics

Collects Kubernetes object state metrics:
- Node status, capacity, allocatable resources
- Pod status (running, pending, failed, crashloop)
- Deployment status (desired, available, unavailable replicas)
- Service, ConfigMap, Secret counts
- PVC and PV status

---

## 21. Security Architecture (Defense in Depth)

MiniPaaS implements a layered security approach with multiple gates at
different stages of the DevSecOps pipeline:

```
Layer 1: Code Commit
├── Gitleaks (secret leak detection)
└── Developer awareness (local pre-commit hooks)

Layer 2: Code Analysis
├── Ruff (Python lint)
├── ESLint (TypeScript lint)
└── tsc (TypeScript type checking)

Layer 3: Testing
├── Vitest (frontend unit tests)
└── pytest (Python per-service tests)

Layer 4: Static Analysis
└── SonarCloud (code quality, security hotspots, coverage)

Layer 5: Build Security
├── Hadolint (Dockerfile best practices)
├── Checkov (IaC security scanning)
└── Multi-stage builds (minimal runtime images)

Layer 6: Container Security
├── Trivy (CVE scanning — HIGH/CRITICAL)
├── Dockle (CIS Docker benchmarks)
├── ClamAV (malware detection)
├── YARA (custom rule matching)
├── TruffleHog (secret detection)
└── Policy Engine (configurable block rules)

Layer 7: Supply Chain
├── Exact version pinning (requirements.txt)
├── GHCR with immutable tags (SHA-based)
└── --only-binary :all: (no compilation in production)

Layer 8: Deployment Security
├── Non-root containers (USER nobody/nginx)
├── Kubernetes Secrets (base64 + RBAC)
├── Network policies (ClusterIP only)
└── Healthchecks (liveness + readiness probes)

Layer 9: Runtime Security
├── Prometheus metrics collection
├── Grafana dashboards (real-time visibility)
├── Container restart monitoring
└── Log collection and analysis
```

### Security-Gating Philosophy

- **Fail closed**: Every security check defaults to blocking. If a scan tool
  fails, the image is not pushed. If a policy is violated, the deployment is
  blocked.
- **Defense in depth**: No single layer is trusted. Code passes through
  multiple independent tools (5 scanners, 2 linters, 1 static analyzer).
- **Supply chain integrity**: Exact dependency pinning + SHA-tagged images +
  binary-only pip installs prevent dependency confusion and tampering.
- **Least privilege**: Containers run as non-root (except those requiring
  Docker socket access, which is documented and justified).

---

## 22. Risk Acceptance & Vulnerability Management

### Accepted Risk Categories

Not all vulnerabilities can be fixed immediately. MiniPaaS maintains a
formal risk acceptance process through `.trivyignore`.

**Criteria for acceptance**:

1. **No fix available**: The CVE has no patched version released by the
   upstream maintainer. Tracked for periodic review.

2. **Not in application code**: The CVE is in the base OS image (Debian
   packages, Alpine packages) or in an embedded tool (Trivy binary itself)
   — not in code written by the MiniPaaS team.

3. **Requires upstream upgrade**: The CVE is in a transitive dependency
   (e.g., Starlette via FastAPI) and fixing it requires an upgrade that is
   not yet compatible (e.g., FastAPI >0.116.x for Starlette >=0.49.1).

4. **Low exploitability**: The CVE requires local access or specific
   conditions that do not apply to the deployment context (e.g., CVEs in
   container runtime tools within a CI pipeline that runs ephemerally).

### Vulnerability Tracking Process

```
1. NEW CVE detected by Trivy
   │
   ├─ Is it in our code? → FIX IMMEDIATELY
   │
   ├─ Does a fix exist? → UPGRADE dependency
   │
   └─ No fix available? → ADD TO .trivyignore with reason
                          └─ Set periodic review (monthly)

2. During periodic review:
   ├─ Is fix now available? → Remove from .trivyignore → UPGRADE
   └─ Still no fix? → Keep in .trivyignore, update review date
```

### Security Scanner Docker Image

The Security Scanner container is itself the most security-critical image:

- Contains 5 scanning tools (Trivy, ClamAV, YARA, TruffleHog, Dockle).
- Has access to the Docker daemon.
- Receives untrusted Docker images for analysis.

**Mitigations**:
- Scanner runs as `clamav` user (not root).
- ClamAV daemon runs in non-blocking mode.
- Trivy DB is downloaded in background to not block startup.
- Image extraction uses temporary directories cleaned up after scan.

---

## 23. Complete GitOps Flow

The full GitOps cycle that transforms a code change into running production
infrastructure:

```
                    ┌─────────────────────────────────────┐
                    │     Developer commits to main        │
                    │     git push origin main             │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │     GitHub receives push event       │
                    │     Triggers: .github/workflows/    │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │     CI/CD Pipeline (8 jobs)          │
                    │                                     │
                    │  1. Gitleaks: Scan git history      │
                    │     for secrets                     │
                    │                                     │
                    │  2. Ruff: Lint Python code          │
                    │                                     │
                    │  3. ESLint + tsc: Lint and          │
                    │     type-check frontend             │
                    │                                     │
                    │  4. Tests: Vitest (20) +            │
                    │     pytest (83)                     │
                    │                                     │
                    │  5. SonarCloud: Static analysis     │
                    │     + coverage                      │
                    │                                     │
                    │  6. Hadolint + Checkov: Lint        │
                    │     and security-scan Dockerfiles   │
                    │                                     │
                    │  7. Build all images → Trivy scan   │
                    │     → Dockle scan → Push to GHCR    │
                    │                                     │
                    │  8. Deploy to K3s: Pull images,     │
                    │     apply manifests, restart        │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │     Production K3s Cluster           │
                    │                                     │
                    │  ┌─────────────────────────────┐    │
                    │  │ 10 microservice deployments  │    │
                    │  │ 1 PostgreSQL StatefulSet     │    │
                    │  │ 1 Docker registry            │    │
                    │  │ 1 Traefik Ingress            │    │
                    │  └─────────────────────────────┘    │
                    │                                     │
                    │  ┌─────────────────────────────┐    │
                    │  │ Monitoring Stack            │    │
                    │  │ ├─ Prometheus (7 scrape     │    │
                    │  │ │   jobs, 7d retention)     │    │
                    │  │ ├─ Grafana (2 dashboards,   │    │
                    │  │ │   NodePort 30300)         │    │
                    │  │ ├─ kube-state-metrics       │    │
                    │  │ └─ node-exporter (DaemonSet)│    │
                    │  └─────────────────────────────┘    │
                    │                                     │
                    │  ┌─────────────────────────────┐    │
                    │  │ Port-forward: 8080 → svc/   │    │
                    │  │ frontend (systemd user      │    │
                    │  │ service with Restart=always)│    │
                    │  └─────────────────────────────┘    │
                    └─────────────────────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │     Continuous Feedback Loop         │
                    │                                     │
                    │  ├─ Prometheus scrapes every 15s    │
                    │  ├─ Grafana dashboards refresh       │
                    │  ├─ Container metrics collected      │
                    │  │   every 30s (monitoring-service)  │
                    │  ├─ Logs collected every 30s         │
                    │  ├─ Old data cleaned every 1h        │
                    │  └─ Trivy DB updated on each build   │
                    └─────────────────────────────────────┘
```

### Key Metrics

| Metric | Value |
|--------|-------|
| Services | 9 microservices + 1 frontend |
| Languages | Python 3.11/3.12, TypeScript, Go (tools) |
| Test count | 20 frontend + 83 Python = 103 |
| Docker images | 10 (pushed to GHCR) |
| K8s manifests | 42 YAML files |
| CI/CD jobs | 8 sequential |
| Pipeline time | ~20-30 minutes |
| Security tools | 9 (Gitleaks, Ruff, ESLint, tsc, SonarCloud, Hadolint, Checkov, Trivy, Dockle) |
| Runtime scanners | 5 (Trivy, ClamAV, YARA, TruffleHog, Dockle) |
| Monitoring targets | 7 Prometheus scrape jobs |
| Dashboards | 2 Grafana dashboards |
| Database tables | 6 across PostgreSQL |
| Deployment | K3s on single node (ThinkCentre) |
| API endpoints | ~50 across all services |

---

*MiniPaaS — Built as a DevSecOps demonstration for the report
"DevSecOps for Microservices".*
