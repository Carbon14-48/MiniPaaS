# MiniPaaS - Comprehensive Repository Scan Report

## Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Services Architecture](#services-architecture)
4. [Technology Stack](#technology-stack)
5. [DevSecOps Implementation](#devsecops-implementation)
6. [CI/CD Pipelines](#cicd-pipelines)
7. [Security Tools & Features](#security-tools--features)
8. [Infrastructure](#infrastructure)
9. [Development Practices](#development-practices)
10. [File Inventory](#file-inventory)

---

## 1. Project Overview

### Project Name
**MiniPaaS** (also known as Cloudoku)

### Description
A lightweight Platform-as-a-Service (PaaS) that allows developers to deploy applications by connecting their GitHub repositories. Built with microservices architecture and DevSecOps practices.

### Core Features
- GitHub OAuth authentication
- Repository browsing and selection
- Automated Dockerfile generation for Python/Node/Java
- Security scanning of Docker images
- Web dashboard for deployment management
- Container lifecycle control (start, stop, restart)
- Log viewing and monitoring

### Current Status
- Multiple services in production/development
- Comprehensive security pipeline implemented
- Kubernetes deployment support

---

## 2. Repository Structure

```
MiniPaaS/
├── .github/
│   └── workflows/          # CI/CD pipelines (GitHub Actions)
│       ├── ci-api-gateway.yml
│       ├── ci-auth-service.yml
│       ├── ci-build-service.yml
│       ├── ci-deployer-service.yml
│       ├── ci-deployment-service.yml
│       ├── ci-frontend.yml
│       ├── ci-monitoring.yml
│       ├── ci-security-scanner.yml
│       ├── deploy.yml
│       └── security-scan.yml
├── docs/
│   ├── api/
│   │   ├── README.md
│   │   └── service-auth-contract-v1.md
│   ├── architecture.md
│   ├── deployment.md
│   ├── development.md
│   └── security.md
├── docker/
├── frontend/                # React + TypeScript frontend
├── good-deployable-test/
├── infra/
│   ├── docker/
│   │   └── docker-compose.yml
│   └── kubernetes/
│       ├── base/
│       │   ├── configmaps/
│       │   ├── deployments/
│       │   ├── namespaces.yaml
│       │   ├── secrets/
│       │   └── services/
│       └── overlays/
│           ├── dev/
│           └── prod/
├── scripts/
│   ├── dev.sh
│   ├── lint-all.sh
│   ├── setup.sh
│   └── test-all.sh
├── services/
│   ├── api-gateway/
│   ├── app-management/
│   ├── auth-service/
│   ├── build-service/
│   ├── deployer-service/
│   ├── deployment-service/
│   ├── monitoring-service/
│   ├── registry-service/
│   └── security-scanner/
├── shared/
│   └── python/
│       └── cloudoku_common/
├── Makefile
├── README.md
└── LICENSE
```

---

## 3. Services Architecture

### Service Inventory

| Service | Port | Description | Technology | Status |
|---------|------|-------------|------------|--------|
| **Frontend** | 5173 | Web dashboard (React) | React + TypeScript + Vite | Production |
| **Auth Service** | 8001 | JWT auth, GitHub OAuth, user management | Python FastAPI | Production |
| **API Gateway** | 8000 | Entry point, routing, rate limiting | Python FastAPI | Stub |
| **App Management** | 8002 | App CRUD, config management | Python FastAPI | Stub |
| **Build Service** | 8003 | Git clone, Docker build, security scan | Python FastAPI | Production |
| **Deployment Service** | 8004 | Kubernetes deployment | Python FastAPI | Stub |
| **Monitoring Service** | 8005 | Logs, metrics, health checks | Python FastAPI | Stub |
| **Security Scanner** | 8006 | Multi-layer security scanning | Python FastAPI | Production |
| **Registry Service** | 8007 | Docker image storage, tagging | Python FastAPI | Production |
| **Deployer Service** | 8008 | End-to-end deployment orchestration | Python FastAPI | Production |

### Service Communication

- **Synchronous**: HTTP/REST between services via API Gateway
- **Asynchronous**: RabbitMQ for event-driven communication (build triggers, deployment events)

### Data Flow

1. User creates app via frontend → API Gateway → App Management Service
2. App Management triggers build → Build Service (via RabbitMQ)
3. Build Service clones repo, builds Docker image, pushes to registry
4. Security Scanner scans the image
5. Deployment Service deploys to Kubernetes
6. Monitoring Service collects logs and metrics

---

## 4. Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL 16-alpine
- **ORM**: SQLAlchemy 2.0 + Alembic
- **Authentication**: JWT (PyJWT) + bcrypt
- **Message Broker**: RabbitMQ 3-management-alpine
- **Cache**: Redis 7-alpine

### Frontend
- **Framework**: React 18.3.x
- **Language**: TypeScript 5.x
- **Build Tool**: Vite 6.x
- **Styling**: TailwindCSS 3.x
- **Routing**: React Router DOM 7.x
- **Charts**: Recharts 3.x
- **Animations**: Framer Motion 12.x

### Infrastructure
- **Container Runtime**: Docker
- **Orchestration**: Kubernetes
- **Container Registries**: Local Docker Registry (port 5000)
- **Monitoring**: Prometheus + Grafana
- **Code Quality**: SonarQube

### Development Tools
- **Python Version**: 3.12 (primary), 3.14 (auth-service)
- **Node Version**: 20.x
- **Linting**: Ruff
- **Testing**: pytest, pytest-asyncio

---

## 5. DevSecOps Implementation

### DevSecOps Pipeline Overview

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
                         │  Scan   │   │ Detect  │   │ Rules   │
                         └─────────┘   └─────────┘   └─────────┘
```

### Phase 1: Plan (Planning & Design)

- **Threat Modeling**: Architecture analysis for Flask, Django, FastAPI applications
- **Secure Configuration**: Hardened configurations for containers and servers defined in documentation
- **Security by Design**: All services implement security best practices from the start

### Phase 2: Code (Development)

- **Static Analysis**: Bandit for Python security scanning
- **Linting**: Flake8, Ruff for code quality
- **Secret Management**: Environment variables, .gitignore for secrets protection
- **Pre-commit hooks**: Noted in .git/info/exclude

### Phase 3: Build (CI)

- **Dependency Scanning**: Safety, pip-audit for Python packages
- **SAST**: GitHub Actions workflows with security scanning
- **Container Scanning**: Trivy, Hadolint for Dockerfile analysis
- **Build Tests**: pytest runs on every commit

### Phase 4: Deploy (CD)

- **Kubernetes Security**: Kustomize for configuration management
- **Image Scanning**: Security scanner in deployment pipeline
- **Policy Enforcement**: Blocks CRITICAL CVEs, warns on others

### Phase 5: Operate (Runtime)

- **Monitoring**: Prometheus + Grafana dashboards
- **Logging**: Centralized logging service
- **Health Checks**: All services implement /health endpoints
- **Security Updates**: Trivy database updates

---

## 6. CI/CD Pipelines

### GitHub Actions Workflows

#### 1. Security Scan Workflow (security-scan.yml)
```yaml
- Trigger: push to main, pull_request to main
- Jobs:
  - trivy-scan: Scans filesystem for vulnerabilities (CRITICAL, HIGH)
  - sonarqube: Code quality and security analysis (requires SONAR_TOKEN)
```

#### 2. Deploy Workflow (deploy.yml)
```yaml
- Trigger: push to main branch
- Steps:
  - Builds Docker images for all services
  - Deploys to Kubernetes using kubectl apply -k
```

#### 3. Service-Specific CI Workflows

Each service has its own CI workflow:
- **ci-api-gateway.yml** - Tests + pip install
- **ci-auth-service.yml** - Tests + pip install
- **ci-build-service.yml** - Tests + pip install
- **ci-deployer-service.yml** - Tests + pip install + ruff lint
- **ci-deployment-service.yml** - Tests + pip install
- **ci-frontend.yml** - npm ci + npm run build
- **ci-monitoring-service.yml** - Tests + pip install
- **ci-security-scanner.yml** - Tests + pip install

### Testing Pipeline

The project uses a comprehensive testing approach:

1. **Unit Tests**: pytest in each service's tests/ directory
2. **Integration Tests**: Service-to-service communication tests
3. **Test Execution**: scripts/test-all.sh runs all service tests

---

## 7. Security Tools & Features

### Security Scanner (Primary Security Feature)

The security-scanner service implements multi-layer security scanning:

#### Scanning Tools Implemented

| Tool | Purpose | Blocking Policy |
|------|---------|-----------------|
| **Trivy** | CVE detection in OS packages and dependencies | Blocks CRITICAL/HIGH CVEs |
| **ClamAV** | Malware detection in container filesystem | Warning only |
| **YARA Rules** | Custom threat patterns | Warning only |
| **TruffleHog** | Secret detection (API keys, passwords) | Warning only |
| **Dockle** | CIS Docker benchmark compliance | Warning only |
| **Base Image Check** | Approved base images list | Warning only |

#### YARA Rules Categories

- **crypto_miners.yara**: XMRig binary signatures, mining pool patterns
- **webshells.yara**: eval(base64_decode()), system() abuse, backdoor PHP shells
- **container_escape.yara**: Host filesystem access, cgroup escape, docker socket abuse
- **reverse_shells.yara**: /dev/tcp/, bash reverse shells, nc -e patterns
- **rootkits.yara**: Cron job anomalies, systemd injection, SSH abuse
- **general_malware.yara**: Known backdoor binaries, suspicious ELF headers

#### Base Image Allowlist (Strict)

**Python:**
- python:3.8-slim through python:3.13-slim
- python:3.8-alpine through python:3.13-alpine

**Node.js:**
- node:16-alpine through node:22-alpine
- node:16-slim through node:22-slim

**Go:**
- golang:1.20-alpine through golang:1.23-alpine

**Java:**
- eclipse-temurin:8-jre-alpine through eclipse-temurin:21-jre-alpine

**Distroless (Production Recommended):**
- gcr.io/distroless/python3-debian11/12
- gcr.io/distroless/nodejs18/20-debian11

**Blocked Base Images:**
- scratch (no package manager)
- ubuntu:latest, ubuntu:20.04, ubuntu:21.04
- debian:latest, debian:stable
- centos:*, rockylinux:*, fedora:*
- busybox:*
- amazoncorretto:*, openjdk:*
- Any image with 'latest' tag

### Authentication & Authorization

- **JWT Tokens**: HS256 algorithm
- **Token Expiration**: Configurable (default: 15 min access, 7 days refresh)
- **GitHub OAuth**: Full OAuth 2.0 flow
- **Password Hashing**: bcrypt

### Infrastructure Security

- **Kubernetes**: RBAC, least-privilege service accounts
- **Secrets Management**: Kubernetes Secrets + environment variables
- **Network Policies**: Namespace isolation

---

## 8. Infrastructure

### Docker Compose Services

```yaml
- postgres:16-alpine        # Database
- rabbitmq:3-management     # Message broker
- redis:7-alpine           # Cache
- prometheus:latest        # Metrics
- grafana:latest           # Dashboards
- sonarqube:community      # Code quality
```

### Kubernetes Configuration

#### Base Configuration (infra/kubernetes/base/)
- namespaces.yaml: cloudoku namespace
- configmaps/cloudoku-config.yaml: Application configuration
- secrets/cloudoku-secrets.yaml: JWT secret, DB password
- deployments/api-gateway.yaml: API Gateway deployment
- services/api-gateway.yaml: Service definitions

#### Overlays
- **dev/**: Kustomize overlay for development
- **prod/**: Kustomize overlay for production

---

## 9. Development Practices

### Code Quality

1. **Linting**: Ruff (scripts/lint-all.sh)
2. **Testing**: pytest (scripts/test-all.sh)
3. **Type Checking**: TypeScript for frontend, Pydantic for backend

### Project Management

- **Makefile Targets**:
  - make setup: Initial project setup
  - make dev: Start all services locally
  - make stop: Stop all services
  - make test: Run all tests
  - make lint: Lint all services
  - make build: Build all Docker images
  - make clean: Clean up build artifacts

### Environment Configuration

Each service uses:
- .env files for local development
- .env.example for template
- pydantic-settings for configuration management

---

## 10. File Inventory

### Root Level Files
- README.md - Main project documentation
- LICENSE - MIT License
- Makefile - Build automation
- .gitignore - Git ignore patterns
- scan_result.json - Previous scan results
- scan_result_v2.json - Additional scan results
- logs_res.json - Log data

### GitHub Actions Workflows (10 files)
- .github/workflows/ci-api-gateway.yml
- .github/workflows/ci-auth-service.yml
- .github/workflows/ci-build-service.yml
- .github/workflows/ci-deployer-service.yml
- .github/workflows/ci-deployment-service.yml
- .github/workflows/ci-frontend.yml
- .github/workflows/ci-monitoring.yml
- .github/workflows/ci-security-scanner.yml
- .github/workflows/deploy.yml
- .github/workflows/security-scan.yml

### Documentation Files
- docs/architecture.md - System architecture
- docs/deployment.md - Deployment guide
- docs/development.md - Development guide
- docs/security.md - Security documentation
- docs/api/README.md - API documentation
- docs/api/service-auth-contract-v1.md - Auth contract

### Scripts (4 files)
- scripts/setup.sh - Project setup
- scripts/dev.sh - Development mode
- scripts/test-all.sh - Test all services
- scripts/lint-all.sh - Lint all services

### Infrastructure Files
- infra/docker/docker-compose.yml - Docker compose configuration
- infra/kubernetes/base/namespaces.yaml
- infra/kubernetes/base/secrets/cloudoku-secrets.yaml
- infra/kubernetes/base/configmaps/cloudoku-config.yaml
- infra/kubernetes/base/deployments/api-gateway.yaml
- infra/kubernetes/base/services/api-gateway.yaml
- infra/kubernetes/overlays/dev/kustomization.yaml
- infra/kubernetes/overlays/prod/kustomization.yaml

### Frontend Files
- frontend/package.json - NPM dependencies
- frontend/package-lock.json - Locked dependencies
- frontend/tsconfig.json - TypeScript config
- frontend/tsconfig.node.json - Node TypeScript config
- frontend/vite.config.ts - Vite configuration
- frontend/tailwind.config.js - TailwindCSS config
- frontend/postcss.config.js - PostCSS config
- frontend/server.py - Server file
- frontend/src/main.tsx - React entry point
- frontend/src/App.tsx - Main app component
- frontend/src/index.css - Global styles

**Frontend Components:**
- frontend/src/components/layout/AuthBackground.tsx
- frontend/src/components/monitoring/AppCharts.tsx
- frontend/src/components/monitoring/HealthGrid.tsx
- frontend/src/components/monitoring/LogConsole.tsx
- frontend/src/components/monitoring/OverviewCards.tsx
- frontend/src/components/ui/DeploymentCard.tsx
- frontend/src/components/ui/Lightning.tsx
- frontend/src/components/ui/LogViewer.tsx
- frontend/src/components/ui/RepoCard.tsx
- frontend/src/components/ui/StatusBadge.tsx

**Frontend Pages:**
- frontend/src/pages/Dashboard.tsx
- frontend/src/pages/Deployments.tsx
- frontend/src/pages/GitHubCallback.tsx
- frontend/src/pages/Home.tsx
- frontend/src/pages/Login.tsx
- frontend/src/pages/Monitoring.tsx
- frontend/src/pages/NewDeployment.tsx
- frontend/src/pages/Register.tsx
- frontend/src/pages/Repositories.tsx

**Frontend Utilities:**
- frontend/src/context/AuthContext.tsx
- frontend/src/lib/api.ts
- frontend/src/lib/monitoringApi.ts
- frontend/src/types/auth.ts

### Service: Auth Service (8001)
- services/auth-service/Dockerfile
- services/auth-service/requirements.txt
- services/auth-service/alembic.ini
- services/auth-service/src/main.py
- services/auth-service/src/config.py
- services/auth-service/src/database.py
- services/auth-service/src/models/user.py
- services/auth-service/src/routes/auth.py
- services/auth-service/src/routes/health.py
- services/auth-service/src/services/auth_service.py
- services/auth-service/tests/test_auth.py
- services/auth-service/tests/test_health.py
- services/auth-service/tests/test_password.py
- services/auth-service/migrations/versions/001_initial.py

### Service: Build Service (8003)
- services/build-service/Dockerfile
- services/build-service/requirements.txt
- services/build-service/alembic.ini
- services/build-service/src/main.py
- services/build-service/src/config.py
- services/build-service/src/db.py
- services/build-service/src/models/job.py
- services/build-service/src/routes/build.py
- services/build-service/src/services/docker_service.py
- services/build-service/src/services/git_service.py
- services/build-service/src/services/auth_client.py
- services/build-service/src/services/registry_client.py
- services/build-service/src/services/scanner_client.py
- services/build-service/tests/test_build_route.py
- services/build-service/tests/test_docker_service.py

### Service: Security Scanner (8006)
- services/security-scanner/Dockerfile
- services/security-scanner/requirements.txt
- services/security-scanner/src/main.py
- services/security-scanner/src/config.py
- services/security-scanner/src/routes/health.py
- services/security-scanner/src/routes/scans.py
- services/security-scanner/src/scanners/base_image_checker.py
- services/security-scanner/src/scanners/clamav_scanner.py
- services/security-scanner/src/scanners/dockle_scanner.py
- services/security-scanner/src/scanners/sonar_scanner.py
- services/security-scanner/src/scanners/trivy_scanner.py
- services/security-scanner/src/scanners/trufflehog_scanner.py
- services/security-scanner/src/scanners/yara_scanner.py
- services/security-scanner/src/scanners/rules/container_escape.yara
- services/security-scanner/src/scanners/rules/crypto_miners.yara
- services/security-scanner/src/scanners/rules/general_malware.yara
- services/security-scanner/src/scanners/rules/reverse_shells.yara
- services/security-scanner/src/scanners/rules/rootkits.yara
- services/security-scanner/src/scanners/rules/webshells.yara
- services/security-scanner/src/services/image_loader.py
- services/security-scanner/src/services/policy_engine.py
- services/security-scanner/src/services/result_aggregator.py
- services/security-scanner/src/models/scan_request.py
- services/security-scanner/src/models/scan_result.py
- services/security-scanner/src/models/findings.py
- services/security-scanner/tests/test_health.py
- services/security-scanner/tests/test_trivy_scanner.py
- services/security-scanner/tests/test_clamav_scanner.py
- services/security-scanner/tests/test_yara_scanner.py
- services/security-scanner/tests/test_trufflehog_scanner.py
- services/security-scanner/tests/test_base_image_checker.py
- services/security-scanner/tests/test_policy_engine.py
- services/security-scanner/tests/test_result_aggregator.py

### Service: Registry Service (8007)
- services/registry-service/Dockerfile
- services/registry-service/requirements.txt
- services/registry-service/alembic.ini
- services/registry-service/src/main.py
- services/registry-service/src/config.py
- services/registry-service/src/db.py
- services/registry-service/src/models/image.py
- services/registry-service/src/routes/registry.py
- services/registry-service/src/services/docker_registry.py
- services/registry-service/tests/test_registry_route.py
- services/registry-service/tests/test_docker_registry.py

### Service: Deployer Service (8008)
- services/deployer-service/Dockerfile
- services/deployer-service/requirements.txt
- services/deployer-service/src/main.py
- services/deployer-service/src/config.py
- services/deployer-service/src/db.py
- services/deployer-service/src/models/deployment.py
- services/deployer-service/src/routes/deployments.py
- services/deployer-service/src/routes/github.py
- services/deployer-service/src/routes/health.py
- services/deployer-service/src/services/auth_client.py
- services/deployer-service/src/services/build_client.py
- services/deployer-service/src/services/docker_runner.py
- services/deployer-service/src/services/github_client.py
- services/deployer-service/src/services/registry_client.py
- services/deployer-service/tests/test_health.py

### Service: API Gateway (8000)
- services/api-gateway/Dockerfile
- services/api-gateway/requirements.txt
- services/api-gateway/src/main.py
- services/api-gateway/src/config.py
- services/api-gateway/src/middleware/auth.py
- services/api-gateway/src/routes/health.py
- services/api-gateway/src/routes/proxy.py
- services/api-gateway/tests/test_health.py

### Service: App Management (8002)
- services/app-management/Dockerfile
- services/app-management/requirements.txt
- services/app-management/src/main.py
- services/app-management/src/config.py
- services/app-management/src/models/app.py
- services/app-management/src/routes/apps.py
- services/app-management/src/routes/health.py
- services/app-management/src/services/app_service.py
- services/app-management/tests/test_health.py

### Service: Deployment Service (8004)
- services/deployment-service/Dockerfile
- services/deployment-service/requirements.txt
- services/deployment-service/src/main.py
- services/deployment-service/src/config.py
- services/deployment-service/src/k8s/client.py
- services/deployment-service/src/routes/deployments.py
- services/deployment-service/src/routes/health.py
- services/deployment-service/tests/test_health.py

### Service: Monitoring Service (8005)
- services/monitoring-service/Dockerfile
- services/monitoring-service/requirements.txt
- services/monitoring-service/alembic.ini
- services/monitoring-service/prometheus.yml
- services/monitoring-service/src/main.py
- services/monitoring-service/src/config.py
- services/monitoring-service/src/db.py
- services/monitoring-service/src/models/log_entry.py
- services/monitoring-service/src/models/metric.py
- services/monitoring-service/src/routes/health.py
- services/monitoring-service/src/routes/logs.py
- services/monitoring-service/src/routes/metrics.py
- services/monitoring-service/src/services/auth_client.py
- services/monitoring-service/src/services/docker_collector.py
- services/monitoring-service/src/services/log_collector.py
- services/monitoring-service/src/services/scheduler.py
- services/monitoring-service/tests/test_docker_collector.py
- services/monitoring-service/tests/test_metrics_route.py
- services/monitoring-service/grafana/dashboards/minipaas.json
- services/monitoring-service/grafana/provisioning/dashboards/dashboard.yml
- services/monitoring-service/grafana/provisioning/datasources/prometheus.yml

### Shared Python Library
- shared/python/pyproject.toml
- shared/python/cloudoku_common/__init__.py
- shared/python/cloudoku_common/auth.py
- shared/python/cloudoku_common/config.py
- shared/python/cloudoku_common/logging.py

### Test Applications
- good-deployable-test/app.py
- good-deployable-test/Dockerfile
- good-deployable-test/README.md

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Total Services | 9 |
| GitHub Workflows | 10 |
| Documentation Files | 6 |
| Scripts | 4 |
| Dockerfiles | 9 |
| Python Source Files | ~60 |
| Frontend Components | ~20 |
| Kubernetes YAML Files | 8 |

---

## Conclusion

The MiniPaaS project demonstrates a comprehensive implementation of DevSecOps practices:

1. **Security Integrated Throughout Pipeline**: From code commit to deployment, security is checked at every stage
2. **Multi-layer Security Scanning**: Trivy, ClamAV, YARA, TruffleHog, and Dockle provide defense in depth
3. **Automated Security Gates**: CRITICAL CVEs automatically block deployment
4. **Infrastructure as Code**: Kubernetes configurations with Kustomize
5. **Comprehensive Testing**: pytest for all services
6. **Code Quality**: Ruff linting, SonarQube integration
7. **Secret Management**: Kubernetes secrets + environment variables

The project structure shows a mature microservices architecture with clear separation of concerns and strong security focus.