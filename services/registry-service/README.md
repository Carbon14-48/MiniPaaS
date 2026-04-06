# Registry Service

Reçoit les images Docker du build-service et les pousse vers le registry local (`registry:5000`).

## Endpoints

### `GET /`
Santé du service.

```json
{ "status": "healthy", "service": "registry-service" }
```

### `POST /push`
Pousse une image locale vers le registry.

**Requête :**
```json
{
    "image_tag": "user42/myapp:v1",
    "user_id": 42,
    "app_name": "myapp"
}
```

**Réponse :**
```json
{
    "url": "http://registry:5000/user42/myapp:v1",
    "digest": "sha256:abc123..."
}
```

## Variables d'environnement

| Variable       | Default                  | Description                      |
|----------------|--------------------------|----------------------------------|
| `REGISTRY_URL` | `http://registry:5000`   | URL du registry Docker local     |
| `LOG_LEVEL`    | `INFO`                   | Niveau de logging                |

## Architecture

```
build-service
    │
    │ POST /push { image_tag, user_id, app_name }
    ▼
registry-service
    │
    │ docker tag + docker push
    ▼
registry:5000
```

Le service accède au socket Docker (`/var/run/docker.sock`) pour exécuter `docker tag` et `docker push`.
