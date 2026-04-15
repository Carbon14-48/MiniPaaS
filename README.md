# MiniPaaS - Mini Heroku-like PaaS

A lightweight Platform-as-a-Service that allows developers to deploy applications by simply connecting their GitHub repositories. Built with microservices architecture and DevSecOps practices.

## Overview

MiniPaaS enables you to:
- Connect your GitHub account via OAuth
- Browse and select repositories from your GitHub account
- Deploy any repository with a Dockerfile (or auto-generate one for Python/Node/Java)
- Security scanning ensures deployed images are free from vulnerabilities
- Manage deployments through a web dashboard
- View logs and control container lifecycle (start, stop, restart)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend (React)                                │
│                    http://localhost:5173 (Vite Dev Server)                   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Deployer Service (8008)                             │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Deployments  │  │    GitHub    │  │    Health    │  │     Logs     │  │
│  │     CRUD      │  │  Repos/Branches│  │              │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘  └──────────────┘  │
│         │                  │                                                   │
│         ▼                  ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     Service Clients                                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │   Auth   │  │  Build   │  │ Registry │  │  Docker  │           │   │
│  │  │ Service  │  │ Service  │  │ Service  │  │   Runner │           │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │   │
│  └───────┼─────────────┼─────────────┼─────────────┼──────────────────┘   │
└──────────┼─────────────┼─────────────┼─────────────┼──────────────────────┘
           │             │             │             │
           ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Service Mesh                                       │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │  Auth Service │  │ Build Service  │  │Registry Service│                 │
│  │    (8001)     │  │    (8003)      │  │    (8007)      │                 │
│  │               │  │                │  │                │                 │
│  │ • JWT Tokens  │  │ • Git Clone    │  │ • Docker Tag   │                 │
│  │ • GitHub OAuth│  │ • Dockerfile    │  │ • Docker Push  │                 │
│  │ • User Mgmt   │  │ • Docker Build │  │ • Image Store │                 │
│  │ • Token Refresh│ │ • Security Scan│  │                │                 │
│  └────────────────┘  └───────┬────────┘  └────────────────┘                 │
│                             │                                                │
│                             ▼                                                │
│                    ┌────────────────┐                                       │
│                    │Security Scanner│                                       │
│                    │    (8006)      │                                       │
│                    │                │                                       │
│                    │ • Trivy CVE   │                                       │
│                    │ • ClamAV       │                                       │
│                    │ • YARA Rules  │                                       │
│                    │ • TruffleHog   │                                       │
│                    │ • Dockle       │                                       │
│                    └────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Infrastructure                                       │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  PostgreSQL │  │   RabbitMQ  │  │    Redis    │  │   Docker    │       │
│  │  (Database) │  │   (Queue)   │  │   (Cache)   │  │  (Runtime)  │       │
│  │   :5432     │  │    :5672    │  │    :6379    │  │  Daemon     │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────┬──────┘       │
│                                                              │              │
│                     ┌───────────────────────────────────────┘              │
│                     ▼                                                      │
│              ┌─────────────┐  ┌─────────────┐                                │
│              │   Docker    │  │  Container  │                                │
│              │  Registry   │  │  Runtime    │                                │
│              │   :5000     │  │  Ports      │                                │
│              └─────────────┘  │ 30000-40000 │                                │
│                               └─────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Microservices

| Service | Port | Description | Status |
|---------|------|-------------|--------|
| [auth-service](services/auth-service/README.md) | 8001 | JWT authentication, GitHub OAuth, user management | ✅ Production |
| [build-service](services/build-service/README.md) | 8003 | Git clone, Docker build, security scan, push to registry | ✅ Production |
| [registry-service](services/registry-service/README_registry.md) | 8007 | Docker image storage, tagging, pushing to local registry | ✅ Production |
| [security-scanner](services/security-scanner/README.md) | 8006 | Multi-layer security scanning (Trivy, ClamAV, YARA, etc.) | ✅ Production |
| [deployer-service](services/deployer-service/README.md) | 8008 | End-to-end deployment orchestration, GitHub integration | ✅ Production |
| api-gateway | 8000 | Entry point, routing, rate limiting | 🔧 Stub |
| app-management | 8002 | App CRUD, config management | 🔧 Stub |
| deployment-service | 8004 | Kubernetes deployment (future) | 🔧 Stub |
| monitoring-service | 8005 | Logs, metrics, health checks | 🔧 Stub |

