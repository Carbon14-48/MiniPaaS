# API Gateway

> **Status:** ✅ FUNCTIONAL - Unified entry point for MiniPaaS

## Purpose

The API Gateway serves as the unified entry point for all MiniPaaS client requests, providing:
- Centralized routing to backend services
- Request/response proxy forwarding
- Authentication middleware (JWT)
- CORS support

## Implemented Routes

| Path | Target Service | Internal Port | Description |
|------|----------------|---------------|-------------|
| `/api/auth/*` | auth-service | 8000 | Authentication routes |
| `/api/apps/*` | app-management | 8000 | App CRUD operations |
| `/api/deployments/*` | deployer-service | 8000 | Deployment management |
| `/api/builds/*` | build-service | 8002 | Build operations |
| `/api/registry/*` | registry-service | 8005 | Registry operations |
| `/api/monitoring/*` | monitoring-service | 8006 | Monitoring (logs, metrics, health) |
| `/api/scanner/*` | security-scanner | 8000 | Security scanning |

## Running Locally

```bash
cd services/api-gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

## Docker

The gateway is automatically built and started via docker-compose:

```bash
docker compose up -d api-gateway
```

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Proxy to auth service
curl http://localhost:8000/api/auth/

# Proxy to monitoring service
curl http://localhost:8000/api/monitoring/health

# Proxy to deployments
curl http://localhost:8000/api/deployments/
```

## Architecture

```
                    ┌─────────────┐
                    │   Client    │
                    └──────┬──────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   API Gateway :8000  │
                │                     │
                │  • Routing          │
                │  • CORS             │
                │  • Proxy Forward    │
                └──────────┬──────────┘
                           │
      ┌───────────┬────────┼────────┬───────────┐
      ▼           ▼        ▼        ▼           ▼
┌──────────┐┌────────┐┌─────────┐┌─────────┐┌──────────┐
│  Auth     ││ Deploy ││ Monitoring││ Registry ││  Build   │
│ :8000     ││ :8000  ││  :8006   ││ :8005   ││  :8002   │
└──────────┘└────────┘└──────────┘└─────────┘└──────────┘
```

## Environment Variables

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Service URLs (internal Docker)
AUTH_SERVICE_URL=http://auth-service:8000
APP_MANAGEMENT_SERVICE_URL=http://app-management:8000
BUILD_SERVICE_URL=http://build-service:8002
DEPLOYMENT_SERVICE_URL=http://deployment-service:8000
DEPLOYER_SERVICE_URL=http://deployer-service:8000
MONITORING_SERVICE_URL=http://monitoring-service:8006
SECURITY_SCANNER_URL=http://security-scanner:8000
REGISTRY_SERVICE_URL=http://registry-service:8005
```

## Related Documentation

- [Main README](../../README.md)
- [Architecture Documentation](../../docs/architecture.md)
