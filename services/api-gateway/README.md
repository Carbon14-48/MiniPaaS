# API Gateway

> **Status:** 🔧 STUB - NOT YET IMPLEMENTED
> **Note:** Currently, the frontend connects directly to services. This gateway is a future enhancement for unified API entry point.

## Purpose

The API Gateway serves as the unified entry point for all MiniPaaS client requests, providing:
- Centralized routing to backend services
- Rate limiting
- Request/response transformation
- Authentication middleware
- Load balancing

## Planned Endpoints

| Method | Path | Target Service | Description |
|--------|------|----------------|-------------|
| `GET` | `/health` | - | Health check |
| `GET` | `/api/apps` | app-management | List apps |
| `POST` | `/api/apps` | app-management | Create app |
| `GET` | `/api/apps/{id}` | app-management | Get app |
| `DELETE` | `/api/apps/{id}` | app-management | Delete app |
| `GET` | `/api/deployments` | deployer-service | List deployments |
| `POST` | `/api/deployments` | deployer-service | Create deployment |
| `GET` | `/api/deployments/{id}` | deployer-service | Get deployment |
| `POST` | `/api/deployments/{id}/stop` | deployer-service | Stop deployment |
| `POST` | `/api/deployments/{id}/start` | deployer-service | Start deployment |
| `GET` | `/api/logs/{app_id}` | monitoring-service | Get logs |
| `GET` | `/api/auth/*` | auth-service | Authentication routes |

## Current Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ Direct connections (for now)
       ▼
┌─────────────┐     ┌─────────────┐
│ Auth Service│     │Deployer Svc │
│   (8001)  │     │   (8008)   │
└─────────────┘     └─────────────┘
```

## Future Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ API Gateway │     ┌─────────────┐     ┌─────────────┐
│   (8000)   │────►│ Auth Service│     │Deployer Svc │
│            │     │   (8001)   │     │   (8008)   │
│ Rate Limit │     └─────────────┘     └─────────────┘
│ Auth Check │
│  Routing   │     ┌─────────────┐     ┌─────────────┐
└─────────────┘────►│ App Mgmt   │────►│Monitoring   │
                    │   (8002)   │     │   (8005)   │
                    └─────────────┘     └─────────────┘
```

## Implementation Requirements

1. **Routing**: Proxy requests to appropriate backend services
2. **Rate Limiting**: Implement per-user rate limits
3. **Authentication**: Validate JWT tokens before proxying
4. **Logging**: Log all requests for audit trail
5. **CORS**: Handle cross-origin requests

## Running Locally

```bash
cd services/api-gateway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

## Future Enhancements

- [ ] Implement proxy forwarding
- [ ] Add rate limiting middleware
- [ ] Add authentication middleware
- [ ] Add request logging
- [ ] Add response caching
- [ ] Add circuit breaker pattern

## Related Documentation

- [Main README](../../README.md)
- [Architecture Documentation](../../docs/architecture.md)
