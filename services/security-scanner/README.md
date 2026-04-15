# Security Scanner — MiniPaaS Security Analysis Service

> **Status:** ✅ PRODUCTION READY
> **Current state:** Fully implemented multi-layer image security scanner
> **Policy:** Permissive mode (blocks CRITICAL CVEs only, warns on others)

## Quick Summary

The Security Scanner performs comprehensive analysis of Docker images before deployment:
- **Trivy** for CVE detection
- **ClamAV** for malware detection
- **YARA Rules** for custom threat patterns
- **TruffleHog** for secrets detection
- **Dockle** for CIS benchmark compliance

**Endpoint:** `POST /scans/image`

---

## Overview

The security-scanner is the gatekeeper of the MiniPaaS build pipeline. Every Docker image built by `build-service` must pass through this scanner before being pushed to the registry and deployed.

The scanner operates as a **synchronous policy enforcement point** — the build-service calls it, waits for the verdict, and blocks or proceeds accordingly.

---

## Architecture

```
build-service:8003
    │
    │  POST /scans/image { "image_tag": "user42/myapp:v1", "user_id": 42 }
    ▼
┌──────────────────────────────────────────────────────────────┐
│                    security-scanner:8006                     │
│                                                              │
│  1. Load image from local Docker daemon                      │
│           ↓                                                  │
│  2a. Trivy scan     → CVE report (OS + lang deps)          │
│  2b. ClamAV scan    → Malware signatures                    │
│  2c. YARA scan      → Custom container malware rules         │
│  2d. TruffleHog     → Secrets in layers + env vars          │
│  2e. Dockle scan    → CIS benchmark misconfigs               │
│           ↓                                                  │
│  3. Aggregate all results into unified report                 │
│           ↓                                                  │
│  4. Apply policy engine → PASS / WARN / BLOCK                │
│           ↓                                                  │
│  5. Return verdict + full details to build-service           │
└──────────────────────────────────────────────────────────────┘
    │
    │  ScanResult { status: "PASS" | "WARN" | "BLOCKED", ... }
    ▼
build-service decides: push to registry or abort build
```

---

## Tool Stack

| Tool | Purpose | Version |
|---|---|---|
| **Trivy** | CVE scanning (OS packages + language deps) | Latest |
| **ClamAV** | Signature-based malware detection | Latest |
| **YARA** | Custom container malware rule engine | Latest |
| **TruffleHog v3** | Secrets detection in image layers | Latest |
| **Dockle** | CIS Docker benchmark misconfiguration checks | Latest |
| **Docker SDK** | Image access via `/var/run/docker.sock` | Latest |

All tools are installed inside the scanner's Docker container at build time.

---

## Approved Base Image Allowlist

**Strict allowlist — only these base images are permitted:**

### Python
```
python:3.11-slim
python:3.12-slim
python:3.11-alpine
python:3.12-alpine
python:3.11-bookworm-slim
python:3.12-bookworm-slim
```

### Node.js
```
node:18-alpine
node:20-alpine
node:18-slim
node:20-slim
node:18-bookworm-slim
node:20-bookworm-slim
```

### Go
```
golang:1.21-alpine
golang:1.22-alpine
golang:1.21-slim
golang:1.22-slim
```

### Java / JVM
```
eclipse-temurin:8-jre-alpine
eclipse-temurin:8-jre-fips
eclipse-temurin:11-jre-alpine
eclipse-temurin:11-jre-fips
eclipse-temurin:17-jre-alpine
eclipse-temurin:17-jre-fips
eclipse-temurin:21-jre-alpine
eclipse-temurin:21-jre-fips
maven:3.9-eclipse-temurin-17
maven:3.9-eclipse-temurin-21
maven:3.11-eclipse-temurin-17
maven:3.11-eclipse-temurin-21
```

### Distroless (preferred for production)
```
gcr.io/distroless/python3-debian11
gcr.io/distroless/nodejs18-debian11
gcr.io/distroless/nodejs20-debian11
gcr.io/distroless/static-debian11
gcr.io/distroless/static-debian12
```

### Minimal / Alpine
```
alpine:3.18
alpine:3.19
alpine:3.20
```

### Debian Slim
```
debian:bookworm-slim
debian:bullseye-slim
debian:trixie-slim
```

### Ubuntu
```
ubuntu:22.04
ubuntu:24.04
ubuntu:24.10
```

### Common Services
```
nginx:alpine
nginx:1.25-alpine
redis:7-alpine
redis:7-bookworm
postgres:15-alpine
postgres:16-alpine
postgres:17-alpine
rabbitmq:3-management-alpine
```

### Blocked Base Images

