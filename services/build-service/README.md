# Build Service

MiniPaaS Build Service - transforms source code repositories into Docker container images through a secure CI/CD pipeline.

## Overview

The Build Service is responsible for:
- Validating user identity via auth-service
- Cloning GitHub repositories
- Detecting or generating Dockerfiles
- Building Docker images
- Running security scans on built images
- Pushing safe images to the registry
- Persisting build job history

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Build Service (8003)                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Routes Layer                                    │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐│   │
│  │  │   /build        │  │  /build/me     │  │       /health         ││   │
│  │  │  • POST /       │  │  • GET /       │  │  • GET /              ││   │
│  │  │  • GET /{id}   │  │                │  └─────────────────────────┘│   │
│  │  └─────────────────┘  └─────────────────┘                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                        │
│                                      ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Services Layer                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │ auth_client   │  │ git_service   │  │docker_service│           │   │
│  │  │              │  │              │  │              │           │   │
│  │  │ verify_token │  │ clone_repo   │  │detect_docker│           │   │
│  │  │              │  │cleanup_repo│  │file        │           │   │
│  │  │              │  │              │  │build_image │           │   │
│  │  └──────────────┘  └──────────────┘  └──────┬───────┘           │   │
│  │                                              │                      │   │
│  │                   ┌──────────────────────────┼──────────────────┐  │   │
│  │                   │                          ▼                  │  │   │
│  │  ┌──────────────┐│┌──────────────┐  ┌──────────────┐      │  │   │
│  │  │scanner_client│ ││registry_    │  │               │      │  │   │
│  │  │              │ ││client       │  │               │      │  │   │
│  │  │ scan_image  │ ││push_image  │  │               │      │  │   │
│  │  └──────────────┘│└──────────────┘  └──────────────┘      │  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Database Layer                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│  │
│  │  │                    BuildJob Model                                 ││  │
│  │  │  job_id, user_id, repo_url, app_name, branch, status         ││  │
│  │  │  image_tag, image_url, build_logs, scan_result               ││  │
│  │  └─────────────────────────────────────────────────────────────────┘│  │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
     ┌────────────────────────────────┼────────────────────────────────┐
     │                                │                                │
     ▼                                ▼                                ▼
┌─────────────┐            ┌─────────────┐            ┌─────────────┐
│Auth Service │            │  Security   │            │  Registry   │
│  (8001)    │            │  Scanner    │            │  Service    │
│             │            │  (8006)     │            │  (8007)    │
│ • JWT       │            │             │            │             │
│   Verify    │            │ • Trivy     │            │ • Image     │
│             │            │ • ClamAV    │            │   Tag/Push  │
│             │            │ • YARA      │            │             │
└─────────────┘            │ • Dockle    │            └─────────────┘
                           │ • TruffleHog│
                           └─────────────┘
                                      │
                                      ▼
                           ┌─────────────┐
                           │    GitHub    │
                           │    API       │
                           │              │
                           │ • Repository │
                           │   Access    │
                           └─────────────┘
```

## Build Pipeline

```
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
│ 1. Auth  │────►│ 2. Clone │────►│ 3. Detect │────►│ 4. Build │────►│ 5. Scan  │
│           │     │   Repo    │     │  Docker-  │     │   Image   │     │  Image   │
│ Verify    │     │           │     │    file   │     │           │     │           │
│ JWT       │     │ git clone │     │           │     │ docker    │     │ Trivy    │
│ token     │     │ --depth=1 │     │ Custom or │     │ build     │     │ ClamAV   │
│           │     │           │     │ generated │     │           │     │ YARA     │
└───────────┘     └───────────┘     └───────────┘     └───────────┘     └─────┬─────┘
                                                                              │
                         ┌─────────────────────────────────────────────────────┼─────┐
                         │                                                     │     │
                         ▼                                                     ▼     ▼
                   ┌───────────┐                                        ┌───────────┐
                   │  PASS     │                                        │  BLOCKED  │
                   │ (No crit) │                                        │(Critical  │
                   │           │                                        │  CVE)     │
                   │ Continue  │                                        │          │
                   └─────┬─────┘                                        │ Stop here │
                         │                                               │ Don't    │
                         │                                               │ push     │
                         ▼                                               └───────────┘
                   ┌───────────┐
                   │ 6. Push   │
                   │   to      │
                   │ Registry  │
                   │           │
                   │ docker    │
                   │ tag + push│
                   └─────┬─────┘
                         │
                         ▼
                   ┌───────────┐
                   │  SUCCESS  │
                   │ Job saved │
                   │ to DB     │
                   └───────────┘
