# Deployer Service

The Deployer Service is the central orchestration layer of MiniPaaS, providing end-to-end deployment management from GitHub repository to running container.

## Overview

The Deployer Service serves as the bridge between the frontend and the backend microservices, handling:

- **Deployment Lifecycle Management**: Create, start, stop, restart, and delete deployments
- **GitHub Integration**: List repositories and branches from the user's GitHub account
- **Container Management**: Control Docker containers (run, stop, start, logs)
- **Port Allocation**: Automatically assigns ports in the 30000-40000 range
- **Status Tracking**: Real-time deployment status updates

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend (React)                                 │
│                    Dashboard → Deployments → Repositories                     │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      │ HTTP/REST (Bearer Token)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Deployer Service (8008)                              │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                         Routes Layer                                    │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐│   │
│  │  │  /deployments   │  │     /repos     │  │       /health          ││   │
│  │  │  • POST /       │  │  • GET /       │  │  • GET /health         ││   │
│  │  │  • GET /        │  │                 │  └─────────────────────────┘│   │
│  │  │  • GET /{id}    │  │                 │                           │   │
│  │  │  • DELETE /{id} │  │                 │                           │   │
│  │  │  • POST /{id}/  │  │                 │                           │   │
│  │  │      stop/start/ │  │                 │                           │   │
│  │  │      restart     │  │                 │                           │   │
│  │  │  • GET /{id}/   │  │                 │                           │   │
│  │  │      logs        │  │                 │                           │   │
│  │  └─────────────────┘  └─────────────────┘                              │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                      │                                        │
│                                      ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                      Service Layer                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │ auth_client  │  │build_client │  │registry_    │                │   │
│  │  │              │  │              │  │client       │                │   │
│  │  │ verify_token │  │trigger_build│  │             │                │   │
│  │  │ get_user_info│  │get_build_   │  │             │                │   │
│  │  │              │  │status       │  │             │                │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │   │
│  │                                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐                                  │   │
│  │  │github_client│  │docker_runner│                                  │   │
│  │  │              │  │              │                                  │   │
│  │  │get_user_    │  │run_container│                                  │   │
│  │  │repos        │  │stop_        │                                  │   │
│  │  │get_repo_    │  │start_       │                                  │   │
│  │  │branches     │  │restart_     │                                  │   │
│  │  │             │  │remove_      │                                  │   │
│  │  │             │  │get_logs     │                                  │   │
│  │  └──────────────┘  └──────────────┘                                  │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                      │                                        │
│                                      ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                      Data Layer                                         │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │                    Deployment Model                               │  │   │
│  │  │  id, user_id, app_name, repo_url, branch, status              │  │   │
│  │  │  build_job_id, image_tag, image_url                            │  │   │
│  │  │  container_id, host_port, container_url                        │  │   │
│  │  │  build_logs, error_message, is_active                          │  │   │
│  │  │  created_at, updated_at, started_at, stopped_at                │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  │                           │                                              │   │
│  │                           ▼                                              │   │
│  │                    PostgreSQL                                           │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Auth Service   │     │  Build Service  │     │ Registry Service│
│    (8001)      │     │    (8003)       │     │    (8007)       │
│                 │     │                 │     │                 │
│ • JWT verify    │     │ • Git clone    │     │ • Image info    │
│ • User info     │     │ • Docker build │     │                 │
│ • GitHub token  │     │ • Security scan│     │                 │
└─────────────────┘     │ • Push image   │     └─────────────────┘
                        └─────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────┐
                        │  Security Scanner  │
                        │      (8006)        │
                        │                    │
                        │ • CVE scanning     │
                        │ • Malware detection│
                        │ • Secret detection │
                        └─────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────┐
                        │    Docker Daemon    │
                        │                     │
                        │ • Build images      │
                        │ • Run containers    │
                        │ • Container logs    │
                        └─────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────┐
                        │   Docker Registry   │
                        │      (:5000)        │
                        │                     │
                        │ • Image storage    │
                        │ • Image retrieval  │
                        └─────────────────────┘
```

## Deployment Lifecycle

```
┌─────────────┐
│   PENDING   │ ← Initial state when deployment is created
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  BUILDING   │ ← Triggering build pipeline
└──────┬──────┘
       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
┌─────────────┐                       ┌─────────────┐
│  BLOCKED    │                       │   FAILED    │
│ (Security   │                       │ (Build      │
│  policy     │                       │  error)     │
│  violation) │                       └─────────────┘
└─────────────┘
       │
       │ (if build succeeds)
       ▼
┌─────────────┐
│  DEPLOYING  │ ← Starting container
└──────┬──────┘
       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
┌─────────────┐                       ┌─────────────┐
│  RUNNING    │                       │   FAILED    │
│ (Container  │                       │ (Container  │
│  running)   │                       │  start      │
└──────┬──────┘                       │  error)     │
       │                              └─────────────┘
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   STOPPED   │────►│   RUNNING   │────►│  RESTARTING │
│ (Container  │     │ (Container  │     │ (Restarting │
│  stopped)   │     │  running)   │     │  container) │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Endpoints

