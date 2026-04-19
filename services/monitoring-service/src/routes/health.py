"""
routes/health.py
----------------
Endpoints health check du monitoring-service.

GET /health                → healthcheck du service lui-même
GET /health/{app_id}       → santé d'une app spécifique (container running?)
GET /health/containers/all → état de tous les containers monitorés
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.db import get_db
from src.models.metric import ContainerMetric
from src.services.docker_collector import (
    get_docker_client,
    get_monitored_containers,
    parse_container_identity,
)

router = APIRouter(prefix="/health", tags=["health"])


# ── GET /health/containers/all ────────────────────────────────────────────────
# IMPORTANT : avant /health/{app_id} pour éviter que "containers" soit app_id

@router.get("/containers/all")
def get_all_containers_health():
    """
    Retourne l'état de tous les containers monitorés en temps réel.
    Lit directement depuis le Docker daemon — pas depuis la base.
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


# ── GET /health/{app_id} ──────────────────────────────────────────────────────

@router.get("/{app_id}")
def get_app_health(app_id: str, db: Session = Depends(get_db)):
    """
    Retourne la santé d'une application spécifique.

    Combine :
      - Statut live du container (Docker daemon)
      - Dernières métriques connues (base PostgreSQL)
    """
    # Statut live depuis Docker
    client = get_docker_client()
    container_status = "unknown"
    container_name = None

    if client:
        containers = get_monitored_containers(client)
        for c in containers:
            identity = parse_container_identity(c)
            if identity["app_id"] == app_id:
                container_status = c.status
                container_name = c.name.lstrip("/")
                break

    # Dernières métriques depuis la base
    since = datetime.now(timezone.utc) - timedelta(minutes=10)
    latest_metric = (
        db.query(ContainerMetric)
        .filter(
            ContainerMetric.app_id == app_id,
            ContainerMetric.collected_at >= since,
        )
        .order_by(ContainerMetric.collected_at.desc())
        .first()
    )

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
