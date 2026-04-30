"""
routes/health.py
----------------
Endpoints health check du monitoring-service.

GET /health                → healthcheck du service lui-même
GET /health/{app_id}       → santé d'une app spécifique (container running?)
GET /health/containers/all → état de tous les containers monitorés
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.db import get_db
from src.models.metric import ContainerMetric
from src.services.docker_collector import (
    get_docker_client,
    get_monitored_containers,
    parse_container_identity,
)
from src.services.auth_client import verify_token

router = APIRouter(prefix="/health", tags=["health"])


from typing import Optional


def get_current_user(authorization: str = Header(None)) -> Optional[int]:
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        authorization = authorization[7:]
    try:
        return verify_token(authorization)
    except:
        return None


# ── GET /health/containers/all ────────────────────────────────────────────────
# IMPORTANT : avant /health/{app_id} pour éviter que "containers" soit app_id

@router.get("/containers/all")
def get_all_containers_health(
    current_user: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retourne l'état de tous les containers monitorés en temps réel.
    Lit directement depuis le Docker daemon — pas depuis la base.
    Ne retourne que les containers de l'utilisateur connecté.
    """
    client = get_docker_client()
    if not client:
        return {
            "docker_daemon": "unreachable",
            "containers": [],
            "total": 0,
        }

    containers = get_monitored_containers(client)
    result = []

    for c in containers:
        identity = parse_container_identity(c)
        if current_user is None or identity["user_id"] != current_user:
            continue
        result.append({
            "app_id": identity["app_id"],
            "user_id": identity["user_id"],
            "container_name": c.name.lstrip("/"),
            "container_id": c.short_id,
            "status": c.status,
            "healthy": c.status == "running",
        })

    return {
        "docker_daemon": "ok",
        "containers": result,
        "total": len(result),
        "running": sum(1 for r in result if r["healthy"]),
    }


# ── GET /health/{app_id} ───────────────────────────────���──────────────────────

@router.get("/{app_id}")
def get_app_health(
    app_id: str,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retourne la santé d'une application spécifique.

    Combine :
      - Statut live du container (Docker daemon)
      - Dernières métriques connues (base PostgreSQL)
    Vérifie que l'app appartient à l'utilisateur connecté.
    """
    client = get_docker_client()
    container_status = "unknown"
    container_name = None

    if client:
        containers = get_monitored_containers(client)
        for c in containers:
            identity = parse_container_identity(c)
            if identity["app_id"] == app_id:
                if identity["user_id"] != current_user:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
                container_status = c.status
                container_name = c.name.lstrip("/")
                break

    since = datetime.now(timezone.utc) - timedelta(minutes=10)
    latest_metric = (
        db.query(ContainerMetric)
        .filter(
            ContainerMetric.app_id == app_id,
            ContainerMetric.user_id == current_user,
            ContainerMetric.collected_at >= since,
        )
        .order_by(ContainerMetric.collected_at.desc())
        .first()
    )

    if not latest_metric and container_status == "unknown":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App non trouvée ou accès refusé")

    healthy = container_status == "running"

    return {
        "app_id": app_id,
        "status": container_status,
        "healthy": healthy,
        "container_name": container_name,
        "last_seen": latest_metric.collected_at.isoformat() if latest_metric else None,
        "last_cpu_percent": latest_metric.cpu_percent if latest_metric else None,
        "last_memory_percent": latest_metric.memory_percent if latest_metric else None,
    }


# ── GET /health ───────────────────────────────────────────────────────────────

@router.get("")
def health_check(db: Session = Depends(get_db)):
    """
    Healthcheck du monitoring-service lui-même.
    Vérifie : base de données + Docker daemon.
    Utilisé par Docker Compose pour savoir si le service est prêt.
    """
    # Vérifie la base de données
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    # Vérifie le Docker daemon
    client = get_docker_client()
    docker_status = "ok" if client else "unreachable"

    overall = "ok" if db_status == "ok" else "degraded"

    return {
        "status": overall,
        "service": "monitoring-service",
        "port": 8006,
        "database": db_status,
        "docker_daemon": docker_status,
    }
