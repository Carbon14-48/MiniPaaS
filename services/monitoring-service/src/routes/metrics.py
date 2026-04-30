"""
routes/metrics.py
-----------------
Endpoints métriques du monitoring-service.

GET /metrics/{app_id}     → métriques récentes d'une app (JSON)
GET /metrics/user/{uid}   → toutes les apps d'un utilisateur
GET /metrics              → format Prometheus texte (pour scraping)
GET /metrics/summary      → résumé agrégé de toutes les apps

Le endpoint GET /metrics en format Prometheus est crucial :
Prometheus le scrape toutes les 15s et Grafana affiche les graphiques.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.db import get_db
from src.models.metric import ContainerMetric
from src.services.auth_client import verify_token

router = APIRouter(prefix="/metrics", tags=["metrics"])


def get_current_user(authorization: str = Header(None)) -> Optional[int]:
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        authorization = authorization[7:]
    try:
        return verify_token(authorization)
    except:
        return None
    if token.startswith("Bearer "):
        token = token[7:]
    try:
        user_id = verify_token(token)
        logger.info(f"metrics.py: get_current_user returning user_id={user_id}")
        return user_id
    except Exception as e:
        logger.warning(f"metrics.py: get_current_user verify_token failed: {e}")
        return None


# ── GET /metrics/user/{user_id} ───────────────────────────────────────────────
# IMPORTANT : cette route DOIT être avant /metrics/{app_id}
# sinon FastAPI capture "user" comme app_id

@router.get("/user/{user_id}")
def get_user_metrics(
    user_id: int,
    minutes: int = 60,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retourne les métriques récentes de toutes les apps d'un utilisateur.
    Paramètre minutes : fenêtre temporelle (défaut 60 minutes).
    Un utilisateur ne peut voir que ses propres métriques.
    """
    if current_user != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    metrics = db.query(ContainerMetric).filter(
        ContainerMetric.user_id == user_id,
        ContainerMetric.collected_at >= since,
    ).order_by(ContainerMetric.collected_at.desc()).limit(500).all()

    return [_metric_to_dict(m) for m in metrics]


# ── GET /metrics/summary ──────────────────────────────────────────────────────

