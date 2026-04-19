"""
routes/logs.py
--------------
Endpoints logs du monitoring-service.

GET /logs/{app_id}         → logs récents d'une app depuis la base
GET /logs/{app_id}/live    → logs live directement depuis Docker (sans base)
GET /logs/user/{user_id}   → logs récents de toutes les apps d'un utilisateur
POST /logs/{app_id}/collect → force une collecte immédiate des logs
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.db import get_db, SessionLocal
from src.models.log_entry import LogEntry
from src.services.docker_collector import (
    get_docker_client,
    get_monitored_containers,
    parse_container_identity,
)
from src.services.log_collector import collect_container_logs

router = APIRouter(prefix="/logs", tags=["logs"])


# ── GET /logs/user/{user_id} ──────────────────────────────────────────────────
# IMPORTANT : avant /logs/{app_id} pour éviter que "user" soit capturé comme app_id

@router.get("/user/{user_id}")
def get_user_logs(
    user_id: int,
    minutes: int = 60,
    level: str = None,
    db: Session = Depends(get_db)
):
    """
    Logs récents de toutes les apps d'un utilisateur.
    Filtrable par niveau : INFO, WARN, ERROR, DEBUG.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    query = db.query(LogEntry).filter(
        LogEntry.user_id == user_id,
        LogEntry.collected_at >= since,
    )

    if level:
        query = query.filter(LogEntry.level == level.upper())

    logs = query.order_by(LogEntry.collected_at.desc()).limit(500).all()
    return [_log_to_dict(l) for l in logs]


# ── GET /logs/{app_id} ────────────────────────────────────────────────────────

@router.get("/{app_id}")
def get_app_logs(
    app_id: str,
    minutes: int = 60,
    level: str = None,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    """
    Retourne les logs d'une app depuis la base PostgreSQL.

    Paramètres :
        minutes : fenêtre temporelle (défaut 60 min)
        level   : filtrer par niveau INFO/WARN/ERROR/DEBUG
        limit   : nombre max de lignes (défaut 200)
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    query = db.query(LogEntry).filter(
        LogEntry.app_id == app_id,
        LogEntry.collected_at >= since,
    )

    if level:
        query = query.filter(LogEntry.level == level.upper())

    logs = query.order_by(LogEntry.collected_at.desc()).limit(limit).all()
    return [_log_to_dict(l) for l in logs]


# ── GET /logs/{app_id}/live ───────────────────────────────────────────────────

@router.get("/{app_id}/live")
def get_app_logs_live(
    app_id: str,
    tail: int = Query(default=100, le=500)
):
    """
    Logs live directement depuis le Docker daemon — sans passer par la base.
    Utile pour voir les logs en temps réel sans attendre la collecte périodique.

    Ne stocke PAS en base — lecture directe uniquement.
    Paramètre tail : nombre de lignes (max 500).
    """
    client = get_docker_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker daemon injoignable"
        )

    containers = get_monitored_containers(client)
    target = None
    for c in containers:
        identity = parse_container_identity(c)
        if identity["app_id"] == app_id:
            target = c
            break

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucun container actif trouvé pour l'app '{app_id}'"
        )

    entries = collect_container_logs(target, tail=tail)
    return {
        "app_id": app_id,
        "container": target.name.lstrip("/"),
        "source": "live",
        "entries": entries,
    }


# ── POST /logs/{app_id}/collect ───────────────────────────────────────────────

@router.post("/{app_id}/collect")
def force_collect_logs(app_id: str):
    """
    Force une collecte immédiate des logs pour une app.
    Utile après un déploiement pour voir les logs de démarrage sans attendre.
    """
    client = get_docker_client()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker daemon injoignable"
        )

    containers = get_monitored_containers(client)
    target = None
    for c in containers:
        identity = parse_container_identity(c)
        if identity["app_id"] == app_id:
            target = c
            break

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucun container actif trouvé pour l'app '{app_id}'"
        )

    identity = parse_container_identity(target)
    entries = collect_container_logs(target, tail=200)

    db = SessionLocal()
    saved = 0
    try:
        for entry in entries:
            log = LogEntry(
                app_id=identity["app_id"],
                user_id=identity["user_id"],
                container_id=target.short_id,
                container_name=target.name.lstrip("/"),
                level=entry["level"],
                message=entry["message"],
                log_timestamp=entry.get("log_timestamp"),
                collected_at=datetime.now(timezone.utc),
            )
            db.add(log)
            saved += 1
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde : {e}")
    finally:
        db.close()

    return {
        "app_id": app_id,
        "collected": saved,
        "message": f"{saved} lignes de logs collectées et sauvegardées"
    }


# ── Utilitaire ────────────────────────────────────────────────────────────────

def _log_to_dict(l: LogEntry) -> dict:
    return {
        "id": l.id,
        "app_id": l.app_id,
        "user_id": l.user_id,
        "container_id": l.container_id,
        "container_name": l.container_name,
        "level": l.level,
        "message": l.message,
        "log_timestamp": l.log_timestamp.isoformat() if l.log_timestamp else None,
        "collected_at": l.collected_at.isoformat(),
    }
