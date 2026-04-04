# Security

## DevSecOps Pipeline

```
Code → Build → Test → Security Scan → Deploy
```

## Security Tools

- **Trivy**: Container image vulnerability scanning
- **SonarQube**: Code quality and security analysis
- **JWT**: Token-based authentication with configurable expiration

## Best Practices

- Never commit secrets (use `.env` files)
- Rotate JWT_SECRET_KEY in production
- Scan all Docker images before deployment
- Use least-privilege Kubernetes service accounts
- Enable RBAC on all services