## Deployment Flow

```
User Action                          System Flow
───────────────────────────────────────────────────────────────────────────────

1. User logs in via GitHub OAuth
   ───────────────────────────────────────────────────────────────────────────►
   
   ┌─────────┐    OAuth    ┌─────────┐   Token    ┌─────────┐
   │ Browser │ ──────────► │  Auth   │ ────────► │ GitHub  │
   └─────────┘             │Service  │            │   API   │
                           └─────────┘            └─────────┘
                               │
                               ▼
                          JWT Tokens
                          (access + refresh)
                               │
2. User selects repository       │
   ───────────────────────────────────────────────────────────────────────────►
   
   ┌─────────┐   GET /repos   ┌─────────────┐   GitHub API   ┌─────────┐
   │ Browser │ ─────────────► │  Deployer   │ ─────────────► │ GitHub  │
   └─────────┘                │  Service    │                │   API   │
                              └─────────────┘                └─────────┘
   
3. User clicks "Deploy"         │
   ───────────────────────────────────────────────────────────────────────────►
   
   ┌─────────┐  POST /deployments  ┌─────────────┐
   │ Browser │ ─────────────────►  │  Deployer    │
   └─────────┘                     │  Service     │
                                   └──────┬──────┘
                                          │
                                          │ 1. Verify JWT
                                          ▼
                                   ┌─────────────┐
                                   │Auth Service │
                                   └──────┬──────┘
                                          │
                                          │ 2. Trigger Build
                                          ▼
                                   ┌─────────────┐
                                   │  Build      │
                                   │  Service    │
                                   └──────┬──────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
              ┌───────────┐        ┌───────────┐        ┌───────────┐
              │Git Clone  │        │ Dockerfile │        │Docker Build│
              │  Repo     │        │ Detect/   │        │   Image   │
              └───────────┘        │ Generate  │        └─────┬─────┘
                                   └───────────┘              │
                                                              │
                                                              ▼
                                                       ┌───────────┐
                                                       │ Security  │
                                                       │ Scanner   │
                                                       └─────┬─────┘
                                                             │
                                        ┌────────────────────┼────────────────────┐
                                        │                    │                    │
                                        ▼                    ▼                    ▼
                                  ┌───────────┐       ┌───────────┐       ┌───────────┐
                                  │   PASS    │       │   WARN    │       │  BLOCKED  │
                                  │(no critical│       │(warnings  │       │(critical  │
                                  │   CVEs)   │       │  only)    │       │  CVEs)    │
                                  └─────┬─────┘       └─────┬─────┘       └───────────┘
                                        │                     │
                                        │                     │
                                        └──────────┬──────────┘
                                                   │
                                                   ▼
                                            ┌───────────┐
                                            │  Registry │
                                            │  Service  │
                                            └─────┬─────┘
                                                  │
                                                  │ Push Image
                                                  ▼
                                           ┌───────────┐
                                           │  Docker   │
                                           │ Registry  │
                                           │   :5000   │
                                           └─────┬─────┘
                                                 │
                                                 │ 3. Run Container
                                                 ▼
                                          ┌───────────┐
                                          │  Docker   │
                                          │  Daemon   │
                                          └─────┬─────┘
                                                │
                                                ▼
                                          ┌───────────┐
                                          │ Container  │
                                          │ Running on │
                                          │ Port 3xxxx │
                                          └───────────┘

4. Deployment Complete         │
   ◄──────────────────────────────────────────────────────────────────────────
   
   ┌─────────┐  GET /deployments   ┌─────────────┐
   │ Browser │ ◄─────────────────  │  Deployer    │
   └─────────┘                     │  Service     │
                                   └─────────────┘
```

## Security Pipeline

The security scanner performs multi-layer analysis before any image is deployed:

| Scanner | Purpose | Blocking Policy |
|---------|---------|------------------|
| **Trivy** | CVE detection in OS packages and dependencies | Blocks CRITICAL CVEs only |
| **ClamAV** | Malware detection in container filesystem | Warning only (permissive mode) |
| **YARA Rules** | Custom threat patterns (webshells, reverse shells, etc.) | Warning only |
| **TruffleHog** | Secret detection (API keys, passwords in code) | Warning only |
| **Dockle** | CIS Docker benchmark compliance | Warning only |
| **Base Image Check** | Approved base images list | Warning only |

