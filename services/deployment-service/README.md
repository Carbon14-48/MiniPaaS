# Deployment Service

> **Status:** 🔧 STUB - NOT YET IMPLEMENTED
> **Note:** Container management is currently handled by the deployer-service using Docker. This service is planned for future Kubernetes-based deployments.

## Purpose

The Deployment Service is designed for:
- Kubernetes-based container orchestration
- Multi-container application support
- Auto-scaling based on load
- Rolling deployments and rollbacks
- Ingress management and public URLs
- SSL/TLS certificate management

## Planned Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/deployments` | Create Kubernetes deployment |
| `GET` | `/deployments` | List all deployments |
| `GET` | `/deployments/{id}` | Get deployment details |
| `PUT` | `/deployments/{id}` | Update deployment |
| `DELETE` | `/deployments/{id}` | Delete deployment |
| `POST` | `/deployments/{id}/scale` | Scale deployment replicas |
| `POST` | `/deployments/{id}/restart` | Rolling restart |
| `POST` | `/deployments/{id}/rollback` | Rollback to previous version |
| `GET` | `/deployments/{id}/logs` | Get deployment logs |
| `GET` | `/deployments/{id}/metrics` | Get deployment metrics |
| `POST` | `/domains` | Add custom domain |
| `GET` | `/health` | Health check |

## Current vs Future Architecture

### Current (Docker-based)
```
Deployer Service ──► Docker Daemon ──► Container
                     (port 30000+)
```

### Future (Kubernetes-based)
```
Deployment Service ──► Kubernetes API ──► Pods
                              │
                              ▼
                        Ingress Controller
                              │
                              ▼
                         Custom Domains
                         (SSL/TLS)
```

## Data Model (Planned)

```python
class Deployment:
    id: str
    user_id: int
    app_id: str
    image: str
    replicas: int
    port: int
    resources: Resources  # CPU, memory limits
    autoscaling: AutoscalingConfig
    domain: Optional[str]
    ssl_enabled: bool
    status: DeploymentStatus
    created_at: datetime
    updated_at: datetime
```

## Features

1. **Container Orchestration**
   - Multi-container pods
   - Init containers
   - Sidecar patterns

2. **Scaling**
   - Horizontal pod autoscaling (HPA)
   - Vertical pod autoscaling (VPA)
   - Custom metrics-based scaling

3. **Networking**
   - Ingress resources
   - Service mesh integration
   - Network policies

4. **Security**
   - Network policies
   - Pod security policies
   - Secrets management
   - RBAC

5. **Continuous Deployment**
   - Rolling updates
   - Blue-green deployments
   - Canary deployments
   - Rollback support

## Running Locally

```bash
cd services/deployment-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8004
```

## Future Enhancements

- [ ] Kubernetes client integration
- [ ] Ingress controller setup
- [ ] SSL certificate management
- [ ] Auto-scaling configuration
- [ ] Rolling update strategies
- [ ] Rollback automation
- [ ] Custom domain management

## Related Documentation

- [Main README](../../README.md)
- [Deployer Service](../deployer-service/README.md)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
