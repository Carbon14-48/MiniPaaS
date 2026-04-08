"""
routes/registry.py
------------------
Tous les endpoints HTTP du registry-service.

Endpoints :
  POST   /push                      ← appelé par build-service après scan OK
  GET    /images/{user_id}          ← appelé par deployment-service
  GET    /images/tag/{image_tag}    ← appelé par deployment-service
  DELETE /images/{image_tag}        ← appelé par deployment-service / admin
  GET    /health                    ← healthcheck

CONTRAT CRITIQUE avec build-service (registry_client.py existant) :
  La réponse de POST /push DOIT contenir le champ "url" (pas "registry_url")
  car build-service fait : registry_result.get("url")
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import urllib.parse

from src.db import get_db
from src.models.image import RegistryImage
from src.services.docker_registry import push_to_registry, delete_from_registry
from src.config import settings

router = APIRouter()


# ─── Schémas Pydantic ────────────────────────────────────────────────────────

class PushRequest(BaseModel):
    """
    Corps reçu depuis build-service POST /push.
    Correspond exactement à ce qu'envoie registry_client.py du build-service.
    """
    image_tag: str    # ex: "user42/myapp:v1"
    user_id: int      # ex: 42
    app_name: str     # ex: "myapp"


class PushResponse(BaseModel):
    """
    Réponse retournée au build-service.

    ATTENTION : le champ s'appelle "url" et non "registry_url"
    parce que registry_client.py du build-service fait :
        registry_result.get("url")
    Ne JAMAIS changer ce nom de champ.
    """
    status: str
    image_tag: str
    url: str          # ← nom imposé par le contrat build-service
    digest: Optional[str] = None
    size_bytes: Optional[int] = None


class ImageResponse(BaseModel):
    """Représentation d'une image dans les réponses GET."""
    image_id: str
    user_id: int
    app_name: str
    image_tag: str
    registry_url: str
    digest: Optional[str] = None
    size_bytes: Optional[int] = None
    pushed_at: str
    is_active: bool


# ─── POST /push ───────────────────────────────────────────────────────────────

@router.post("/push", response_model=PushResponse)
def push_image(request: PushRequest, db: Session = Depends(get_db)):
    """
    Reçoit une image buildée, la pousse vers le registry local, sauvegarde
    les métadonnées en base et retourne l'URL + digest au build-service.

    Appelé UNIQUEMENT par build-service après un scan CVE réussi.

    Pipeline interne :
      1. Vérifie que l'image existe localement (sur le daemon Docker)
      2. docker tag + docker push vers registry:5000
      3. Nettoie les images locales (libère l'espace disque)
      4. Sauvegarde les métadonnées en base PostgreSQL
      5. Retourne { url, digest, size_bytes } au build-service
    """

    # Vérifie si cette image a déjà été pushée (idempotence)
    existing = db.query(RegistryImage).filter(
        RegistryImage.image_tag == request.image_tag,
        RegistryImage.is_active == True
    ).first()

    if existing:
        # L'image existe déjà dans le registry — retourne les infos existantes
        # sans re-pusher (idempotent)
        return PushResponse(
            status="already_exists",
            image_tag=existing.image_tag,
            url=existing.registry_url,
            digest=existing.digest,
            size_bytes=existing.size_bytes,
        )

    # Push vers registry:5000 via Docker SDK
    # Lève HTTPException si l'image n'existe pas localement ou si push échoue
    result = push_to_registry(request.image_tag)

    # Sauvegarde les métadonnées en base
    image_record = RegistryImage(
        user_id=request.user_id,
        app_name=request.app_name,
        image_tag=request.image_tag,
        registry_url=result["registry_url"],
        digest=result.get("digest"),
        size_bytes=result.get("size_bytes"),
        pushed_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db.add(image_record)
    db.commit()
    db.refresh(image_record)

    return PushResponse(
        status="success",
        image_tag=request.image_tag,
        url=result["registry_url"],   # ← "url" imposé par contrat build-service
        digest=result.get("digest"),
        size_bytes=result.get("size_bytes"),
    )


# ─── GET /images/{user_id} ────────────────────────────────────────────────────

@router.get("/images/{user_id}", response_model=List[ImageResponse])
def get_user_images(user_id: int, db: Session = Depends(get_db)):
    """
    Liste toutes les images actives d'un utilisateur.

    Appelé par le deployment-service pour savoir quelles images sont
    disponibles à déployer pour un utilisateur donné.

    Retourne les images triées de la plus récente à la plus ancienne.
    """
    images = db.query(RegistryImage).filter(
        RegistryImage.user_id == user_id,
        RegistryImage.is_active == True
    ).order_by(RegistryImage.pushed_at.desc()).all()

    return [_to_response(img) for img in images]


# ─── GET /images/tag/{image_tag} ─────────────────────────────────────────────

@router.get("/images/tag/{image_tag:path}", response_model=ImageResponse)
def get_image_by_tag(image_tag: str, db: Session = Depends(get_db)):
    """
    Retourne les détails d'une image par son tag.

    Appelé par le deployment-service pour obtenir l'URL et le digest
    d'une image spécifique avant de la déployer.

    Le paramètre :path permet d'accepter les slashes dans le tag.
    Ex: /images/tag/user42/myapp:v1  (le "/" est dans le tag)

    Le tag peut être encodé URL ou non :
      /images/tag/user42/myapp:v1
      /images/tag/user42%2Fmyapp%3Av1
    """
    # Décode l'URL encoding si présent
    decoded_tag = urllib.parse.unquote(image_tag)

    image = db.query(RegistryImage).filter(
        RegistryImage.image_tag == decoded_tag,
        RegistryImage.is_active == True
    ).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image '{decoded_tag}' introuvable dans le registry"
        )

    return _to_response(image)