### Deployment Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `POST` | `/deployments/` | Create new deployment | Yes |
| `GET` | `/deployments/` | List user's deployments | Yes |
| `GET` | `/deployments/{id}` | Get deployment details | Yes |
| `DELETE` | `/deployments/{id}` | Delete deployment (stop + deactivate) | Yes |
| `POST` | `/deployments/{id}/stop` | Stop running container | Yes |
| `POST` | `/deployments/{id}/start` | Start stopped container | Yes |
| `POST` | `/deployments/{id}/restart` | Restart container | Yes |
| `GET` | `/deployments/{id}/logs` | Get build/container logs | Yes |

### GitHub Integration Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/repos/` | List user's GitHub repositories | Yes |
| `GET` | `/repos/{owner}/{repo}/branches` | List repository branches | Yes |

### Health Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/health` | Service health check | No |

## API Reference

### Create Deployment

**POST** `/deployments/`

Request:
```json
{
  "repo_url": "https://github.com/username/repository",
  "branch": "main",
  "app_name": "my-awesome-app"
}
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 1,
  "app_name": "my-awesome-app",
  "repo_url": "https://github.com/username/repository",
  "branch": "main",
  "status": "running",
  "build_job_id": "...",
  "image_tag": "user1/my-awesome-app:v1",
  "image_url": "localhost:5000/user1/my-awesome-app:v1",
  "container_id": "abc123...",
  "host_port": 30001,
  "container_url": "http://localhost:30001",
  "error_message": null,
  "build_logs": "...",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:31:00Z",
  "started_at": "2024-01-15T10:31:00Z"
}
```

### List Deployments

**GET** `/deployments/`

Response:
```json
{
  "deployments": [...],
  "total": 5
}
```

### List GitHub Repositories

**GET** `/repos/`

Query Parameters:
- `page` (default: 1)
- `per_page` (default: 30, max: 100)

Response:
```json
[
  {
    "id": 123456789,
    "name": "my-project",
    "full_name": "username/my-project",
    "description": "A cool project",
    "private": false,
    "html_url": "https://github.com/username/my-project",
    "default_branch": "main",
    "updated_at": "2024-01-15T10:30:00Z",
    "language": "Python"
  }
]
```

### List Branches

**GET** `/repos/{owner}/{repo}/branches`

Response:
```json
[
  {
    "name": "main",
    "commit_sha": "abc123...",
    "protected": true
  },
  {
    "name": "feature-branch",
    "commit_sha": "def456...",
    "protected": false
  }
]
```

### Get Logs

**GET** `/deployments/{id}/logs?tail=100`

Response:
```json
{
  "logs": "Container log output...",
  "source": "container"
}
```

Possible sources: `build`, `container`, `none`

## Authentication Contract

All protected endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

The Deployer Service validates tokens by calling the Auth Service:

```
Deployer → GET /auth/me (with Bearer token) → Auth Service
```

### Token Validation Flow

```
1. Client sends request with Authorization: Bearer <token>
   ↓
2. Deployer extracts token from header
   ↓
3. Deployer calls auth-service:8001/auth/me
   ↓
4. Auth Service returns user ID if valid
   ↓
5. Deployer queries deployments WHERE user_id = <id>
   ↓
6. Response returned to client
```

### GitHub Token Retrieval

To access GitHub repositories, the Deployer Service retrieves the stored GitHub OAuth token:

```
Deployer → GET /auth/github-token (with Bearer token) → Auth Service
```

This requires the user to have logged in via GitHub OAuth.

## Docker Container Management

### Port Allocation

The service allocates ports from the range 30000-40000:
- Checks currently used ports
- Finds next available port
- Prevents port conflicts

### Container Naming

Containers are named following the pattern: `minipaas-{user_id}-{app_name}`

Example: `minipaas-1-my-awesome-app`

### Container Labels

All containers are labeled for tracking:
```yaml
minipaas: "true"
user_id: "1"
app_name: "my-awesome-app"
```

### Container Policies

- **Restart Policy**: `unless-stopped` - Container restarts automatically unless explicitly stopped
- **Network**: Default bridge network
- **Ports**: Single port mapping (container port 8000 → host port 30000+)

### Image Pull Strategy

When starting a container:
1. Check if image exists locally
2. If not found, pull from local Docker registry (`localhost:5000`)
3. If pull fails, throw error

## Configuration

### Environment Variables

Create a `.env` file in the service directory:

```env
# Service Configuration
SERVICE_PORT=8008
ENV=development

# Auth Service (for token validation)
AUTH_SERVICE_URL=http://localhost:8001

# Build Service (for triggering builds)
BUILD_SERVICE_URL=http://localhost:8003

# Registry Service (for image info)
REGISTRY_SERVICE_URL=http://localhost:8007

# Database
DATABASE_URL=postgresql://minipaas:minipaas@localhost:5432/minipaas

# Docker (for container management)
DOCKER_HOST=unix:///var/run/docker.sock
```

### Docker Compose Configuration