Anything **NOT** on this list is immediately **BLOCKED**. Specifically blocked:
- `scratch` — no package manager, cannot be scanned
- `ubuntu:latest`, `ubuntu:20.04`, `ubuntu:21.04` — non-slim, unpredictable
- `debian:latest`, `debian:stable` — moving target
- `centos:*`, `rockylinux:*`, `fedora:*` — EOL risk, slow patches
- `busybox:*` — too minimal, no CVE database
- `amazoncorretto:*`, `openjdk:*` — use eclipse-temurin instead
- `python:*`, `node:*`, `golang:*` without slim/alpine suffix — large attack surface
- Any image with `latest` tag — non-deterministic
- Any image from untrusted registries (not Docker Hub, Google, Eclipse)

---

## Blocking Policy

### Hard Blocks (deployment REJECTED)

| Category | Condition | Action |
|---|---|---|
| **Base Image** | Not in approved allowlist | BLOCK |
| **Vulnerability** | Any CRITICAL CVE found | BLOCK |
| **Vulnerability** | Any HIGH CVE found | BLOCK |
| **Malware** | Any malware signature detected | BLOCK |
| **Secret** | Any secret detected in any layer | BLOCK |
| **Misconfiguration** | USER directive missing (runs as root) | BLOCK |
| **Misconfiguration** | `scratch` base image | BLOCK |

### Soft Warnings (deployment ALLOWED, user notified)

| Category | Condition | Action |
|---|---|---|
| **Vulnerability** | MEDIUM CVEs only | WARN |
| **Vulnerability** | LOW CVEs only | WARN |
| **Misconfiguration** | Privileged ports exposed (22, 3389) | WARN |
| **Misconfiguration** | `latest` tag used | WARN |

### Pass (deployment APPROVED)

| Condition | Action |
|---|---|
| Zero CRITICAL/HIGH CVEs | PASS |
| Zero malware | PASS |
| Zero secrets | PASS |
| Base image in allowlist | PASS |
| No root user misconfig | PASS |

---

## Custom YARA Rules

Located at `src/scanners/rules/` — custom rules targeting container-specific threats.

### Rule Categories

**1. Crypto Miners**
```
rules/crypto_miners.yara
- XMRig binary signatures
- Stratum protocol strings
- Mining pool URL patterns
- Crypto wallet address patterns in config
```

**2. Webshells**
```
rules/webshells.yara
- eval(base64_decode()) patterns
- system() / shell_exec() abuse
- Backdoor PHP shells (c99, r57, wso)
- JSP/ASP web shells
```

**3. Container Escape**
```
rules/container_escape.yara
- Host filesystem access patterns
- cgroup escape indicators
- nsenter / unshare abuse
- Docker socket abuse patterns
```

**4. Reverse Shells**
```
rules/reverse_shells.yara
- /dev/tcp/ patterns
- bash -i >& /dev/tcp/
- nc -e patterns
- Python/ruby/php reverse shell payloads
```

**5. Rootkits / Persistence**
```
rules/rootkits.yara
- Cron job anomalies
- systemd service injection
- SSH authorized_keys abuse
- LD_PRELOAD / etc/ld.so.preload patterns
```

**6. General Malicious**
```
rules/general_malware.yara
- Known backdoor binaries (patterns)
- Suspicious ELF headers
- Obfuscated shell scripts
```

---

## API Specification

### POST /scans/image

**Request:**
```json
{
  "image_tag": "user42/myapp:v1",
  "user_id": 42,
  "app_name": "myapp"
}
```

**Response — BLOCKED:**
```json
{
  "status": "BLOCKED",
  "verdict": "policy_violation",
  "image_tag": "user42/myapp:v1",
  "scan_duration_seconds": 34,
  "severity_breakdown": {
    "critical": 3,
    "high": 12,
    "medium": 45,
    "low": 120
  },
  "block_reason": "3 CRITICAL CVEs found",
  "policy_passed": false,
  "details": {
    "vulnerabilities": [
      {
        "id": "CVE-2024-3094",
        "severity": "CRITICAL",
        "package": "liblzma",
        "installed_version": "5.6.0",
        "fixed_version": "6.4",
        "description": "XZ Utils backdoor allowing remote code execution",
        "layer": "sha256:aabbcc..."
      }
    ],
    "malware": [
      {
        "rule": "crypto_miner_xmrig",
        "file": "/usr/bin/xmrig",
        "signature": "XMRig",
        "severity": "CRITICAL"
      }
    ],
    "secrets": [
      {
        "type": "aws_access_key",
        "file": "app/config.json",
        "line": 12,
        "description": "AWS Access Key ID detected"
      }
    ],
    "misconfigurations": [
      {
        "code": "DKR0001",
        "title": "USER directive not set",
        "severity": "CRITICAL",
        "description": "Container is running as root user"
      }
    ],
    "base_image": {
      "image": "python:3.11",
      "approved": false,
      "suggestion": "Use python:3.11-slim instead"
    }
  }
}
```

