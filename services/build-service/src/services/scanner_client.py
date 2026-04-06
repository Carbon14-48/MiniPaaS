"""
services/scanner_client.py
--------------------------
FICHIER PYTHON INTERNE AU BUILD-SERVICE — pas un microservice.

Son unique rôle : appeler security-scanner:8003 via HTTP après le docker build.
Si le scanner détecte une CVE critique, le build est bloqué (image non pushée).

Flux :
  Après docker build réussi → image "user42/myapp:v1" existe localement
      ↓
  scan_image("user42/myapp:v1") appelé ici
      ↓
  POST http://security-scanner:8006/scan  { "image_tag": "user42/myapp:v1" }
      ↓
  Le scanner analyse l'image avec Trivy et répond :
    { "critical": false, "vulnerabilities": [{"id": "CVE-2024-5678", "severity": "medium"}] }
  ou
    { "critical": true, "cve": "CVE-2024-1234", "severity": "CRITICAL", "package": "libssl" }
      ↓
  On retourne le résultat brut à la route pour décider de la suite
"""

import httpx
from fastapi import HTTPException, status
from src.config import settings


async def scan_image(image_tag: str) -> dict:
    """
    Envoie l'image au security-scanner pour analyse CVE.

    Paramètre :
        image_tag : tag de l'image à scanner (ex: "user42/myapp:v1")

    Retourne :
        dict avec au minimum :
          - "critical" (bool) : True si une CVE critique a été trouvée
          - "vulnerabilities" (list) : liste des vulnérabilités trouvées
          - "cve" (str, optionnel) : ID de la CVE critique si présente

    Lève :
        HTTPException 503 : si le scanner est injoignable
    """
    try:
        # Timeout long car Trivy peut prendre du temps sur une grosse image
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.scanner_service_url}/scan",
                json={"image_tag": image_tag}
            )
            response.raise_for_status()
    except httpx.ConnectError:
        # Le scanner est down → on bloque par sécurité (fail-safe)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security scanner injoignable — build bloqué par sécurité"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erreur scanner : {str(e)}"
        )

    return response.json()
