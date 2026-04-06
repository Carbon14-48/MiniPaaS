"""
routes/push.py
--------------
Endpoint POST /push — reçoit une image locale du build-service
et la pousse vers le registry Docker local (registry:5000).

Schéma de la requête :
{
    "image_tag": "user42/myapp:v1",   # tag local (ex: <user>/<app>:v<num>)
    "user_id": 42,
    "app_name": "myapp"
}

Schéma de la réponse :
{
    "url": "localhost:5000/user42/myapp:v1",
    "digest": "sha256:abc123..."
}
"""

import docker
import hashlib
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.config import settings

router = APIRouter()

client = docker.from_env()


class PushRequest(BaseModel):
    image_tag: str
    user_id: int
    app_name: str


class PushResponse(BaseModel):
    url: str
    digest: str


@router.post("/push", response_model=PushResponse)
async def push_image(request: PushRequest):
    """
    1. Vérifie que l'image existe localement
    2. Tague l'image pour le registry local (localhost:5000/<user>/<app>:v<num>)
    3. Push vers le registry
    4. Retourne l'URL complète et le digest SHA256
    """
    try:
        client.images.get(request.image_tag)
    except docker.errors.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {request.image_tag} introuvable localement"
        )

    registry_tag = f"{settings.registry_url}/{request.image_tag}"

    try:
        client.api.tag(request.image_tag, registry_tag)
    except docker.errors.APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Échec du docker tag : {str(e)}"
        )

    try:
        output_lines = []
        for line in client.api.push(registry_tag, stream=True, decode=True):
            output_lines.append(line)
    except docker.errors.APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Échec du docker push : {str(e)}"
        )

    digest = _extract_digest(output_lines)

    return PushResponse(
        url=registry_tag,
        digest=digest
    )


def _extract_digest(output_lines: list) -> str:
    for line in reversed(output_lines):
        if "digest" in line:
            return line["digest"]
    return "sha256:unknown"