### Base Image Allowlist

The scanner accepts these base images (among others):
- Python: `python:3.8-slim` through `python:3.13-slim`, alpine variants
- Node: `node:16-alpine` through `node:22-alpine`, slim variants
- Go: `golang:1.20-alpine` through `golang:1.23-alpine`
- Alpine, Debian, Ubuntu (all versions)
- Distroless images

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL client (for local development)

### Local Development Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd MiniPaaS

# 2. Install frontend dependencies
cd frontend
npm install
cd ..

# 3. Install backend dependencies for each service
for service in auth-service build-service registry-service security-scanner deployer-service; do
    cd services/$service
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ../..
done

# 4. Start infrastructure
docker compose up -d postgres redis rabbitmq registry

# 5. Start all services (in separate terminals)
# Terminal 1: Auth Service
cd services/auth-service && source venv/bin/activate && uvicorn src.main:app --reload --port 8001

# Terminal 2: Build Service
cd services/build-service && source venv/bin/activate && uvicorn src.main:app --reload --port 8003

# Terminal 3: Registry Service
cd services/registry-service && source venv/bin/activate && uvicorn src.main:app --reload --port 8007

# Terminal 4: Security Scanner
cd services/security-scanner && source venv/bin/activate && uvicorn src.main:app --reload --port 8006

# Terminal 5: Deployer Service
cd services/deployer-service && source venv/bin/activate && uvicorn src.main:app --reload --port 8008

# Terminal 6: Frontend
cd frontend && npm run dev
```

### Production Deployment (Docker Compose)

```bash
# Start all services with Docker Compose
docker compose up -d

# Check service health
docker compose ps

# View logs
docker compose logs -f deployer-service
```

## Service Ports Reference

| Service | Port | URL |
|---------|------|-----|
| Frontend | 5173 | http://localhost:5173 |
| Auth Service | 8001 | http://localhost:8001 |
| Build Service | 8003 | http://localhost:8003 |
| Security Scanner | 8006 | http://localhost:8006 |
| Registry Service | 8007 | http://localhost:8007 |
| Deployer Service | 8008 | http://localhost:8008 |
| Docker Registry | 5000 | http://localhost:5000 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

## Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://minipaas:minipaas@localhost:5432/minipaas

# GitHub OAuth (create at https://github.com/settings/developers)
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:5173/oauth/github/callback

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Service URLs (for local development)
AUTH_SERVICE_URL=http://localhost:8001
BUILD_SERVICE_URL=http://localhost:8003
SCANNER_SERVICE_URL=http://localhost:8006
REGISTRY_SERVICE_URL=http://localhost:8007
DEPLOYER_SERVICE_URL=http://localhost:8008

# Docker Registry
REGISTRY_HOST=localhost:5000
```

## Testing

```bash
# Run all tests
./scripts/test-all.sh

# Run tests for specific service
cd services/deployer-service
pytest tests/

# Test deployment flow manually
curl -X POST http://localhost:8008/deployments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "repo_url": "https://github.com/username/repo",
    "branch": "main",
    "app_name": "my-app"
  }'
```

## API Documentation

- [Auth Service API](services/auth-service/README.md)
- [Build Service API](services/build-service/README.md)
- [Registry Service API](services/registry-service/README_registry.md)
- [Security Scanner API](services/security-scanner/README.md)
- [Deployer Service API](services/deployer-service/README.md)

## Documentation

- [Architecture](docs/architecture.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)
- [Security](docs/security.md)
- [API Reference](docs/api/)

## DevSecOps Pipeline

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Push   │───►│  Build  │───►│  Test   │───►│  Scan   │───►│ Deploy  │
│  Code   │    │         │    │         │    │         │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    ▼              ▼              ▼
                              ┌─────────┐   ┌─────────┐   ┌─────────┐
                              │  Trivy  │   │ ClamAV  │   │  YARA   │
                              │  CVE    │   │ Malware │   │ Custom  │
                              │ Scan    │   │ Detect  │   │ Rules   │
                              └─────────┘   └─────────┘   └─────────┘
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- Open an issue for bugs or feature requests
- Join the discussion on GitHub Discussions