```

## Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `POST` | `/build` | Trigger full build pipeline | Yes |
| `GET` | `/build/{job_id}` | Get build status/details (owner only) | Yes |
| `GET` | `/build/me` | List current user's build history | Yes |
| `GET` | `/build/user/{user_id}` | Legacy endpoint (same-user only) | Yes |
| `GET` | `/health` | Health check | No |

## API Reference

### Trigger Build

**POST** `/build`

Request:
```json
{
  "repo_url": "https://github.com/username/repository",
  "branch": "main",
  "app_name": "my-app"
}
```

Response (Success):
```json
{
  "status": "success",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "image_tag": "user1/my-app:v1",
  "image_url": "localhost:5000/user1/my-app:v1",
  "build_logs": "Step 1/5 : FROM python:3.12-slim...",
  "scan_result": {
    "status": "PASS",
    "verdict": "policy_passed",
    "severity_breakdown": {
      "critical": 0,
      "high": 0,
      "medium": 2,
      "low": 5
    },
    "policy_passed": true,
    "signed": false,
    "warnings": [...]
  }
}
```

Response (Blocked):
```json
{
  "status": "blocked",
  "job_id": "550e8400-e29b-41d4-a716-446655440001",
  "image_tag": "user1/my-app:v2",
  "build_logs": "...",
  "reason": "Security policy violation: 3 CRITICAL CVE(s) found",
  "scan_result": {
    "status": "BLOCKED",
    "verdict": "policy_violation",
    "severity_breakdown": {
      "critical": 3,
      "high": 5,
      "medium": 10,
      "low": 20
    },
    "policy_passed": false,
    "block_reason": "3 CRITICAL CVE(s) found"
  }
}
```

### Get Build Status

**GET** `/build/{job_id}`

Response:
```json
{
  "status": "success",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "image_tag": "user1/my-app:v1",
  "image_url": "localhost:5000/user1/my-app:v1",
  "build_logs": "...",
  "scan_result": {...}
}
```

### List My Builds

**GET** `/build/me`

Response:
```json
[
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "app_name": "my-app",
    "status": "success",
    "image_tag": "user1/my-app:v1",
    "created_at": "2024-01-15T10:30:00Z",
    "finished_at": "2024-01-15T10:31:30Z"
  },
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440001",
    "app_name": "my-app",
    "status": "blocked",
    "image_tag": "user1/my-app:v2",
    "created_at": "2024-01-15T11:00:00Z",
    "finished_at": "2024-01-15T11:01:00Z"
  }
]
```

## Dockerfile Detection

The build service can handle repositories with or without Dockerfiles:

### Custom Dockerfile (User Provided)

If a `Dockerfile` exists in the repository root, it's used as-is.

Supported languages:
- Python
- Node.js
- Java/Maven
- Go
- Ruby
- PHP
- Any custom setup

### Auto-Generated Dockerfile

If no Dockerfile exists, the service detects the language and generates one:

| Detected | Generated Dockerfile |
|----------|---------------------|
| Python (`requirements.txt` or `.py` files) | `python:3.12-slim` + pip install |
| Node.js (`package.json`) | `node:20-alpine` + npm install |
| Java (`pom.xml`) | Multi-stage Maven build |

### Generated Dockerfile Examples

**Python:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Node.js:**
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["node", "index.js"]
```

**Java:**
```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
```

## Image Tagging

Built images are tagged following the pattern:
```
user{user_id}/{app_name}:v{build_number}
```

Examples:
- `user1/my-app:v1`
- `user1/my-app:v2`
- `user1/my-app:v3`

The build number increments based on successful builds for the same app.

## Authentication Contract

This service does **not** decode JWT locally. It delegates token validation to auth-service:

```
Build Service → GET /auth/me (Bearer token) → Auth Service
```

### Token Validation Flow

```
1. Client sends request with Authorization: Bearer <token>
   ↓
2. Build service extracts token from header
   ↓
3. Build service calls auth-service:8001/auth/me
   ↓
4. Auth service returns user info including ID
   ↓
5. Build service uses user ID for image tagging and DB records
   ↓
6. Response returned to client
```

## Security Scanning

Before pushing images to the registry, all builds are scanned by the security-scanner service.

### Scanning Process

1. **Trivy CVE Scan** - Scans for known vulnerabilities in OS packages and dependencies
2. **ClamAV Malware Scan** - Scans container filesystem for malware
3. **YARA Custom Rules** - Scans for webshells, reverse shells, and other threats
4. **TruffleHog Secrets Scan** - Scans for exposed API keys, passwords, and secrets
5. **Dockle CIS Benchmark** - Checks Docker image best practices

