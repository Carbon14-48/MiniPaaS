"""
services/registry_client.py
----------------------------
FICHIER PYTHON INTERNE AU BUILD-SERVICE — pas un microservice.

Son unique rôle : appeler registry-service:8005 pour pousser l'image Docker.
N'est appelé QUE si le scan de sécurité est passé (critical: false).

Le registry-service se charge lui-même de :
  - Se connecter au registry local (registry:5000)
  - Faire le docker tag + docker push
  - Retourner l'URL finale de l'image

Flux :
  Scan OK (critical: false)
      ↓
  push_image("user42/myapp:v1", 42, "myapp") appelé ici
      ↓
  POST http://registry-service:8005/push
       { "image_tag": "user42/myapp:v1", "user_id": 42, "app_name": "myapp" }
      ↓
  registry-service répond :
    { "url": "registry:5000/user42/myapp:v1", "digest": "sha256:abc123..." }
      ↓
  On retourne l'URL à la route pour la sauvegarder en base et la retourner au Gateway
"""

import httpx
from fastapi import HTTPException, status
from src.config import settings


async def push_image(image_tag: str, user_id: int, app_name: str) -> dict:
    """
    Demande au registry-service de pousser l'image vers le registry local.

    Paramètres :
        image_tag : tag local de l'image (ex: "user42/myapp:v1")
        user_id   : ID de l'utilisateur propriétaire de l'image
        app_name  : nom de l'application

    Retourne :
        dict avec :
          - "url" (str) : URL complète de l'image dans le registry
          - "digest" (str) : hash SHA256 de l'image poussée

    Lève :
        HTTPException 503 : si le registry-service est injoignable
        HTTPException 500 : si le push échoue côté registry
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.registry_service_url}/push",
                json={
                    "image_tag": image_tag,
                    "user_id": user_id,
                    "app_name": app_name
                }
            )
            response.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Registry service injoignable"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du push : {str(e)}"
        )

    return response.json()
