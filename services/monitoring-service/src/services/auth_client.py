import httpx
from fastapi import HTTPException, status
from typing import Optional

from src.config import settings


def verify_token(token: Optional[str]) -> int:
    """
    Vérifie un token Bearer et retourne le user_id.
    Lève HTTPException 401 si invalide/expiré.
    Lève HTTPException 503 si auth-service unreachable.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant"
        )

    if token.startswith("Bearer "):
        token = token[7:]

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{settings.auth_service_url}/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("id")
            elif response.status_code in [401, 403]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalide ou expiré"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Auth service error: {response.status_code}"
                )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unreachable"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service timeout"
        )


def get_current_user(token: str = None) -> int:
    """Dépendance FastAPI pour extraire et vérifier le user_id depuis le token."""
    return verify_token(token)