### Blocking Policy

| Severity | Action |
|----------|--------|
| CRITICAL | BLOCK - Image not pushed |
| HIGH | WARN - Image pushed with warning |
| MEDIUM | WARN - Image pushed with warning |
| LOW | WARN - Image pushed with warning |

### Scan Result Format

```json
{
  "status": "PASS" | "WARN" | "BLOCKED",
  "verdict": "policy_passed" | "advisory_warning" | "policy_violation",
  "severity_breakdown": {
    "critical": 0,
    "high": 5,
    "medium": 10,
    "low": 20
  },
  "policy_passed": true | false,
  "signed": true | false,
  "warnings": [
    {"type": "high_vulnerabilities", "count": 5, "message": "5 HIGH severity CVE(s) found..."}
  ],
  "block_reason": "...",
  "details": {...}
}
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
# Service Configuration
SERVICE_PORT=8003
ENV=development

# Auth Service (for token validation)
AUTH_SERVICE_URL=http://localhost:8001

# Security Scanner (for image scanning)
SCANNER_SERVICE_URL=http://localhost:8006

# Registry Service (for image push)
REGISTRY_SERVICE_URL=http://localhost:8007

# Database
DATABASE_URL=postgresql://minipaas:minipaas@localhost:5432/minipaas

# Build Settings
BUILD_WORKDIR=/tmp/builds
MAX_BUILD_TIMEOUT=300
```

### Docker Compose

```yaml
build-service:
  build: ./services/build-service
  ports:
    - "8003:8000"
  env_file:
    - .env
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
    - /tmp/builds:/tmp/builds
  depends_on:
    - auth-service
    - security-scanner
    - registry-service
    - postgres
```

## Local Development

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL
- All dependent services running

### Setup

```bash
# Navigate to service directory
cd services/build-service

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
AUTH_SERVICE_URL=http://localhost:8001
SCANNER_SERVICE_URL=http://localhost:8006
REGISTRY_SERVICE_URL=http://localhost:8007
DATABASE_URL=postgresql://minipaas:minipaas@localhost:5432/minipaas
BUILD_WORKDIR=/tmp/builds
MAX_BUILD_TIMEOUT=300
ENV=development
EOF

# Run database migrations
alembic upgrade head

# Start the service
uvicorn src.main:app --reload --port 8003
```

### Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=src tests/

# Manual API test
curl -X POST http://localhost:8003/build \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "repo_url": "https://github.com/username/repo",
    "branch": "main",
    "app_name": "test-app"
  }'
```

## Database Schema

### build_jobs Table

```sql
CREATE TYPE buildstatus AS ENUM (
    'pending',
    'running',
    'success',
    'failed',
    'blocked'
);

CREATE TABLE build_jobs (
    job_id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    repo_url VARCHAR(500) NOT NULL,
    app_name VARCHAR(255) NOT NULL,
    branch VARCHAR(255) NOT NULL DEFAULT 'main',
    status buildstatus NOT NULL DEFAULT 'pending',
    image_tag VARCHAR(500),
    image_url VARCHAR(500),
    build_logs TEXT,
    scan_result JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP
);

CREATE INDEX ix_build_jobs_user_id ON build_jobs(user_id);
CREATE INDEX ix_build_jobs_status ON build_jobs(status);
CREATE INDEX ix_build_jobs_created_at ON build_jobs(created_at);
```

## Security Notes

- All endpoints (except `/health`) require valid JWT
- Users can only access their own builds
- Legacy route `/build/user/{user_id}` enforces same-user access
- No Docker socket exposure to untrusted environments
- Build workspace cleaned after each build

## Troubleshooting

### Common Issues

**"Invalid Authorization header format"**
- Ensure header is: `Authorization: Bearer <token>`

**"Security scanner unreachable"**
- Verify security-scanner is running on port 8006
- Check network connectivity

**"Registry service injoignable"**
- Verify registry-service is running on port 8007
- Check Docker registry is running on port 5000

**"Impossible de détecter le langage"**
- Add `requirements.txt` (Python), `package.json` (Node.js), or `pom.xml` (Java)
- Or provide a Dockerfile in repository root

**"Docker build échoué"**
- Check Dockerfile syntax
- Verify dependencies in requirements.txt
- Check base image exists

## Future Enhancements

- [ ] Parallel build support
- [ ] Build caching
- [ ] Build cancellation
- [ ] Build artifact storage
- [ ] Custom build environments
- [ ] Multi-stage build support
- [ ] Build webhook notifications
- [ ] Build resource limits

## License

MIT License - See [../../LICENSE](../../LICENSE) for details.
