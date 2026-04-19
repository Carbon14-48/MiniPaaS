"""
models/metric.py
----------------
Table container_metrics — stocke les métriques collectées périodiquement.

Une ligne = une snapshot de métriques pour un container à un instant T.
Collectée toutes les N secondes par le scheduler APScheduler.

Lien avec les autres services :
  Les containers sont identifiés par leur nom Docker.
  Le deployer-service crée des containers avec des noms prévisibles
  (ex: minipaas_user42_myapp). Le monitoring les trouve par ce nom.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, BigInteger, DateTime
from src.db import Base


class ContainerMetric(Base):
    __tablename__ = "container_metrics"

    # Identifiant unique de cette mesure
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Identifiant de l'application — correspond à app_name dans build-service
    app_id = Column(String, nullable=False, index=True)

    # user_id propriétaire de l'app
    user_id = Column(Integer, nullable=False, index=True)

    # Nom du container Docker (ex: minipaas_user42_myapp)
    container_name = Column(String, nullable=False)

    # ID court du container Docker
    container_id = Column(String, nullable=False)

    # ── Métriques CPU ─────────────────────────────────────────────────────────
    # Pourcentage d'utilisation CPU (0.0 - 100.0)
    cpu_percent = Column(Float, nullable=True)

    # ── Métriques Mémoire ─────────────────────────────────────────────────────
    # Mémoire utilisée en bytes
    memory_usage_bytes = Column(BigInteger, nullable=True)

    # Limite mémoire du container en bytes
    memory_limit_bytes = Column(BigInteger, nullable=True)

    # Pourcentage mémoire utilisée (0.0 - 100.0)
    memory_percent = Column(Float, nullable=True)

    # ── Métriques Réseau ──────────────────────────────────────────────────────
    # Bytes reçus depuis le démarrage du container
    network_rx_bytes = Column(BigInteger, nullable=True)

    # Bytes envoyés depuis le démarrage du container
    network_tx_bytes = Column(BigInteger, nullable=True)

    # ── Statut ────────────────────────────────────────────────────────────────
    # Statut Docker du container : running, exited, paused...
    status = Column(String, nullable=False, default="running")

    # Date/heure de cette mesure
    collected_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