**Response — PASS:**
```json
{
  "status": "PASS",
  "verdict": "policy_passed",
  "image_tag": "user42/myapp:v1",
  "scan_duration_seconds": 28,
  "severity_breakdown": {
    "critical": 0,
    "high": 0,
    "medium": 3,
    "low": 47
  },
  "policy_passed": true,
  "details": {
    "vulnerabilities": [...],
    "malware": [],
    "secrets": [],
    "misconfigurations": [
      {
        "code": "DKR0005",
        "title": "Latest tag used in base image",
        "severity": "INFO",
        "description": "Base image uses 'latest' tag which is non-deterministic"
      }
    ],
    "base_image": {
      "image": "python:3.11-slim",
      "approved": true
    }
  }
}
```

**Response — WARN:**
```json
{
  "status": "WARN",
  "verdict": "advisory_warning",
  "image_tag": "user42/myapp:v1",
  "policy_passed": true,
  "warnings": [
    {
      "type": "medium_vulnerabilities",
      "count": 5,
      "message": "5 MEDIUM severity CVEs found — deployment allowed but review recommended"
    }
  ],
  "details": {...}
}
```

### GET /scans/{scan_id}

Returns cached scan result for a previously scanned image.

### GET /scans/history/{user_id}

Returns scan history for a user (paginated).

### GET /health

```json
{
  "status": "healthy",
  "service": "security-scanner",
  "tools": {
    "trivy": "available",
    "clamav": "available",
    "yara": "available",
    "trufflehog": "available",
    "dockle": "available"
  }
}
```

---

## File Structure

```
services/security-scanner/
├── src/
│   ├── main.py                          # FastAPI app entry point
│   ├── config.py                        # Pydantic settings
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py                    # GET /health
│   │   └── scans.py                     # POST /scans/image, GET /scans/{id}
│   ├── scanners/
│   │   ├── __init__.py
│   │   ├── trivy_scanner.py             # CVE scanning via Trivy
│   │   ├── clamav_scanner.py            # Malware scanning via ClamAV
│   │   ├── yara_scanner.py              # Custom YARA rule scanning
│   │   ├── trufflehog_scanner.py        # Secrets detection
│   │   ├── dockle_scanner.py            # CIS benchmark misconfigs
│   │   └── base_image_checker.py        # Allowlist enforcement
│   ├── scanners/rules/                  # Custom YARA rules
│   │   ├── crypto_miners.yara
│   │   ├── webshells.yara
│   │   ├── container_escape.yara
│   │   ├── reverse_shells.yara
│   │   ├── rootkits.yara
│   │   └── general_malware.yara
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_loader.py               # Extract image layers for scanning
│   │   ├── policy_engine.py             # Apply blocking policy
│   │   └── result_aggregator.py          # Merge all scan results
│   ├── models/
│   │   ├── __init__.py
│   │   ├── scan_request.py              # Pydantic request models
│   │   ├── scan_result.py               # Pydantic response models
│   │   └── findings.py                  # Vulnerability, Secret, Malware models
│   └── db.py                            # Optional: cache scan results in PostgreSQL
│   ├── migrations/                      # Alembic migrations (if using DB)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_trivy_scanner.py
│   │   ├── test_clamav_scanner.py
│   │   ├── test_yara_scanner.py
│   │   ├── test_trufflehog_scanner.py
│   │   ├── test_base_image_checker.py
│   │   ├── test_policy_engine.py
│   │   ├── test_result_aggregator.py
│   │   └── test_routes.py
│   ├── Dockerfile                       # Multi-stage with all tools
│   ├── requirements.txt
│   ├── .env.example
│   ├── README.md                        # This file
│   └── alembic.ini
```

---

## Dockerfile Changes

The current Dockerfile uses `python:3.12-slim`. The new one needs multi-stage build:

```dockerfile
# Stage 1: Builder — install all scanning tools
FROM python:3.12-slim AS builder

# Install system dependencies for all tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    libclamav9 \
    clamav \
    clamav-daemon \
    build-essential \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Trivy
RUN wget -qO- https://github.com/aquasecurity/trivy/releases/download/v0.56.0/trivy_0.56.0_Linux-64bit.tar.gz \
    | tar -xzf - -C /usr/local/bin trivy

# Update ClamAV database
RUN freshclam

# Install YARA (compile from source for Python bindings)
RUN pip install yara-python

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    clamav \
    libclamav9 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/bin/trivy /usr/local/bin/trivy
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /var/lib/clamav /var/lib/clamav
COPY --from=builder /etc/clamav /etc/clamav

# Copy YARA rules
COPY src/scanners/rules/ /rules/

WORKDIR /app
COPY . .
EXPOSE 8000

# Pre-update ClamAV DB at startup (background)
CMD ["sh", "-c", "freshclam & uvicorn src.main:app --host 0.0.0.0 --port 8000"]
```

