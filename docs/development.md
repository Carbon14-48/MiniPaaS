# Development Guide

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Node.js 20+ (for frontend)
- kubectl (for local K8s testing)

## Local Development

```bash
# Setup
./scripts/setup.sh

# Start all services
./scripts/dev.sh

# Or start individual service
cd services/api-gateway
pip install -r requirements.txt
uvicorn src.main:app --reload
```

## Project Structure

```
services/          # Python microservices
frontend/          # React dashboard
shared/            # Common code
infra/             # Docker & K8s configs
.github/workflows/ # CI/CD pipelines
docs/              # Documentation
scripts/           # Dev utility scripts
```

## Running Tests

```bash
# All services
./scripts/test-all.sh

# Individual service
cd services/api-gateway
pytest tests/ -v
```

## Code Style

- Python: Ruff for linting, Black for formatting
- TypeScript: ESLint + Prettier
