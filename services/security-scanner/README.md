# Security Scanner

Scans code and Docker images for vulnerabilities using Trivy and SonarQube.

## Endpoints

- `POST /scans/image` - Scan a container image
- `POST /scans/code` - Scan source code
- `GET /scans/{id}` - Get scan results
- `GET /health` - Health check

## Running locally

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```