@router.get("/summary")
def get_metrics_summary(
    current_user: Optional[int] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Résumé agrégé : dernière valeur connue par app_id.
    Si pas de user connecté, retourne toutes les apps système.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    # Si pas de user connecté, retourner tous les containers système
    if current_user is None:
        results = (
            db.query(ContainerMetric)
            .filter(ContainerMetric.collected_at >= since)
            .order_by(ContainerMetric.app_id, ContainerMetric.collected_at.desc())
            .distinct(ContainerMetric.app_id)
            .limit(50)
            .all()
        )
    else:
        subq = (
            db.query(
                ContainerMetric.app_id,
                func.max(ContainerMetric.collected_at).label("latest")
            )
            .filter(
                ContainerMetric.collected_at >= since,
                ContainerMetric.user_id == current_user
            )
            .group_by(ContainerMetric.app_id)
            .subquery()
        )

        results = (
            db.query(ContainerMetric)
            .join(
                subq,
                (ContainerMetric.app_id == subq.c.app_id) &
                (ContainerMetric.collected_at == subq.c.latest)
            )
            .all()
        )

    return [_metric_to_dict(m) for m in results]


# ── GET /metrics/{app_id} ─────────────────────────────────────────────────────

@router.get("/{app_id}")
def get_app_metrics(
    app_id: str,
    minutes: int = 60,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retourne les métriques d'une app sur les N dernières minutes.
    Triées de la plus récente à la plus ancienne.
    Un utilisateur ne peut voir que les métriques de ses propres apps.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    metrics = db.query(ContainerMetric).filter(
        ContainerMetric.app_id == app_id,
        ContainerMetric.user_id == current_user,
        ContainerMetric.collected_at >= since,
    ).order_by(ContainerMetric.collected_at.desc()).limit(500).all()

    if not metrics:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App non trouvée ou accès refusé")

    return [_metric_to_dict(m) for m in metrics]


# ── GET /metrics — format Prometheus ──────────────────────────────────────────

@router.get("", response_class=PlainTextResponse)
def prometheus_metrics(db: Session = Depends(get_db)):
    """
    Expose les métriques au format texte Prometheus.

    Prometheus scrape cet endpoint toutes les 15s (configuré dans prometheus.yml).
    Grafana lit Prometheus et affiche les graphiques.

    Format :
      # HELP metric_name Description
      # TYPE metric_name gauge
      metric_name{label="value"} 42.0
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=5)

    # Dernière valeur connue par container (dans les 5 dernières minutes)
    subq = (
        db.query(
            ContainerMetric.app_id,
            func.max(ContainerMetric.collected_at).label("latest")
        )
        .filter(ContainerMetric.collected_at >= since)
        .group_by(ContainerMetric.app_id)
        .subquery()
    )

    metrics = (
        db.query(ContainerMetric)
        .join(
            subq,
            (ContainerMetric.app_id == subq.c.app_id) &
            (ContainerMetric.collected_at == subq.c.latest)
        )
        .all()
    )

    lines = []

    # ── CPU ──────────────────────────────────────────────────────────────────
    lines.append("# HELP minipaas_container_cpu_percent CPU usage percent")
    lines.append("# TYPE minipaas_container_cpu_percent gauge")
    for m in metrics:
        if m.cpu_percent is not None:
            labels = _prom_labels(m)
            lines.append(f"minipaas_container_cpu_percent{{{labels}}} {m.cpu_percent}")

    # ── Mémoire utilisée ─────────────────────────────────────────────────────
    lines.append("# HELP minipaas_container_memory_usage_bytes Memory usage in bytes")
    lines.append("# TYPE minipaas_container_memory_usage_bytes gauge")
    for m in metrics:
        if m.memory_usage_bytes is not None:
            labels = _prom_labels(m)
            lines.append(
                f"minipaas_container_memory_usage_bytes{{{labels}}} {m.memory_usage_bytes}"
            )

    # ── Mémoire % ────────────────────────────────────────────────────────────
    lines.append("# HELP minipaas_container_memory_percent Memory usage percent")
    lines.append("# TYPE minipaas_container_memory_percent gauge")
    for m in metrics:
        if m.memory_percent is not None:
            labels = _prom_labels(m)
            lines.append(
                f"minipaas_container_memory_percent{{{labels}}} {m.memory_percent}"
            )

    # ── Réseau RX ────────────────────────────────────────────────────────────
    lines.append("# HELP minipaas_container_network_rx_bytes Network bytes received")
    lines.append("# TYPE minipaas_container_network_rx_bytes counter")
    for m in metrics:
        if m.network_rx_bytes is not None:
            labels = _prom_labels(m)
            lines.append(
                f"minipaas_container_network_rx_bytes{{{labels}}} {m.network_rx_bytes}"
            )

    # ── Réseau TX ────────────────────────────────────────────────────────────
    lines.append("# HELP minipaas_container_network_tx_bytes Network bytes sent")
    lines.append("# TYPE minipaas_container_network_tx_bytes counter")
    for m in metrics:
        if m.network_tx_bytes is not None:
            labels = _prom_labels(m)
            lines.append(
                f"minipaas_container_network_tx_bytes{{{labels}}} {m.network_tx_bytes}"
            )

    return "\n".join(lines) + "\n"


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _metric_to_dict(m: ContainerMetric) -> dict:
    return {
        "id": m.id,
        "app_id": m.app_id,
        "user_id": m.user_id,
        "container_name": m.container_name,
        "container_id": m.container_id,
        "cpu_percent": m.cpu_percent,
        "memory_usage_bytes": m.memory_usage_bytes,
        "memory_limit_bytes": m.memory_limit_bytes,
        "memory_percent": m.memory_percent,
        "network_rx_bytes": m.network_rx_bytes,
        "network_tx_bytes": m.network_tx_bytes,
        "status": m.status,
        "collected_at": m.collected_at.isoformat(),
    }


def _prom_labels(m: ContainerMetric) -> str:
    """Formate les labels Prometheus pour une métrique."""
    return (
        f'app_id="{m.app_id}",'
        f'user_id="{m.user_id}",'
        f'container="{m.container_name}"'
    )
