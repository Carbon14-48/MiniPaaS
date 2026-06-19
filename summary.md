# MiniPaaS — Current Architecture & Setup

## Architecture

Microservices PaaS deployed on k3s (single-node Kubernetes). Users connect GitHub repos → auto-build Docker images → security scan → deploy as containers.

### Services (all in `minipaas` namespace)

| Service | Role |
|---------|------|
| **frontend** | React + TypeScript SPA, served via nginx, port 8080 |
| **api-gateway** | Entry point, proxies `/auth/*`, `/builds/*`, `/deployments/*` etc. to services |
| **auth-service** | JWT auth, GitHub OAuth, user management (FastAPI + PostgreSQL) |
| **app-management** | App CRUD (FastAPI) |
| **build-service** | Git clone, Docker build (FastAPI + RabbitMQ) |
| **deployment-service** | K8s deployment orchestration |
| **deployer-service** | End-to-end deployment flow |
| **monitoring-service** | Logs, metrics, health checks |
| **registry-service** | Docker image tagging & metadata |
| **security-scanner** | Trivy, ClamAV, YARA, Dockle, TruffleHog scans |
| **postgres** | Primary database (StatefulSet) |
| **rabbitmq** | Message broker for async tasks |
| **registry** | Docker registry for user app images |

### Networking

- **NodePort 30080** → frontend service (port 8080)
- **Port-forward 8080** → localhost:8080 → frontend
- All inter-service communication via internal k8s DNS

## CI/CD Pipeline (`.github/workflows/lint.yml`)

```
push to main → gitleaks → ruff → eslint+tsc → sonarcloud → hadolint+checkov → docker compose build → trivy scan → dockle scan → push to GHCR → deploy to k3s
```

### Deploy steps (self-hosted runner on this machine):
1. `ctr images pull` each image directly from GHCR into containerd
2. `kubectl apply -f k8s/namespace.yaml` (first)
3. `kubectl apply -f k8s/*.yaml` and `k8s/*/` (configs, secrets, all services)
4. Inject `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET` from GitHub Actions secrets into the k8s Secret
5. Rollout restart all deployments, wait for readiness
6. Port-forward localhost:8080 → frontend

## Infrastructure

- **K3s** on single node (containerd runtime, no Docker dependency in cluster)
- **k8s manifests** at `k8s/` — plain YAML per service dir
- **Secrets** via `k8s/secret.yaml` (placeholders) + runtime injection from GitHub Actions secrets
- **Images** stored on GHCR (`ghcr.io/carbon14-48/minipaas-*`)

## Key Tools

| Tool | Use |
|------|-----|
| **Trivy** | CVE scanning (CI + runtime) |
| **Dockle** | Docker CIS benchmark (CI) |
| **Hadolint** | Dockerfile linting |
| **Checkov** | Infrastructure as Code scanning |
| **Gitleaks** | Secret leak detection |
| **SonarCloud** | Code quality & coverage |
| **Ruff** | Python linting |
| **ESLint + tsc** | TypeScript/React quality |

## Access

- **Frontend**: http://localhost:8080 or http://localhost:30080
- **GitHub Login**: OAuth flow → authorize → callback to `/oauth/github/callback` → JWT tokens

## Automation

- Self-hosted runner (`~/actions-runner/`) listens for deploy jobs
- On each push to `main`: build → scan → push → deploy (full cycle ~15-20 min)
- Port-forward auto-restored after each deploy via `deploy-from-ghcr.sh`
