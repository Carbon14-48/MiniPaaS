"""Auth client for service-to-service identity checks.

Build-service delegates token validation to auth-service via a stable
introspection endpoint: GET /auth/me with Bearer token.
"""

import httpx
from fastapi import HTTPException, status
from src.config import settings


async def verify_token(token: str) -> int:
    """Validate token and return user_id from auth-service.

    Contract:
    - Request: GET {auth_service_url}/auth/me with Authorization: Bearer <token>
    - Response: 200 JSON containing at least {"id": <int>}.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.auth_service_url}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service injoignable"
        )

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )

    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service indisponible"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Réponse auth-service invalide"
        )

    try:
        data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Réponse auth-service non JSON"
        )

    user_id = data.get("id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Champ user id manquant dans la réponse auth-service"
        )

    return int(user_id)
