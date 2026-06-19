# MiniPaaS — Comprehensive Project Summary

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Service Inventory](#3-service-inventory)
4. [Service Deep Dive](#4-service-deep-dive)
5. [Frontend](#5-frontend)
6. [Infrastructure & Deployment](#6-infrastructure--deployment)
7. [CI/CD Pipeline](#7-cicd-pipeline)
8. [Security & Scanning](#8-security--scanning)
9. [GitHub OAuth Flow](#9-github-oauth-flow)
10. [Kubernetes Manifests](#10-kubernetes-manifests)
11. [Self-Hosted Runner](#11-self-hosted-runner)
12. [Networking & Access](#12-networking--access)
13. [Data Flow](#13-data-flow)
14. [Environment & Configuration](#14-environment--configuration)
15. [Development](#15-development)
16. [File Inventory](#16-file-inventory)
17. [Troubleshooting](#17-troubleshooting)
18. [Appendix](#18-appendix)

---

## 1. Project Overview

### 1.1 What is MiniPaaS?

MiniPaaS (also referred to as Cloudoku) is a lightweight Platform-as-a-Service (PaaS) that allows developers to deploy applications directly from their GitHub repositories. Users connect their GitHub account, select a repository, and MiniPaaS automatically builds a Docker image, runs comprehensive security scans, and deploys the application as a container — all through a web dashboard.

### 1.2 Core Features

- **GitHub OAuth Authentication**: Users log in with their GitHub account
- **Repository Browsing**: Browse and select repositories from connected GitHub account
- **Automated Docker Builds**: Auto-generates Dockerfiles for Python, Node.js, and Java projects
- **Multi-Layer Security Scanning**: Trivy (CVEs), ClamAV (malware), YARA (custom rules), TruffleHog (secrets), Dockle (CIS benchmark)
- **Container Lifecycle Management**: Start, stop, restart, and delete deployments
- **Application Monitoring**: Real-time logs, resource metrics, health status
- **Web Dashboard**: Full-featured React SPA for managing everything

### 1.3 Current Deployment Status

- **Orchestrator**: K3s (lightweight Kubernetes) on single node
- **Container Runtime**: containerd (managed by k3s)
- **Frontend**: React + TypeScript + Vite, served via nginx
- **Backend**: 9 Python FastAPI microservices
- **Database**: PostgreSQL 16 (StatefulSet)
- **Message Broker**: RabbitMQ
- **Registry**: Docker Registry v2 (for user application images)
- **CI/CD**: GitHub Actions + Self-hosted runner
- **Image Storage**: GitHub Container Registry (GHCR)
- **All 13 pods**: Running and healthy

---

## 2. Architecture

### 2.1 High-Level Architecture

```
Internet / Browser
       │
       ▼
┌─────────────────────────────┐
│   localhost:8080 (port-fwd)  │
│   localhost:30080 (NodePort) │
└──────────┬──────────────────┘
           │
           ▼
┌──────────────────────┐
│   frontend (nginx)   │
│   SPA + proxy_pass   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    api-gateway       │
│  port 8000 (int.)   │
└──────┬───────┬───────┘
       │       │
       ▼       ▼
  auth-svc   app-mgmt
  build-svc  deployer-svc
  deploy-svc monitor-svc
  registry   scanner
       │       │
       ▼       ▼
  ┌──────────────┐
  │   postgres   │
  │   rabbitmq   │
  │   registry   │
  └──────────────┘
```

### 2.2 Communication Patterns

**Synchronous (HTTP/REST)**:
- API Gateway receives all external requests
- Gateway proxies to appropriate service based on path prefix
- Services communicate via internal k8s DNS names

**Asynchronous (RabbitMQ)**:
- Build triggers are published to RabbitMQ queues
- Deployment events flow through message broker
- Monitoring data collected asynchronously

### 2.3 Service Dependencies

```
frontend → api-gateway → auth-service (auth/*)
                        → app-management (apps/*)
                        → build-service (builds/*)
                        → deployment-service (deployments/*)
                        → deployer-service (deploy/*)
                        → monitoring-service (monitoring/*)
                        → security-scanner (scanner/*)
                        → registry-service (registry/*)

auth-service → postgres
app-management → postgres, auth-service
build-service → postgres, auth-service, registry, rabbitmq
deployment-service → postgres, auth-service, k8s API
deployer-service → postgres, auth-service, build-service, registry
monitoring-service → postgres, auth-service, Docker socket
security-scanner → auth-service
registry-service → postgres, auth-service, Docker registry
```

---

## 3. Service Inventory

### 3.1 Services Table

| # | Service | Internal Port | Language | DB | Stateful | Description |
|---|---------|--------------|----------|----|----------|-------------|
| 1 | **frontend** | 8080 | TS/React | No | No | Web dashboard served by nginx |
| 2 | **api-gateway** | 8000 | Python/FastAPI | No | No | Entry point, routing, auth middleware |
| 3 | **auth-service** | 8000 | Python/FastAPI | Yes | No | Auth, JWT, GitHub OAuth |
| 4 | **app-management** | 8000 | Python/FastAPI | Yes | No | App CRUD operations |
| 5 | **build-service** | 8002 | Python/FastAPI | Yes | No | Docker build orchestration |
| 6 | **deployment-service** | 8000 | Python/FastAPI | No | No | K8s deployment management |
| 7 | **deployer-service** | 8000 | Python/FastAPI | Yes | No | End-to-end deployment flow |
| 8 | **monitoring-service** | 8006 | Python/FastAPI | Yes | No | Logs, metrics, health |
| 9 | **registry-service** | 8005 | Python/FastAPI | Yes | No | Image metadata |
| 10 | **security-scanner** | 8000 | Python/FastAPI | No | No | Multi-layer security scanning |
| 11 | **postgres** | 5432 | PostgreSQL | Yes | Yes | Primary database |
| 12 | **rabbitmq** | 5672 | RabbitMQ | No | No | Message broker |
| 13 | **registry** | 5000 | Docker Registry | No | No | Container image storage |

### 3.2 Pod Status (Healthy)

All 13 pods in the `minipaas` namespace are in `Running` state with `1/1` ready containers.

---

## 4. Service Deep Dive

### 4.1 Frontend

| Attribute | Value |
|-----------|-------|
| **Location** | `frontend/` |
| **Framework** | React 18.3.x |
| **Language** | TypeScript 5.x |
| **Build Tool** | Vite 6.x |
| **Styling** | TailwindCSS 3.x |
| **Routing** | React Router DOM 7.x |
| **Charts** | Recharts 3.x |
| **Animations** | Framer Motion 12.x |
| **Server** | nginx (serves built SPA + reverse proxy) |
| **Port (internal)** | 8080 |
| **Port (external)** | 30080 (NodePort) / 8080 (port-forward) |

**Key Files**:
- `frontend/src/App.tsx` — Main app with routes
- `frontend/src/pages/Login.tsx` — Login page with GitHub OAuth
- `frontend/src/pages/Dashboard.tsx` — User dashboard
- `frontend/src/pages/NewDeployment.tsx` — Create deployment
- `frontend/src/pages/GitHubCallback.tsx` — OAuth callback handler
- `frontend/src/context/AuthContext.tsx` — Auth state management
- `frontend/src/lib/api.ts` — API client

**Key Routes (React Router)**:
| Path | Component | Description |
|------|-----------|-------------|
| `/` | Home | Landing page |
| `/login` | Login | Login/register with GitHub OAuth |
| `/register` | Register | Email registration |
| `/oauth/github/callback` | GitHubCallback | GitHub OAuth callback handler |
| `/dashboard` | Dashboard | Main user dashboard (protected) |
| `/repositories` | Repositories | Browse GitHub repos (protected) |
| `/deployments` | Deployments | Manage deployments (protected) |
| `/new-deployment` | NewDeployment | Create deployment (protected) |
| `/monitoring` | Monitoring | App metrics & logs (protected) |

### 4.2 API Gateway

| Attribute | Value |
|-----------|-------|
| **Location** | `services/api-gateway/` |
| **Framework** | FastAPI (Python) |
| **Port (internal)** | 8000 |
| **Role** | Central entry point |

**Middleware**:
- `src/middleware/auth.py` — JWT verification for protected routes
- Public routes (no auth): `/auth/register`, `/auth/login`, `/auth/github`, `/auth/callback`

**Proxy Routes**:
| Prefix | Upstream Service |
|--------|-----------------|
| `/auth/*` | auth-service |
| `/apps/*` | app-management |
| `/builds/*` | build-service |
| `/deployments/*` | deployment-service |
| `/deploy/*` | deployer-service |
| `/monitoring/*` | monitoring-service |
| `/scanner/*` | security-scanner |
| `/registry/*` | registry-service |

### 4.3 Auth Service

| Attribute | Value |
|-----------|-------|
| **Location** | `services/auth-service/` |
| **Framework** | FastAPI (Python) |
| **Port (internal)** | 8000 |
| **Database** | PostgreSQL (via SQLAlchemy + Alembic) |

**Models**:
- `User` — id, email, name, password_hash, oauth_provider, oauth_id, github_access_token, created_at, updated_at

**Routes**:
| Method | Path | Description |
|--------|------|-------------|
| POST | `/register` | Email/password registration |
| POST | `/login` | Email/password login |
| POST | `/refresh` | Refresh JWT token |
| GET | `/github` | Get GitHub OAuth URL |
| GET | `/callback` | GitHub OAuth callback (exchange code for token) |
| GET | `/me` | Get current user profile |
| GET | `/github-token` | Get user's GitHub access token |

**Configuration** (`src/config.py`):
| Variable | Default | Source |
|----------|---------|--------|
| `DATABASE_URL` | postgresql://minipaas:minipaas@postgres:5432/minipaas | k8s secret |
| `JWT_SECRET_KEY` | change-me-in-production | k8s secret |
| `JWT_ALGORITHM` | HS256 | k8s configmap |
| `JWT_ACCESS_TOKEN_EXPIRATION_MINUTES` | 15 | k8s configmap |
| `REFRESH_TOKEN_SECRET` | change-me-in-production-refresh | k8s secret |
| `GITHUB_CLIENT_ID` | "" | k8s secret (injected from GitHub Actions secrets) |
| `GITHUB_CLIENT_SECRET` | "" | k8s secret (injected from GitHub Actions secrets) |
| `GITHUB_REDIRECT_URI` | http://localhost:8080/oauth/github/callback | k8s secret |

### 4.4 Build Service

| Attribute | Value |
|-----------|-------|
| **Location** | `services/build-service/` |
| **Framework** | FastAPI (Python) |
| **Port (internal)** | 8002 |
| **Database** | PostgreSQL |

**Services**:
- `docker_service.py` — Docker build orchestration
- `git_service.py` — Git clone and repo management
- `auth_client.py` — Auth service HTTP client
- `registry_client.py` — Registry service HTTP client
- `scanner_client.py` — Security scanner HTTP client

### 4.5 Security Scanner

| Attribute | Value |
|-----------|-------|
| **Location** | `services/security-scanner/` |
| **Framework** | FastAPI (Python) |
| **Port (internal)** | 8000 |

**Scanners Implemented**:
| Scanner | Tool | Purpose | Blocking |
|---------|------|---------|----------|
| TrivyScanner | Trivy | OS/pkg CVE detection | CRITICAL/HIGH |
| ClamavScanner | ClamAV | Malware detection | Warning |
| YaraScanner | YARA | Custom threat patterns | Warning |
| TrufflehogScanner | TruffleHog | Secret/key detection | Warning |
| DockleScanner | Dockle | Docker CIS benchmark | Warning |
| BaseImageChecker | — | Approved base images | Warning |

**YARA Rule Categories**:
- `crypto_miners.yara` — XMRig signatures, mining pools
- `webshells.yara` — eval(base64), system() abuse, backdoor shells
- `container_escape.yara` — Host fs access, cgroup escape, docker socket
- `reverse_shells.yara` — /dev/tcp, bash reverse shells, nc -e
- `rootkits.yara` — Cron anomalies, systemd injection, SSH abuse
- `general_malware.yara` — Known backdoor binaries, suspicious ELF

**Policy Engine** (`services/policy_engine.py`):
- Blocks deployment if CRITICAL/HIGH CVEs exceed thresholds (>50 critical or >500 high)
- Blocks on malware detection, secret leaks, root user
- Configurable via env vars: `BLOCK_ON_HIGH_CVES`, `BLOCK_ON_MALWARE`, etc.

### 4.6 Registry Service

| Attribute | Value |
|-----------|-------|
| **Location** | `services/registry-service/` |
| **Framework** | FastAPI (Python) |
| **Port (internal)** | 8005 |
| **Database** | PostgreSQL |

### 4.7 Deployer Service

| Attribute | Value |
|-----------|-------|
| **Location** | `services/deployer-service/` |
| **Framework** | FastAPI (Python) |
| **Port (internal)** | 8000 |
| **Database** | PostgreSQL |

### 4.8 Deployment Service

| Attribute | Value |
|-----------|-------|
| **Location** | `services/deployment-service/` |
| **Framework** | FastAPI (Python) |
| **Port (internal)** | 8000 |

**K8s Client** (`src/k8s/client.py`):
- Manages Kubernetes deployments for user apps
- Creates/deletes Namespaces, Deployments, Services
- Port allocation and NodePort management

### 4.9 App Management

| Attribute | Value |
|-----------|-------|
| **Location** | `services/app-management/` |
| **Framework** | FastAPI (Python) |
| **Port (internal)** | 8000 |
| **Database** | PostgreSQL |

### 4.10 Monitoring Service

| Attribute | Value |
|-----------|-------|
| **Location** | `services/monitoring-service/` |
| **Framework** | FastAPI (Python) |
| **Port (internal)** | 8006 |
| **Database** | PostgreSQL |
| **Add-ons** | Grafana dashboards, Prometheus config |

---

## 5. Frontend

### 5.1 Tech Stack

- **React 18.3** with TypeScript 5
- **Vite 6** for build tooling
- **TailwindCSS 3** for styling
- **React Router DOM 7** for routing
- **Recharts 3** for charts and graphs
- **Framer Motion 12** for animations
- **Axios** for HTTP client

### 5.2 Pages

| Page | Route | Description |
|------|-------|-------------|
| Home | `/` | Landing page with lightning animation |
| Login | `/login` | GitHub OAuth login + email/password |
| Register | `/register` | Email/password registration |
| Dashboard | `/dashboard` | Overview of apps, stats, quick actions |
| Repositories | `/repositories` | Browse connected GitHub repos |
| Deployments | `/deployments` | List/manage deployments |
| New Deployment | `/new-deployment` | Create new deployment (select repo, configure) |
| Monitoring | `/monitoring` | App metrics, logs, health status |
| GitHub Callback | `/oauth/github/callback` | OAuth code → token exchange handler |

### 5.3 Nginx Configuration

The frontend nginx serves static files and proxies API requests:

```
location /auth/     → proxy_pass http://api-gateway:8000/auth/
location /apps/     → proxy_pass http://api-gateway:8000/apps/
location /builds/   → proxy_pass http://api-gateway:8000/builds/
location /deployments/ → proxy_pass http://api-gateway:8000/deployments/
location /deploy/   → proxy_pass http://api-gateway:8000/deploy/
location /monitoring/ → proxy_pass http://api-gateway:8000/monitoring/
location /scanner/  → proxy_pass http://api-gateway:8000/scanner/
location /registry/ → proxy_pass http://api-gateway:8000/registry/
location = /health  → proxy_pass http://api-gateway:8000/health
location /          → try_files $uri $uri/ /index.html (SPA fallback)
```

All other paths serve the SPA (`index.html`) for client-side routing.

---

## 6. Infrastructure & Deployment

### 6.1 Current Setup

| Component | Details |
|-----------|---------|
| **Node** | 1 node (hostname: `anonymous`) |
| **Kubernetes** | K3s v2.2.3-k3s1 |
| **Container Runtime** | containerd (via k3s built-in) |
| **CRI Socket** | `/run/k3s/containerd/containerd.sock` |
| **Namespace** | `minipaas` |
| **Network** | Flannel (k3s default) |
| **Service CIDR** | 10.43.0.0/16 |
| **Pod CIDR** | 10.42.0.0/16 |
| **OS** | Linux (Ubuntu/Debian based) |
| **User** | carbon14 |

### 6.2 Image Management

**Service Images**:
- Stored on GitHub Container Registry: `ghcr.io/carbon14-48/minipaas-{service}:latest`
- Pulled directly into k3s containerd via `ctr images pull` (bypasses Docker)
- No Docker dependency for k3s image management

**User Application Images**:
- Built by `build-service` on the node
- Pushed to local `registry:5000` (Docker Registry v2 running in k3s)
- Deployed as containers by `deployment-service`

### 6.3 Import Flow (CI/CD)

```
GitHub Actions builds images → pushes to GHCR
         │
         ▼
Self-hosted runner runs deploy-from-ghcr.sh
         │
         ├─ ctr images pull ghcr.io/.../minipaas-{service}:latest
         ├─ kubectl apply -f k8s/namespace.yaml
         ├─ kubectl apply -f k8s/*.yaml + k8s/*/
         ├─ kubectl patch secret (inject GITHUB_CLIENT_ID/SECRET)
         ├─ kubectl rollout restart all deployments
         └─ setsid kubectl port-forward svc/frontend 8080:8080
```

### 6.4 Previous (Deprecated) Import Method

Previously used `docker pull` → `docker save` → `k3s ctr images import`, but this was broken because:
- Docker 29.3.1 uses containerd snapshotter (`io.containerd.snapshotter.v1`)
- `docker save` produces broken tars (layers not included)
- `ctr import` fails with "content digest not found"

The fix: use `ctr images pull` directly from GHCR — works reliably.

---

## 7. CI/CD Pipeline

### 7.1 Workflow File

`.github/workflows/lint.yml` — Single unified workflow with sequential jobs:

```
push to main / PR to main
         │
    ┌────▼────┐
    │ gitleaks│  ← Secret leak detection
    └────┬────┘
         │
    ┌────▼────┐
    │  ruff   │  ← Python linting (services/)
    └────┬────┘
         │
    ┌────▼────┐
    │eslint+tsc│  ← TypeScript quality (frontend/)
    └────┬────┘
         │
    ┌────▼──────┐
    │sonarcloud │  ← Code quality + coverage
    └────┬──────┘
         │
    ┌────▼──────┐
    │docker lint│  ← Hadolint + Checkov
    └────┬──────┘
         │
    ┌────▼───────────┐
    │build-scan-push │  ← docker compose build
    │                │     Trivy scan (HIGH/CRITICAL)
    │                │     Dockle scan
    │                │     Push to GHCR (on push only)
    └────┬───────────┘
         │ (only push to main)
    ┌────▼────┐
    │  deploy │  ← Self-hosted runner
    │  to k3s │     ./deploy-from-ghcr.sh
    └─────────┘
```

### 7.2 Job Details

**gitleaks**:
- Runs: always
- Tool: gitleaks/gitleaks-action@v2
- Purpose: Detect secrets in commit history

**ruff**:
- Runs: after gitleaks
- Tool: astral-sh/ruff-action@v1
- Scope: `services/`

**eslint + tsc**:
- Runs: after ruff
- Working directory: `frontend/`
- Commands: `npx eslint src/ --max-warnings=0`, `npx tsc --noEmit`

**sonarcloud**:
- Runs: after ts
- Requires: `SONAR_TOKEN` secret, test coverage
- Runs both Python and frontend test suites for coverage data

**docker lint**:
- Runs: after sonarcloud
- Tools: Hadolint (Dockerfile lint), Checkov (IaC scan)
- Scans all `services/*/Dockerfile` and `frontend/Dockerfile`

**build-scan-push**:
- Runs: after docker lint
- Steps:
  1. `docker compose build` — builds all service images
  2. Trivy scan — scans each image for HIGH/CRITICAL CVEs, exits 1 if found
  3. Dockle scan — CIS benchmark checks
  4. Login to GHCR (only on push events)
  5. Push images to GHCR with `:latest` and `:${{ github.sha }}` tags

**deploy**:
- Runs: after build-scan-push, only on `push` to `main`
- Runs-on: `self-hosted` (the local runner)
- Env vars:
  - `GHCR_TOKEN` → `${{ secrets.GITHUB_TOKEN }}`
  - `GITHUB_CLIENT_ID` → `${{ secrets.GH_GITHUB_CLIENT_ID }}`
  - `GITHUB_CLIENT_SECRET` → `${{ secrets.GH_GITHUB_CLIENT_SECRET }}`
- Steps:
  1. Checkout code
  2. Run `./deploy-from-ghcr.sh`

### 7.3 Workflow Permissions

```yaml
permissions:
  contents: read
  packages: write    # Required for pushing to GHCR
```

### 7.4 GitHub Secrets Required

| Secret Name | Purpose |
|-------------|---------|
| `SONAR_TOKEN` | SonarCloud authentication |
| `GH_GITHUB_CLIENT_ID` | GitHub OAuth App client ID |
| `GH_GITHUB_CLIENT_SECRET` | GitHub OAuth App client secret |

The `GITHUB_TOKEN` (auto-injected) is used for GHCR push authentication.

---

## 8. Security & Scanning

### 8.1 CI Pipeline Security

| Stage | Tool | What It Checks |
|-------|------|---------------|
| Commit | Gitleaks | Hardcoded secrets, API keys, tokens |
| Code | Ruff | Python linting, security issues |
| Code | ESLint | TypeScript/React best practices |
| Code | SonarCloud | Code quality, security hotspots, coverage |
| Dockerfile | Hadolint | Dockerfile best practices |
| IaC | Checkov | Kubernetes/Docker misconfigurations |
| Image | Trivy | OS packages + dependency CVEs |
| Image | Dockle | CIS Docker benchmark compliance |
| Runtime | Security Scanner | Trivy, ClamAV, YARA, TruffleHog, Dockle |

### 8.2 Runtime Security Scanner

The `security-scanner` service performs multi-layer scanning:

**Workflow**:
```
Image received → Image Loader → Parallel Scanners → Result Aggregator → Policy Engine → Pass/Fail
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
                TrivyScanner   ClamavScanner    YaraScanner
                TrufflehogScanner  DockleScanner  BaseImageChecker
                                    │
                                    ▼
                              ResultAggregator
                                    │
                                    ▼
                              PolicyEngine
                                    │
                            ┌───────┴───────┐
                            ▼               ▼
                          PASS             FAIL
```

**Policy Rules** (`services/security-scanner/src/services/policy_engine.py`):
```python
# Blocking conditions (image rejected):
- critical_cves > 50
- high_cves > 500
- malware_found == True (if BLOCK_ON_MALWARE)
- secrets_found == True (if BLOCK_ON_SECRETS)
- root_user == True (if BLOCK_ON_ROOT_USER)
```

### 8.3 Base Image Allowlist

**Allowed Python**:
- python:3.8-slim through 3.13-slim
- python:3.8-alpine through 3.13-alpine

**Allowed Node.js**:
- node:16-alpine through 22-alpine
- node:16-slim through 22-slim

**Allowed Golang**:
- golang:1.20-alpine through 1.23-alpine

**Allowed Java**:
- eclipse-temurin:8-jre-alpine through 21-jre-alpine

**Distroless**:
- gcr.io/distroless/python3-debian11/12
- gcr.io/distroless/nodejs18/20-debian11

**Blocked**:
- scratch (no package manager)
- ubuntu:latest, debian:latest, centos:*, rockylinux:*, fedora:*
- busybox:*, amazoncorretto:*, openjdk:*
- Any image with `latest` tag (except approved)

---

## 9. GitHub OAuth Flow

### 9.1 Complete Authentication Flow

```
User clicks "Login with GitHub"
         │
         ▼
Frontend calls GET /auth/github
         │
         ▼
Auth-service returns:
  https://github.com/login/oauth/authorize?
    client_id=xxx&
    redirect_uri=http://localhost:8080/oauth/github/callback&
    scope=user:email
         │
         ▼
Browser redirects to GitHub
         │
         ▼
User authorizes the application
         │
         ▼
GitHub redirects to:
  http://localhost:8080/oauth/github/callback?code=xxx
         │
         ▼
nginx serves index.html (SPA fallback for /oauth/*)
         │
         ▼
React Router renders GitHubCallback component
         │
         ▼
GitHubCallback reads `code` from URL query params
         │
         ▼
Frontend calls GET /auth/callback?code=xxx
(proxied by nginx → api-gateway → auth-service)
         │
         ▼
Auth-service exchanges code with GitHub:
  POST https://github.com/login/oauth/access_token
  { client_id, client_secret, code, redirect_uri }
         │
         ▼
Auth-service gets user info:
  GET https://api.github.com/user
  GET https://api.github.com/user/emails
         │
         ▼
Auth-service creates/updates user in database
         │
         ▼
Auth-service returns JWT tokens:
  { access_token, refresh_token, token_type: "bearer" }
         │
         ▼
Frontend stores tokens in localStorage
Frontend calls GET /auth/me for user profile
User is logged in → navigated to /dashboard
```

### 9.2 Token Details

- **Access Token**: JWT (HS256), 15 min expiry
  - Payload: `{ sub: user_id, exp: ..., iat: ... }`
- **Refresh Token**: JWT (HS256), 7 days expiry
  - Payload: `{ sub: user_id, exp: ..., iat: ... }`
- **Storage**: localStorage (`access_token`, `refresh_token`)

### 9.3 GitHub OAuth App Configuration

- **Application URL**: http://localhost:8080
- **Callback URL**: http://localhost:8080/oauth/github/callback
- **Client ID**: Ov23liM7bZfzXolwuhcf
- **Client Secret**: (stored in GitHub Actions secrets, injected at deploy time)

---

## 10. Kubernetes Manifests

### 10.1 Directory Structure

```
k8s/
├── namespace.yaml          # minipaas namespace
├── configmap.yaml          # Shared configuration (service URLs, thresholds)
├── secret.yaml             # Secrets (placeholders, real values injected at deploy)
├── ingress.yaml            # Ingress rules
├── auth-service/           # Auth service deployment + service
├── app-management/         # App management deployment + service
├── build-service/          # Build service deployment + service
├── deployment-service/     # Deployment service deployment + service
├── deployer-service/       # Deployer service deployment + service
├── monitoring-service/     # Monitoring service deployment + service
├── registry-service/       # Registry service deployment + service
├── security-scanner/       # Security scanner deployment + service
├── api-gateway/            # API gateway deployment + service
├── frontend/               # Frontend deployment + service + nginx configmap
├── postgres/               # PostgreSQL StatefulSet + service
├── rabbitmq/               # RabbitMQ deployment + service
└── registry/               # Docker registry deployment + service + PVC
```

### 10.2 Namespace (`namespace.yaml`)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: minipaas
```

Applied FIRST in the deploy script to avoid race conditions.

### 10.3 ConfigMap (`configmap.yaml`)

Contains 50+ configuration values including:
- Service URLs (`AUTH_SERVICE_URL`, `BUILD_SERVICE_URL`, etc.)
- Security thresholds (`BLOCK_ON_HIGH_CVES`, `BLOCK_ON_MALWARE`, etc.)
- Build settings (`MAX_BUILD_TIMEOUT`, `BUILD_WORKDIR`)
- JWT configuration (`JWT_ALGORITHM`, `JWT_EXPIRATION_MINUTES`)
- Registry settings (`REGISTRY_URL`, `REGISTRY_HOST`)
- Logging (`LOG_LEVEL`, `DEBUG`)

### 10.4 Secret (`secret.yaml`)

Contains sensitive values (with placeholders in git):
- `DATABASE_URL` — PostgreSQL connection string
- `JWT_SECRET_KEY` — JWT signing key
- `REFRESH_TOKEN_SECRET` — Refresh token signing key
- `GITHUB_REDIRECT_URI` — OAuth callback URL
- `GITHUB_CLIENT_ID` — Injected from GitHub Actions secret
- `GITHUB_CLIENT_SECRET` — Injected from GitHub Actions secret
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `RABBITMQ_URL`

### 10.5 Frontend Service (NodePort)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: minipaas
spec:
  type: NodePort
  ports:
  - port: 8080
    targetPort: 8080
    nodePort: 30080
  selector:
    app: frontend
```

### 10.6 Image Pull Policy

All deployments use `imagePullPolicy: Always` to ensure fresh images after each deploy.

### 10.7 Resource Limits

Each service has defined resource requests and limits:
- **Requests**: 256Mi memory, 250m CPU
- **Limits**: 512Mi memory, 500m CPU

---

## 11. Self-Hosted Runner

### 11.1 Setup Details

- **Location**: `/home/carbon14/actions-runner/`
- **Version**: 2.335.1
- **Name**: k3s-runner
- **Labels**: self-hosted, k3s
- **Status**: Running (PID in `run.sh` + `Runner.Listener`)
- **Repository**: Carbon14-48/MiniPaaS
- **Work Directory**: `/home/carbon14/actions-runner/_work/MiniPaaS/`

### 11.2 How It Was Set Up

```bash
# Download
curl -o actions-runner-linux-x64-2.335.1.tar.gz -L https://github.com/actions/runner/releases/download/v2.335.1/actions-runner-linux-x64-2.335.1.tar.gz

# Extract
tar xzf actions-runner-linux-x64-2.335.1.tar.gz

# Configure
./config.sh --url https://github.com/Carbon14-48/MiniPaaS --token <REGISTRATION_TOKEN> --name "k3s-runner" --labels "self-hosted,k3s" --unattended

# Run (background daemon)
setsid ./run.sh &> runner.log &
```

### 11.3 Startup

The runner is started manually via:
```bash
setsid ~/actions-runner/run.sh &> ~/actions-runner/runner.log &
```

Note: `sudo ./svc.sh install` could not be used (no sudo password), so the runner is started as a user process. It will NOT auto-start on reboot — must be restarted manually.

### 11.4 Logs

- **Runner log**: `~/actions-runner/runner.log`
  - Shows job pickup and completion status
- **Diagnostic logs**: `~/actions-runner/_diag/`
  - `Worker_*.log` — Detailed step execution logs
  - `Runner_*.log` — Runner service logs

### 11.5 Runner Capabilities

The runner has access to:
- `kubectl` (k3s built-in)
- `k3s ctr` for image management
- Docker (for compatibility, but not used for k3s image import anymore)
- Git
- All project files via checkout

---

## 12. Networking & Access

### 12.1 Access Points

| URL | Type | Target | Status |
|-----|------|--------|--------|
| http://localhost:8080 | Port-forward | frontend:8080 | Active — auto-restored after each deploy |
| http://localhost:30080 | NodePort | frontend:8080 | Always available (k8s native) |

### 12.2 Port-forward Persistence

The deploy script sets up port-forward at the end:
```bash
kill $(lsof -t -i :8080 -sTCP:LISTEN 2>/dev/null) 2>/dev/null || true
setsid kubectl port-forward -n minipaas svc/frontend 8080:8080 &>/dev/null &
```

The `setsid` ensures the port-forward survives the CI job completion.

### 12.3 Internal Networking

| Service | Internal DNS | Port |
|---------|-------------|------|
| frontend | frontend.minipaas.svc.cluster.local | 8080 |
| api-gateway | api-gateway.minipaas.svc.cluster.local | 8000 |
| auth-service | auth-service.minipaas.svc.cluster.local | 8000 |
| postgres | postgres.minipaas.svc.cluster.local | 5432 |
| rabbitmq | rabbitmq.minipaas.svc.cluster.local | 5672 |
| registry | registry.minipaas.svc.cluster.local | 5000 |

---

## 13. Data Flow

### 13.1 User Creates an Application

```
1. Frontend: User fills form (repo URL, name, env vars)
2. POST /deploy/apps → api-gateway → app-management
3. app-management saves app to postgres
4. Returns app ID to frontend
5. Frontend redirects to deployment page
```

### 13.2 Build Pipeline

```
1. RabbitMQ message: "build app X"
2. build-service picks up message
3. git_service clones repo to BUILD_WORKDIR
4. docker_service generates Dockerfile (if missing)
5. docker_service builds image → tags → pushes to registry:5000
6. scanner_client sends image to security-scanner
7. security-scanner runs: Trivy → ClamAV → YARA → TruffleHog → Dockle
8. policy_engine evaluates results
   ┌─ PASS → deployment-service deploys the app
   └─ FAIL → error returned, deployment blocked
```

### 13.3 Deployment Flow

```
1. deployment-service creates k8s Deployment + Service
2. Uses NodePort for external access
3. Port range: 30000-40000
4. Monitors pod readiness
5. Returns access URL to user
```

### 13.4 Monitoring Flow

```
1. monitoring-service polls Docker daemon every COLLECT_INTERVAL_SECONDS (30s)
2. Collects: CPU, memory, network I/O per container
3. Stores in postgres
4. RETENTION: METRICS_RETENTION_DAYS (7 days)
5. Frontend queries via GET /monitoring/metrics and /monitoring/logs
```

---

## 14. Environment & Configuration

### 14.1 Env Var Sources

All services load configuration from:
1. `minipaas-config` ConfigMap (non-sensitive)
2. `minipaas-secret` Secret (sensitive)
3. Each service has defaults in its `config.py`

### 14.2 ConfigMap Contents

| Key | Value | Used By |
|-----|-------|---------|
| AUTH_SERVICE_URL | http://auth-service:8000 | All services |
| APP_MANAGEMENT_SERVICE_URL | http://app-management:8000 | API gateway |
| BUILD_SERVICE_URL | http://build-service:8002 | API gateway |
| DEPLOYMENT_SERVICE_URL | http://deployment-service:8000 | API gateway |
| MONITORING_SERVICE_URL | http://monitoring-service:8006 | API gateway |
| SECURITY_SCANNER_URL | http://security-scanner:8000 | API gateway |
| DEPLOYER_SERVICE_URL | http://deployer-service:8000 | API gateway |
| REGISTRY_SERVICE_URL | http://registry-service:8005 | API gateway |
| SCANNER_SERVICE_URL | http://security-scanner:8000 | Build service |
| LOG_LEVEL | INFO | All services |
| ENV | development | All services |
| ALLOWED_ORIGINS | ["*"] | All services |
| DOCKER_REGISTRY_URL | localhost:5000 | Build service |
| REGISTRY_HOST | localhost:5000 | Build service |
| REGISTRY_URL | http://registry:5000 | Registry service |
| HOST_PORT_RANGE_START | 30000 | Deployment service |
| HOST_PORT_RANGE_END | 40000 | Deployment service |
| JWT_ALGORITHM | HS256 | Auth service |
| JWT_EXPIRATION_MINUTES | 60 | Auth service |
| REFRESH_TOKEN_ALGORITHM | HS256 | Auth service |
| REFRESH_TOKEN_EXPIRATION_DAYS | 7 | Auth service |
| JWT_ACCESS_TOKEN_EXPIRATION_MINUTES | 15 | Auth service |
| DEBUG | true | All services |
| BUILD_WORKDIR | /tmp/builds | Build service |
| MAX_BUILD_TIMEOUT | 600 | Build service |
| DOCKER_SOCKET_PATH | /var/run/docker.sock | Build service |
| TRIVY_PATH | /usr/bin/trivy | Security scanner |
| YARA_RULES_DIR | /rules | Security scanner |
| CLAMAV_DB_PATH | /var/lib/clamav | Security scanner |
| SCANNER_MAX_TIMEOUT | 600 | Security scanner |
| BLOCK_ON_HIGH_CVES | True | Security scanner |
| BLOCK_ON_MALWARE | True | Security scanner |
| BLOCK_ON_SECRETS | True | Security scanner |
| BLOCK_ON_ROOT_USER | True | Security scanner |
| COLLECT_INTERVAL_SECONDS | 30 | Monitoring service |
| METRICS_RETENTION_DAYS | 7 | Monitoring service |
| LOG_TAIL_LINES | 100 | Monitoring service |
| KUBECONFIG_PATH | /root/.kube/config | Deployment service |
| CLOUDOKU_DOMAIN | cloudoku.app | Deployment service |
| GITHUB_API_URL | https://api.github.com | All services |

### 14.3 Secret Contents

| Key | Value (placeholder) | Notes |
|-----|--------------------|-------|
| DATABASE_URL | postgresql://minipaas:minipaas@postgres:5432/minipaas | Actual value in git |
| JWT_SECRET_KEY | change-me-in-production | Should be changed for production |
| REFRESH_TOKEN_SECRET | change-me-in-production-refresh | Should be changed for production |
| GITHUB_REDIRECT_URI | http://localhost:8080/oauth/github/callback | Actual value in git |
| GITHUB_CLIENT_ID | "" | Injected from GitHub Actions secret |
| GITHUB_CLIENT_SECRET | "" | Injected from GitHub Actions secret |
| POSTGRES_USER | minipaas | Actual value in git |
| POSTGRES_PASSWORD | minipaas | Actual value in git |
| POSTGRES_DB | minipaas | Actual value in git |
| RABBITMQ_URL | amqp://guest:guest@rabbitmq:5672/ | Actual value in git |

---

## 15. Development

### 15.1 Local Development (outdated — project now runs on k3s)

The docker-compose approach is deprecated. All services now run on k3s. For local changes:
1. Make code changes
2. Commit and push to main
3. CI builds, scans, and deploys automatically

### 15.2 Direct K8s Updates (for testing)

```bash
# Rebuild and import a single image
docker compose build <service>
k3s ctr -a /run/k3s/containerd/containerd.sock -n k8s.io images pull ...  # or
ctr images pull ghcr.io/.../minipaas-<service>:latest

# Restart a deployment
kubectl rollout restart -n minipaas deployment/<service>

# Watch logs
kubectl logs -n minipaas deployment/<service> -f

# Exec into a pod
kubectl exec -n minipaas deployment/<service> -- <command>
```

### 15.3 Useful Commands

```bash
# Check all pods
kubectl get pods -n minipaas -o wide

# Check all services
kubectl get svc -n minipaas

# Check logs of crashing pod
kubectl logs -n minipaas deployment/<service> --tail=50

# Describe a pod (for error details)
kubectl describe pod -n minipaas <pod-name>

# Restart all services
kubectl rollout restart -n minipaas deployment --all

# Check images in containerd
k3s ctr -a /run/k3s/containerd/containerd.sock -n k8s.io images ls | grep minipaas

# Get secret values
kubectl get secret -n minipaas minipaas-secret -o json | python3 -c "import sys,json,base64; s=json.load(sys.stdin); [print(f'{k}: {base64.b64decode(v).decode()}') for k,v in s.get('data',{}).items()]"
```

---

## 16. File Inventory

### 16.1 Root

| File | Description |
|------|-------------|
| `README.md` | Main project documentation |
| `Makefile` | Build automation targets |
| `docker-compose.yml` | Deprecated local dev setup |
| `.gitignore` | Git ignore patterns |
| `.trivyignore` | Trivy CVE ignore list |
| `.env` | Local environment (gitignored) |
| `.env.example` | Environment template |
| `deploy-from-ghcr.sh` | CI/CD deploy script |
| `summary.md` | This file |

### 16.2 GitHub Actions

| File | Description |
|------|-------------|
| `.github/workflows/lint.yml` | Main CI/CD pipeline |

### 16.3 Kubernetes Manifests

| File | Type |
|------|------|
| `k8s/namespace.yaml` | Namespace |
| `k8s/configmap.yaml` | ConfigMap |
| `k8s/secret.yaml` | Secret |
| `k8s/ingress.yaml` | Ingress |
| `k8s/auth-service/deployment.yaml` | Auth service |
| `k8s/app-management/deployment.yaml` | App management |
| `k8s/build-service/deployment.yaml` | Build service |
| `k8s/deployment-service/deployment.yaml` | Deployment service |
| `k8s/deployer-service/deployment.yaml` | Deployer service |
| `k8s/monitoring-service/deployment.yaml` | Monitoring |
| `k8s/registry-service/deployment.yaml` | Registry service |
| `k8s/security-scanner/deployment.yaml` | Security scanner |
| `k8s/api-gateway/deployment.yaml` + `service.yaml` | API gateway |
| `k8s/frontend/deployment.yaml` + `service.yaml` | Frontend |
| `k8s/frontend/nginx-configmap.yaml` | Frontend nginx config |
| `k8s/postgres/statefulset.yaml` + `service.yaml` | PostgreSQL |
| `k8s/rabbitmq/deployment.yaml` + `service.yaml` | RabbitMQ |
| `k8s/registry/deployment.yaml` + `service.yaml` + `pvc.yaml` | Docker registry |

### 16.4 Services

| Service | Key Source Files |
|---------|-----------------|
| api-gateway | `main.py`, `config.py`, `routes/proxy.py`, `routes/health.py`, `middleware/auth.py` |
| auth-service | `main.py`, `config.py`, `database.py`, `models/user.py`, `routes/auth.py`, `routes/health.py`, `services/auth_service.py` |
| app-management | `main.py`, `config.py`, `models/app.py`, `routes/apps.py`, `services/app_service.py` |
| build-service | `main.py`, `config.py`, `db.py`, `models/job.py`, `routes/build.py`, `services/docker_service.py`, `services/git_service.py`, `services/auth_client.py`, `services/registry_client.py`, `services/scanner_client.py` |
| deployment-service | `main.py`, `config.py`, `k8s/client.py`, `routes/deployments.py` |
| deployer-service | `main.py`, `config.py`, `db.py`, `models/deployment.py`, `routes/deployments.py`, `routes/github.py`, `services/auth_client.py`, `services/build_client.py`, `services/docker_runner.py`, `services/github_client.py`, `services/registry_client.py` |
| monitoring-service | `main.py`, `config.py`, `db.py`, `models/log_entry.py`, `models/metric.py`, `routes/logs.py`, `routes/metrics.py`, `services/docker_collector.py`, `services/log_collector.py`, `services/scheduler.py`, `Grafana dashboards`, `Prometheus config` |
| registry-service | `main.py`, `config.py`, `db.py`, `models/image.py`, `routes/registry.py`, `services/docker_registry.py` |
| security-scanner | `main.py`, `config.py`, `routes/scans.py`, `scanners/trivy_scanner.py`, `scanners/clamav_scanner.py`, `scanners/yara_scanner.py`, `scanners/trufflehog_scanner.py`, `scanners/dockle_scanner.py`, `scanners/base_image_checker.py`, `scanners/sonar_scanner.py`, `scanners/rules/*.yara`, `services/image_loader.py`, `services/policy_engine.py`, `services/result_aggregator.py`, `models/scan_request.py`, `models/scan_result.py`, `models/findings.py` |

### 16.5 Frontend

| Directory | Description |
|-----------|-------------|
| `frontend/src/pages/` | Page components (8 files) |
| `frontend/src/components/` | Reusable UI components |
| `frontend/src/context/` | React context (AuthContext) |
| `frontend/src/lib/` | API clients |
| `frontend/src/types/` | TypeScript type definitions |

### 16.6 Test Applications

| File | Description |
|------|-------------|
| `good-deployable-test/app.py` | Test Python app for deployment validation |
| `good-deployable-test/Dockerfile` | Test app Dockerfile |

---

## 17. Troubleshooting

### 17.1 Common Issues

**Issue: Auth service CrashLoopBackOff**
```
Cause: postgres not ready or missing GITHUB_CLIENT_ID
Fix: kubectl logs -n minipaas deploy/auth-service to check
     Ensure postgres is Running
     Check secret has GITHUB_CLIENT_ID
```

**Issue: Port 8080 not responding**
```
Cause: port-forward died after deploy restart
Fix: kill $(lsof -t -i :8080 -sTCP:LISTEN) 2>/dev/null
     setsid kubectl port-forward -n minipaas svc/frontend 8080:8080 &>/dev/null &
```

**Issue: ImagePullBackOff / ErrImagePull**
```
Cause: image not in containerd, cannot reach GHCR
Fix: Check ctr images pull works from the node
     k3s ctr -a /run/k3s/containerd/containerd.sock -n k8s.io images pull ghcr.io/carbon14-48/minipaas-{service}:latest
```

**Issue: Deploy job fails with "content digest not found"**
```
Cause: Old deploy script used docker save | ctr import (broken with containerd snapshotter)
Fix: Use ctr images pull directly (current script)
```

**Issue: Gitleaks fails on commit**
```
Cause: Secret value hardcoded in YAML
Fix: Use placeholders + GitHub Actions secrets injection
```

**Issue: Workflow fails at "Push to GHCR"**
```
Cause: Missing packages: write permission
Fix: Add permissions block to workflow:
     permissions:
       contents: read
       packages: write
```

**Issue: Runner not picking up jobs**
```
Cause: Runner process died
Fix: Check ps aux | grep Runner.Listener
     Restart: setsid ~/actions-runner/run.sh &> ~/actions-runner/runner.log &
```

**Issue: "namespaces minipaas not found" during deploy**
```
Cause: Race condition - resources applied before namespace ready
Fix: Apply namespace first, then rest (already fixed in deploy script)
```

**Issue: kubectl rollout restart --all fails**
```
Cause: kubectl rollout restart doesn't support --all flag
Fix: List deployments explicitly (already fixed in deploy script)
```

### 17.2 Health Checks

```bash
# Overall cluster health
kubectl get pods -n minipaas -o wide
kubectl get svc -n minipaas

# Service health endpoints
curl http://localhost:8080/health
curl http://localhost:8080/auth/health
curl http://localhost:8080/auth/github  # Should show client_id

# Port 30080 (NodePort - always up)
curl http://localhost:30080

# Check containerd images
k3s ctr -a /run/k3s/containerd/containerd.sock -n k8s.io images ls | grep minipaas
```

### 17.3 Runner Logs

```bash
# Watch runner activity
tail -f ~/actions-runner/runner.log

# Check deploy worker logs
ls -lt ~/actions-runner/_diag/Worker_*.log | head -1
tail -100 ~/actions-runner/_diag/Worker_*.log
```

---

## 18. Appendix

### 18.1 Port Reference

| Port | Service | Type | External |
|------|---------|------|----------|
| 8080 | Frontend | ClusterIP → NodePort 30080 | NodePort + port-forward |
| 8000 | api-gateway | ClusterIP | Internal only |
| 8000 | auth-service | ClusterIP | Internal only |
| 8000 | app-management | ClusterIP | Internal only |
| 8002 | build-service | ClusterIP | Internal only |
| 8000 | deployment-service | ClusterIP | Internal only |
| 8000 | deployer-service | ClusterIP | Internal only |
| 8006 | monitoring-service | ClusterIP | Internal only |
| 8005 | registry-service | ClusterIP | Internal only |
| 8000 | security-scanner | ClusterIP | Internal only |
| 5432 | postgres | ClusterIP | Internal only |
| 5672 | rabbitmq | ClusterIP | Internal only |
| 15672 | rabbitmq (mgmt) | ClusterIP | Internal only |
| 5000 | docker registry | ClusterIP | Internal only |
| 6443 | k3s API | Host | Local only |
| 30000-40000 | User apps | NodePort | External |

### 18.2 CI/CD Timeline

Average workflow duration: ~15-20 minutes

| Phase | Duration | Notes |
|-------|----------|-------|
| gitleaks | ~30s | |
| ruff | ~20s | |
| eslint + tsc | ~60s | |
| sonarcloud | ~3-4min | Runs tests for coverage |
| docker lint | ~30s | |
| docker compose build | ~5min | Parallel: builds all images |
| trivy scan | ~2min | Scans each image |
| dockle scan | ~2min | Scans each image |
| push to GHCR | ~3-5min | Uploads all images |
| deploy to k3s | ~3-5min | Pull + apply + restart |

### 18.3 Image Sizes (latest build)

| Service | Size |
|---------|------|
| auth-service | ~68 MB |
| app-management | ~68 MB |
| build-service | ~165 MB |
| deployment-service | ~68 MB |
| deployer-service | ~68 MB |
| monitoring-service | ~68 MB |
| registry-service | ~157 MB |
| security-scanner | ~68 MB (varies with scan tools) |
| api-gateway | ~68 MB |
| frontend | ~25 MB |

### 18.4 Environment Variables by Service

**auth-service**:
`APP_NAME`, `DEBUG`, `LOG_LEVEL`, `ALLOWED_ORIGINS`, `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRATION_MINUTES`, `REFRESH_TOKEN_SECRET`, `REFRESH_TOKEN_ALGORITHM`, `REFRESH_TOKEN_EXPIRATION_DAYS`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`

**build-service**:
`DATABASE_URL`, `AUTH_SERVICE_URL`, `REGISTRY_SERVICE_URL`, `SCANNER_SERVICE_URL`, `BUILD_WORKDIR`, `MAX_BUILD_TIMEOUT`, `DOCKER_REGISTRY_URL`, `DOCKER_SOCKET_PATH`, `LOG_LEVEL`, `DEBUG`

**security-scanner**:
`TRIVY_PATH`, `YARA_RULES_DIR`, `CLAMAV_DB_PATH`, `SCANNER_MAX_TIMEOUT`, `BLOCK_ON_HIGH_CVES`, `BLOCK_ON_MALWARE`, `BLOCK_ON_SECRETS`, `BLOCK_ON_ROOT_USER`, `AUTH_SERVICE_URL`, `LOG_LEVEL`, `DEBUG`

**monitoring-service**:
`DATABASE_URL`, `COLLECT_INTERVAL_SECONDS`, `METRICS_RETENTION_DAYS`, `LOG_TAIL_LINES`, `AUTH_SERVICE_URL`, `LOG_LEVEL`, `DEBUG`

**deployment-service**:
`KUBECONFIG_PATH`, `HOST_PORT_RANGE_START`, `HOST_PORT_RANGE_END`, `CLOUDOKU_DOMAIN`, `AUTH_SERVICE_URL`, `LOG_LEVEL`, `DEBUG`

**All services**:
`ENV`, `JWT_ALGORITHM`, `JWT_SECRET_KEY`, `GITHUB_API_URL`, `ALLOWED_ORIGINS`

### 18.5 Versions

| Component | Version |
|-----------|---------|
| K3s | v1.32.2+k3s1 (containerd v2.2.3-k3s1) |
| Docker | 29.3.1 (containerd snapshotter v1) |
| Python | 3.12 (3.14 for auth-service) |
| Node | 20.x |
| PostgreSQL | 16-alpine |
| RabbitMQ | 3-management-alpine |
| Docker Registry | 2 |
| React | 18.3.x |
| TypeScript | 5.x |
| Vite | 6.x |
| TailwindCSS | 3.x |
| FastAPI | latest |
| SQLAlchemy | 2.0+ |

### 18.6 Related Files

| File | Purpose |
|------|---------|
| `deploy-from-ghcr.sh` | CI/CD deploy script — pulls images, applies manifests, restarts services |
| `.github/workflows/lint.yml` | Main CI/CD pipeline |
| `k8s/secret.yaml` | Kubernetes secret template |
| `k8s/configmap.yaml` | Shared configuration |
| `k8s/frontend/nginx-configmap.yaml` | Frontend reverse proxy config |
| `.env` | Local environment variables (gitignored) |

---

*Generated: 2026-06-19*

*Last updated: CI/CD pipeline with self-hosted runner, k3s deployment, GitHub OAuth, multi-layer security scanning*
