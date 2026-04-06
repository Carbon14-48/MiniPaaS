# MiniPaas - Mini Heroku-like PaaS

A lightweight Platform-as-a-Service that allows developers to deploy applications by simply pushing their code. Built with microservices architecture and DevSecOps practices.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     API Gateway (FastAPI)                    │
│              Rate Limiting | Auth | Routing                  │
└──┬──────────┬──────────┬──────────┬──────────┬──────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐
│ Auth │ │ App Mgr│ │Build │ │ Deploy   │ │ Monitor  │
│ Svc  │ │ Svc    │ │ Svc  │ │ Svc      │ │ Svc      │
└──────┘ └────────┘ └──────┘ └──────────┘ └──────────┘
                                                    │
                                         ┌──────────▼──────────┐
                                         │  Security Scanner   │
                                         │  (Trivy/SonarQube)  │
                                         └─────────────────────┘
```

## Microservices

| Service | Description | Tech |
|---------|-------------|------|
| `services/api-gateway` | Entry point, routing, rate limiting | FastAPI |
| `services/auth-service` | JWT auth, user management | FastAPI + PostgreSQL |
| `services/app-management` | App CRUD, config management | FastAPI + PostgreSQL |
| `services/build-service` | Git clone, Docker build, registry | FastAPI + Docker |
| `services/deployment-service` | K8s deployment, scaling, URLs | FastAPI + K8s client |
| `services/monitoring-service` | Logs, metrics, health checks | FastAPI + Prometheus |
| `services/security-scanner` | Code & image vulnerability scanning | FastAPI + Trivy |
| `frontend` | React dashboard | React + Tailwind |

## Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd MiniPaaS

# Run setup script
./scripts/setup.sh

# Start all services locally
./scripts/dev.sh

# Run all tests
./scripts/test-all.sh
```

## DevSecOps Pipeline

```
Push → Build → Test → Security Scan (Trivy + SonarQube) → Deploy to K8s
```

## Documentation

- [Architecture](docs/architecture.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)
- [Security](docs/security.md)
- [API Reference](docs/api/)

## License

MIT