# ─── DELETE /images/{image_tag} ──────────────────────────────────────────────

@router.delete("/images/{image_tag:path}")
def delete_image(image_tag: str, db: Session = Depends(get_db)):
    """
    Supprime une image du registry local et marque l'entrée en base
    comme inactive (soft delete — l'historique est conservé).

    Appelé par le deployment-service ou un admin pour nettoyer
    les images obsolètes.

    Le soft delete est intentionnel : on garde l'historique des builds
    pour audit et rollback potentiel.
    """
    decoded_tag = urllib.parse.unquote(image_tag)

    image = db.query(RegistryImage).filter(
        RegistryImage.image_tag == decoded_tag,
        RegistryImage.is_active == True
    ).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image '{decoded_tag}' introuvable"
        )

    # Supprime physiquement du registry:5000 (best effort)
    # Si ça échoue, on continue quand même avec le soft delete en base
    delete_from_registry(image.registry_url)

    # Soft delete en base
    image.is_active = False
    db.commit()

    return {
        "status": "deleted",
        "image_tag": decoded_tag,
        "message": "Image supprimée du registry et marquée inactive en base"
    }


# ─── GET /health ──────────────────────────────────────────────────────────────

@router.get("/health")
def health(db: Session = Depends(get_db)):
    """
    Healthcheck complet : vérifie le service ET la connexion à la base.
    Utilisé par Docker Compose pour savoir si le service est prêt.
    """
    # Vérifie la connexion à la base
    try:
        db.execute(__import__('sqlalchemy').text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    # Vérifie que le registry:5000 est joignable
    try:
        import httpx
        resp = httpx.get(f"{settings.registry_url}/v2/", timeout=3.0)
        registry_status = "ok" if resp.status_code in (200, 401) else "error"
    except Exception:
        registry_status = "unreachable"

    overall = "ok" if db_status == "ok" else "degraded"

    return {
        "status": overall,
        "service": "registry-service",
        "registry": settings.registry_host,
        "registry_status": registry_status,
        "database": db_status,
    }


# ─── Utilitaire ───────────────────────────────────────────────────────────────

def _to_response(img: RegistryImage) -> ImageResponse:
    """Convertit un modèle SQLAlchemy en schéma Pydantic."""
    return ImageResponse(
        image_id=img.image_id,
        user_id=img.user_id,
        app_name=img.app_name,
        image_tag=img.image_tag,
        registry_url=img.registry_url,
        digest=img.digest,
        size_bytes=img.size_bytes,
        pushed_at=img.pushed_at.isoformat(),
        is_active=img.is_active,
    )
