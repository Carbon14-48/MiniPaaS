# App Management Service

> **Status:** 🔧 STUB - NOT YET IMPLEMENTED
> **Note:** App metadata is currently stored in deployment records. This service is planned for future use.

## Purpose

The App Management Service is designed to handle:
- Application CRUD operations
- Application metadata management
- Environment variable management
- Application configuration
- Application secrets management

## Planned Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/apps` | List all applications |
| `POST` | `/apps` | Create new application |
| `GET` | `/apps/{id}` | Get application details |
| `PUT` | `/apps/{id}` | Update application |
| `DELETE` | `/apps/{id}` | Delete application |
| `GET` | `/apps/{id}/config` | Get application config |
| `PUT` | `/apps/{id}/config` | Update application config |
| `POST` | `/apps/{id}/env` | Set environment variables |
| `DELETE` | `/apps/{id}/env` | Delete environment variables |
| `GET` | `/health` | Health check |

## Data Model (Planned)

```python
class App:
    id: str
    user_id: int
    name: str
    description: Optional[str]
    repo_url: str
    default_branch: str
    config: dict  # JSON config
    env_vars: dict  # Environment variables
    created_at: datetime
    updated_at: datetime
```

## Use Cases

1. **Configuration Management**: Store and manage application-specific configuration
2. **Environment Variables**: Securely store environment variables
3. **Multi-Environment Support**: Manage dev/staging/prod configurations
4. **Application Metadata**: Store additional metadata about deployed apps

## Future Integration

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│API Gateway  │ (future)
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│    App     │────►│  Deployer   │
│  Management│     │   Service   │
│   (8002)  │     │   (8008)   │
└─────────────┘     └─────────────┘
```

## Running Locally

```bash
cd services/app-management
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8002
```

## Future Enhancements

- [ ] Implement CRUD endpoints
- [ ] Add environment variable encryption
- [ ] Add configuration validation
- [ ] Add webhook support
- [ ] Add application templates

## Related Documentation

- [Main README](../../README.md)
- [Deployer Service](../deployer-service/README.md)
