"""
routes/build.py
---------------
Définit les 3 endpoints HTTP du build-service :

  POST /build            → déclenche un build complet
  GET  /build/{job_id}   → statut d'un build existant
  GET  /build/user/{uid} → historique des builds d'un utilisateur

C'est ici que toute la logique est orchestrée :
  1. Extraire et vérifier le JWT (auth_client)
  2. Cloner le repo (git_service)
  3. Détecter/générer le Dockerfile (docker_service)
  4. Builder l'image (docker_service)
  5. Scanner l'image (scanner_client)
  6. Pousser vers le registry si scan OK (registry_client)
  7. Sauvegarder le job en base (SQLAlchemy)
  8. Retourner le résultat au Gateway
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional

from src.db import get_db
from src.models.job import BuildJob, BuildStatus
from src.services.auth_client import verify_token
from src.services.git_service import clone_repo, cleanup_repo
from src.services.docker_service import detect_and_prepare_dockerfile, build_image
from src.services.scanner_client import scan_image
from src.services.registry_client import push_image

router = APIRouter()


# ─── Schémas Pydantic (validation des données entrantes/sortantes) ──────────

class BuildRequest(BaseModel):
    """Corps de la requête POST /build envoyée par le Gateway."""
    repo_url: str       # ex: "https://github.com/user42/myapp.git"
    branch: str = "main"
    app_name: str       # ex: "myapp"


class BuildResponse(BaseModel):
    """Réponse retournée au Gateway après un build."""
    status: str
    job_id: str
    image_tag: Optional[str] = None
    image_url: Optional[str] = None
    build_logs: Optional[str] = None
    reason: Optional[str] = None        # rempli si status = "blocked" ou "failed"
    scan_result: Optional[dict] = None


# ─── Endpoint principal : déclenche un build ────────────────────────────────

@router.post("/build", response_model=BuildResponse)
async def trigger_build(
    request: BuildRequest,
    authorization: str = Header(...),   # Header "Authorization: Bearer eyJ..."
    db: Session = Depends(get_db)
):
    """
    Orchestre le pipeline complet :
    auth → clone → dockerfile → build → scan → push → sauvegarde → réponse
    """

    # ── Étape 1 : Extraire le token du header Authorization ──────────────────
    # Header format attendu : "Bearer eyJhbGci..."
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization invalide. Format attendu : Bearer <token>"
        )
    token = authorization.removeprefix("Bearer ").strip()

    # ── Étape 2 : Vérifier le JWT auprès de l'auth-service ──────────────────
    # Si invalide → lève automatiquement HTTPException 401
    user_id = await verify_token(token)

    # ── Étape 3 : Créer le job en base avec status "pending" ─────────────────
    # Génère un ID unique pour ce build
    job_id = str(uuid.uuid4())[:8]  # ex: "a3f9c1b2" — court et lisible

    # Compte combien de builds cet utilisateur a déjà fait pour cette app
    # (sert à incrémenter le numéro de version : v1, v2, v3...)
    build_number = db.query(func.count(BuildJob.job_id)).filter(
        BuildJob.user_id == user_id,
        BuildJob.app_name == request.app_name,
        BuildJob.status == BuildStatus.success
    ).scalar() + 1

    job = BuildJob(
        job_id=job_id,
        user_id=user_id,
        repo_url=request.repo_url,
        app_name=request.app_name,
        branch=request.branch,
        status=BuildStatus.running,
    )
    db.add(job)
    db.commit()

    # À partir d'ici, on essaie de builder — si ça plante on met "failed" en base
    try:

        # ── Étape 4 : Cloner le repo Git ──────────────────────────────────────
        repo_path = clone_repo(request.repo_url, job_id, request.branch)

        # ── Étape 5 : Détecter ou générer le Dockerfile ───────────────────────
        # Cherche dans /tmp/builds/<job_id>/Dockerfile
        # Si absent → génère un Dockerfile selon le langage détecté
        detect_and_prepare_dockerfile(repo_path)

        # ── Étape 6 : Builder l'image Docker ──────────────────────────────────
        # image_tag = "user42/myapp:v1"
        image_tag, build_logs = build_image(
            repo_path=repo_path,
            app_name=request.app_name,
            user_id=user_id,
            build_number=build_number
        )

        # ── Étape 7 : Scanner l'image pour les CVE ────────────────────────────
        scan_result = await scan_image(image_tag)

        if scan_result.get("critical"):
            # CVE critique trouvée → on bloque, on ne push pas
            job.status = BuildStatus.blocked
            job.image_tag = image_tag
            job.build_logs = build_logs
            job.scan_result = scan_result
            job.finished_at = datetime.now(timezone.utc)
            db.commit()

            return BuildResponse(
                status="blocked",
                job_id=job_id,
                image_tag=image_tag,
                build_logs=build_logs,
                scan_result=scan_result,
                reason=f"CVE critique détectée : {scan_result.get('cve', 'inconnue')}"
            )

        # ── Étape 8 : Pousser l'image vers le registry ────────────────────────
        registry_result = await push_image(image_tag, user_id, request.app_name)
        image_url = registry_result.get("url")

        # ── Étape 9 : Marquer le job "success" en base ────────────────────────
        job.status = BuildStatus.success
        job.image_tag = image_tag
        job.image_url = image_url
        job.build_logs = build_logs
        job.scan_result = scan_result
        job.finished_at = datetime.now(timezone.utc)
        db.commit()

        return BuildResponse(
            status="success",
            job_id=job_id,
            image_tag=image_tag,
            image_url=image_url,
            build_logs=build_logs,
            scan_result=scan_result
        )

    except HTTPException:
        # Re-lève les HTTPException déjà bien formées (auth, scan, etc.)
        job.status = BuildStatus.failed
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise

    except Exception as e:
        # Erreur inattendue → marque le job failed et retourne l'erreur
        job.status = BuildStatus.failed
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur inattendue : {str(e)}"
        )

    finally:
        # Toujours nettoyer le dossier temporaire — qu'il y ait succès ou erreur
        cleanup_repo(job_id)


# ─── Endpoint : statut d'un build par son ID ────────────────────────────────

@router.get("/build/{job_id}", response_model=BuildResponse)
def get_build(job_id: str, db: Session = Depends(get_db)):
    """
    Retourne le statut et les détails d'un build existant.
    Utilisé par le Gateway pour que l'utilisateur consulte ses builds.
    """
    job = db.query(BuildJob).filter(BuildJob.job_id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Build {job_id} introuvable"
        )

    return BuildResponse(
        status=job.status.value,
        job_id=job.job_id,
        image_tag=job.image_tag,
        image_url=job.image_url,
        build_logs=job.build_logs,
        scan_result=job.scan_result
    )


# ─── Endpoint : historique des builds d'un utilisateur ──────────────────────

@router.get("/build/user/{user_id}")
def get_user_builds(user_id: int, db: Session = Depends(get_db)):
    """
    Liste tous les builds d'un utilisateur, du plus récent au plus ancien.
    Utile pour afficher l'historique dans le dashboard frontend.
    """
    jobs = db.query(BuildJob).filter(
        BuildJob.user_id == user_id
    ).order_by(BuildJob.created_at.desc()).all()

    return [
        {
            "job_id": job.job_id,
            "app_name": job.app_name,
            "status": job.status.value,
            "image_tag": job.image_tag,
            "created_at": job.created_at.isoformat(),
            "finished_at": job.finished_at.isoformat() if job.finished_at else None
        }
        for job in jobs
    ]
