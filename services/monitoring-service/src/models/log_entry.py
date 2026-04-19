"""
models/log_entry.py
-------------------
Table log_entries — stocke les logs des containers applicatifs.

On ne stocke PAS les logs des services internes MiniPaaS
(build-service, auth-service, etc.) — seulement les logs
des apps déployées par les utilisateurs.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime
from src.db import Base


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Identifiant de l'application utilisateur
    app_id = Column(String, nullable=False, index=True)

    # user_id propriétaire
    user_id = Column(Integer, nullable=False, index=True)

    # ID court du container Docker source
    container_id = Column(String, nullable=False)

    # Nom du container Docker
    container_name = Column(String, nullable=False)

    # Niveau de log détecté : INFO, WARN, ERROR, DEBUG
    # Détecté par analyse du contenu du message
    level = Column(String, nullable=False, default="INFO")

    # Le message de log brut
    message = Column(Text, nullable=False)

    # Timestamp du log (issu du container lui-même)
    log_timestamp = Column(DateTime, nullable=True)

    # Quand on l'a enregistré en base
    collected_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
