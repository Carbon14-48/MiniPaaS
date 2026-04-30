"""
services/scheduler.py
----------------------
Collecte périodique des métriques via APScheduler.

Toutes les N secondes (configurable via COLLECT_INTERVAL_SECONDS),
on parcourt tous les containers monitorés et on sauvegarde
leurs métriques en base PostgreSQL.

Ce scheduler démarre avec l'application FastAPI et s'arrête proprement
quand l'application s'arrête. Il ne bloque pas les requêtes HTTP.

IMPORTANT : Ce module ne casse RIEN dans les autres services.
Il observe passivement le Docker daemon — il ne modifie rien.
"""

import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.config import settings
from src.db import SessionLocal
from src.models.metric import ContainerMetric
from src.models.log_entry import LogEntry
from src.services.docker_collector import (
    get_docker_client,
    get_monitored_containers,
    collect_container_stats,
    parse_container_identity,
)
from src.services.log_collector import collect_container_logs

logger = logging.getLogger(__name__)

# Instance globale du scheduler
_scheduler = BackgroundScheduler()


def collect_metrics_job():
    """
    Job principal exécuté périodiquement.
    Collecte CPU, RAM, réseau de tous les containers monitorés.
    """
    client = get_docker_client()
    if not client:
        logger.warning("Collecte ignorée — Docker daemon injoignable")
        return

    containers = get_monitored_containers(client)

    if not containers:
        logger.debug("Aucun container à monitorer pour l'instant")
        return

    db = SessionLocal()
    try:
        for container in containers:
            identity = parse_container_identity(container)
            stats = collect_container_stats(container)

            if stats is None:
                continue

            metric = ContainerMetric(
                app_id=identity["app_id"],
                user_id=identity["user_id"],
                container_name=container.name.lstrip("/"),
                container_id=container.short_id,
                cpu_percent=stats.get("cpu_percent"),
                memory_usage_bytes=stats.get("memory_usage_bytes"),
                memory_limit_bytes=stats.get("memory_limit_bytes"),
                memory_percent=stats.get("memory_percent"),
                network_rx_bytes=stats.get("network_rx_bytes"),
                network_tx_bytes=stats.get("network_tx_bytes"),
                status=stats.get("status", "unknown"),
                collected_at=datetime.now(timezone.utc),
            )
            db.add(metric)

        db.commit()
        logger.debug(f"Métriques collectées pour {len(containers)} container(s)")

    except Exception as e:
        logger.error(f"Erreur sauvegarde métriques : {e}")
        db.rollback()
    finally:
        db.close()


def cleanup_old_metrics_job():
    """
    Job de nettoyage : supprime les métriques plus vieilles que
    METRICS_RETENTION_DAYS jours. Exécuté une fois par heure.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(
        days=settings.metrics_retention_days
    )
    db = SessionLocal()
    try:
        deleted = db.query(ContainerMetric).filter(
            ContainerMetric.collected_at < cutoff
        ).delete()
        deleted_logs = db.query(LogEntry).filter(
            LogEntry.collected_at < cutoff
        ).delete()
        db.commit()
        if deleted or deleted_logs:
            logger.info(
                f"Nettoyage : {deleted} métriques et {deleted_logs} logs supprimés"
            )
    except Exception as e:
        logger.error(f"Erreur nettoyage : {e}")
        db.rollback()
    finally:
        db.close()


def collect_logs_job():
    """
    Job de collecte des logs.
    Collecte les logs de tous les containers monitorés et les stocke en DB.
    """
    client = get_docker_client()
    if not client:
        logger.warning("Collecte logs ignorée — Docker daemon injoignable")
        return

    containers = get_monitored_containers(client)
    if not containers:
        return

    db = SessionLocal()
    try:
        for container in containers:
            identity = parse_container_identity(container)
            entries = collect_container_logs(container, tail=20)

            for entry in entries:
                log_entry = LogEntry(
                    app_id=identity["app_id"],
                    user_id=identity["user_id"],
                    container_id=identity["container_id"],
                    container_name=container.name.lstrip("/"),
                    level=entry.get("level", "INFO"),
                    message=entry.get("message", ""),
                    log_timestamp=entry.get("log_timestamp"),
                    collected_at=datetime.now(timezone.utc),
                )
                db.add(log_entry)

        db.commit()
        logger.debug(f"Logs collectées pour {len(containers)} container(s)")

    except Exception as e:
        logger.error(f"Erreur sauvegarde logs : {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Démarre le scheduler en arrière-plan."""
    if _scheduler.running:
        return

    # Collecte des métriques toutes les N secondes
    _scheduler.add_job(
        collect_metrics_job,
        trigger=IntervalTrigger(seconds=settings.collect_interval_seconds),
        id="collect_metrics",
        replace_existing=True,
        max_instances=1,  # évite les exécutions parallèles
    )

    # Collecte des logs toutes les 30 secondes
    _scheduler.add_job(
        collect_logs_job,
        trigger=IntervalTrigger(seconds=30),
        id="collect_logs",
        replace_existing=True,
        max_instances=1,
    )

    # Nettoyage des vieilles métriques toutes les heures
    _scheduler.add_job(
        cleanup_old_metrics_job,
        trigger=IntervalTrigger(hours=1),
        id="cleanup_metrics",
        replace_existing=True,
        max_instances=1,
    )

    _scheduler.start()
    logger.info(
        f"Scheduler démarré — collecte toutes les "
        f"{settings.collect_interval_seconds}s"
    )


def stop_scheduler():
    """Arrête proprement le scheduler."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler arrêté")
