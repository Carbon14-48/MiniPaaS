"""
services/auth_client.py
-----------------------
FICHIER PYTHON INTERNE AU BUILD-SERVICE — pas un microservice.

Son unique rôle : appeler auth-service:8001 via HTTP pour vérifier un JWT.
Le build-service appelle cette fonction avant de faire quoi que ce soit.

Flux :
  Route reçoit requête avec header "Authorization: Bearer eyJ..."
      ↓
  verify_token("eyJ...") appelé ici
      ↓
  POST http://auth-service:8001/verify  { "token": "eyJ..." }
      ↓
  auth-service répond { "valid": true, "user_id": 42 }
      ↓
  On retourne user_id=42 à la route, ou on lève une exception si invalide
"""

import httpx
from fastapi import HTTPException, status
from src.config import settings


async def verify_token(token: str) -> int:
    """
    Vérifie le JWT auprès de l'auth-service.

    Paramètre :
        token : le JWT brut extrait du header Authorization (sans "Bearer ")

    Retourne :
        user_id (int) : l'identifiant de l'utilisateur si le token est valide

    Lève :
        HTTPException 401 : si le token est invalide ou expiré
        HTTPException 503 : si l'auth-service est injoignable
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{settings.auth_service_url}/verify",
                json={"token": token}
            )
    except httpx.ConnectError:
        # L'auth-service est down ou pas encore démarré
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service injoignable"
        )

    data = response.json()

    if not data.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré"
        )

    # Retourne l'ID utilisateur pour l'utiliser dans la suite du build
    return int(data["user_id"])