---

## Requirements.txt Additions

```
# Existing
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.10.0
pydantic-settings>=2.6.0
requests>=2.32.0
python-dotenv>=1.0.0
pika>=1.3.0
pytest>=8.3.0
httpx>=0.28.0

# New — scanning tools
docker>=7.1.0                    # Docker SDK for image access
yara-python>=4.5.0              # YARA rule engine Python bindings
clamd>=1.4.0                    # ClamAV Python client (or use subprocess)

# No new dependencies for Trivy/TruffleHog/Dockle —
# they are called as CLI subprocesses, not Python libraries
```

---

## Docker Compose Changes

Add to root `docker-compose.yml`:

```yaml
security-scanner:
  build: ./services/security-scanner
  ports:
    - "8006:8000"
  env_file: .env
  depends_on:
    - rabbitmq
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock  # Required for image access
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
- Rewrite `src/config.py` with new settings
- Rewrite `src/routes/scans.py` with new Pydantic models
- Implement `src/services/image_loader.py` (extract image for scanning)
- Implement `src/scanners/base_image_checker.py` (allowlist enforcement)
- Write custom YARA rules in `src/scanners/rules/`
- Update Dockerfile with all tool installations
- Update `requirements.txt`
- Update `docker-compose.yml`

### Phase 2: Individual Scanners
- Implement `src/scanners/trivy_scanner.py`
- Implement `src/scanners/clamav_scanner.py`
- Implement `src/scanners/yara_scanner.py`
- Implement `src/scanners/trufflehog_scanner.py`
- Implement `src/scanners/dockle_scanner.py`

### Phase 3: Aggregation & Policy
- Implement `src/services/result_aggregator.py`
- Implement `src/services/policy_engine.py`

### Phase 4: Integration & Testing
- Update `build-service/src/services/scanner_client.py` for new response format
- Write unit tests for each scanner
- Write integration tests with real Docker images
- Test blocking policy end-to-end

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Sync scanning (no RabbitMQ) | Simplicity, build-service already waits. Async added later. |
| Strict base image allowlist | Predictable, well-maintained bases reduce attack surface dramatically |
| Custom YARA rules | ClamAV alone misses container-specific threats (miners, webshells, escapes) |
| Block ALL secrets | Zero tolerance — secrets in images are an immediate credential leak risk |
| Extract layers with skopeo/docker save | Avoids running container to inspect layers |
| Cache scan results in DB | Avoid rescanning same image tag repeatedly |

---

## Environment Variables

```env
# Scanner settings
SCANNER_MAX_TIMEOUT=300          # Max seconds for full scan
CLAMAV_DB_PATH=/var/lib/clamav   # ClamAV signatures
YARA_RULES_DIR=/rules            # Custom YARA rules location

# Tool paths (defaults usually fine)
TRIVY_PATH=/usr/local/bin/trivy

# Policy settings
BLOCK_ON_HIGH_CVES=true         # Hard block HIGH CVEs (default: true)
ALLOWED_BASE_IMAGES=strict       # strict | known_bad_only
```

---

## Integration with build-service

The build-service calls the scanner after a successful Docker build, before pushing to registry:

```python
# In build-service src/services/scanner_client.py (to update)
async def scan_image(image_tag: str) -> dict:
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            f"{settings.scanner_service_url}/scans/image",
            json={
                "image_tag": image_tag,
                "user_id": user_id,
                "app_name": app_name
            }
        )
        result = response.json()

        # New behavior based on status
        if result["status"] == "BLOCKED":
            raise HTTPException(
                status_code=400,
                detail=f"Security scan failed: {result['block_reason']}"
            )
        elif result["status"] == "WARN":
            # Log warning but proceed
            logger.warning(f"Scan warnings: {result['warnings']}")

        return result
```

---

## Operational Notes

- **First scan is slow**: Trivy downloads ~50MB vulnerability DB on first run. Cache it with a volume mount.
- **ClamAV DB updates**: Run `freshclam` daily. Add to Dockerfile or a cron job.
- **YARA rules maintenance**: Review and update rules quarterly. New container malware emerges regularly.
- **Scan time budget**: Plan 30-60s per scan. Trivy is the slowest component (DB download + scan).
- **Trivy DB volume**: Mount a persistent volume for Trivy's cache to avoid re-downloading on every container restart:
  ```yaml
  volumes:
    - trivy-cache:/root/.cache/trivy
  ```