```yaml
deployer-service:
  build: ./services/deployer-service
  ports:
    - "8008:8000"
  env_file:
    - .env
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  depends_on:
    - auth-service
    - build-service
    - registry-service
    - postgres
```

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

### Common Errors

| Status Code | Detail | Cause |
|------------|--------|-------|
| 401 | Missing Authorization header | No Bearer token provided |
| 401 | Invalid Authorization header format | Malformed header |
| 401 | Token invalide ou expire | JWT expired or invalid |
| 404 | Deployment not found | Invalid deployment ID |
| 400 | No image available | Attempting to start without built image |
| 503 | Auth service unreachable | auth-service down |
| 500 | Internal server error | Unexpected error |

### Error States

The `error_message` field in deployment responses contains human-readable error details:

| Scenario | error_message |
|----------|---------------|
| Security scan blocked | "Security scan blocked: X CRITICAL, Y HIGH vulnerabilities found" |
| Build failed | "Build failed" or specific error from build-service |
| Container start failed | "Container start failed: <docker error>" |

## Local Development

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL running locally
- All dependent services (auth, build, registry)

### Setup

```bash
# 1. Navigate to service directory
cd services/deployer-service

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cat > .env << EOF
SERVICE_PORT=8008
ENV=development
AUTH_SERVICE_URL=http://localhost:8001
BUILD_SERVICE_URL=http://localhost:8003
REGISTRY_SERVICE_URL=http://localhost:8007
DATABASE_URL=postgresql://minipaas:minipaas@localhost:5432/minipaas
EOF

# 5. Run database migrations (if using Alembic)
alembic upgrade head

# 6. Start the service
uvicorn src.main:app --reload --port 8008
```

### Testing

```bash
# With pytest
pytest tests/

# With pytest and coverage
pytest --cov=src tests/

# Manual API testing
curl http://localhost:8008/health
```

### Service Dependencies

The Deployer Service requires these services to be running:

1. **auth-service** (port 8001) - JWT validation
2. **build-service** (port 8003) - Build triggering
3. **registry-service** (port 8007) - Image information
4. **PostgreSQL** (port 5432) - Deployment storage
5. **Docker Daemon** - Container management
6. **Docker Registry** (port 5000) - Image storage

## Database Schema

### deployments Table

```sql
CREATE TABLE deployments (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    app_name VARCHAR(255) NOT NULL,
    repo_url VARCHAR(500) NOT NULL,
    branch VARCHAR(255) DEFAULT 'main',
    
    -- Status tracking
    status VARCHAR(20) NOT NULL,  -- pending, building, deploying, running, stopped, failed, blocked
    
    -- Build information
    build_job_id VARCHAR(36),
    image_tag VARCHAR(500),
    image_url VARCHAR(500),
    
    -- Container information
    container_id VARCHAR(255),
    container_port INTEGER,
    host_port INTEGER,
    container_url VARCHAR(500),
    
    -- Logs and errors
    build_logs TEXT,
    deploy_logs TEXT,
    error_message TEXT,
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    stopped_at TIMESTAMP
);

CREATE INDEX ix_deployments_user_id ON deployments(user_id);
CREATE INDEX ix_deployments_status ON deployments(status);
```

## Security Considerations

### Authentication
- All deployment endpoints require valid JWT
- Tokens are validated against auth-service on every request
- Expired tokens result in 401 response

### Authorization
- Users can only access their own deployments
- Deployment queries are filtered by user_id from validated token

### Docker Security
- Containers run with labels for tracking
- Port range is restricted (30000-40000)
- Container names are predictable but scoped to user

### Secrets
- GitHub OAuth tokens stored encrypted in auth-service
- Database credentials via environment variables
- No secrets stored in deployment records

## Monitoring

### Health Check

```bash
curl http://localhost:8008/health
```

Response:
```json
{
  "status": "healthy",
  "service": "deployer-service"
}
```

### Container Status Tracking

The service periodically checks container status and updates deployment records:
- Running containers: status = "running"
- Stopped/Exited containers: status = "stopped"
- Missing containers: status = "stopped"

## Troubleshooting

### Common Issues

**"Missing Authorization header"**
- Ensure frontend is sending Bearer token
- Check token is not expired

**"Image not found"**
- Verify build completed successfully
- Check image exists in Docker daemon or registry

**"Container start failed"**
- Check Docker daemon is running
- Verify port 30000-40000 is available
- Check container logs for errors

**"Auth service unreachable"**
- Verify auth-service is running on port 8001
- Check network connectivity between services

### Debug Mode

Enable debug logging in development:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- [ ] WebSocket support for real-time deployment status
- [ ] Deployment scaling (multiple replicas)
- [ ] Custom domain support
- [ ] SSL/TLS termination
- [ ] Resource limits (CPU, memory)
- [ ] Deployment rollback capability
- [ ] Deployment history and versioning
- [ ] Webhook notifications
- [ ] Deployment environment variables management
- [ ] GitHub Actions integration

## License

MIT License - See [../../LICENSE](../../LICENSE) for details.
