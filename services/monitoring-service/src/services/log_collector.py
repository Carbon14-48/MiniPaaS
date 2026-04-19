"""
services/log_collector.py
--------------------------
Collecte et analyse les logs des containers via Docker SDK.

Stratégie : on lit les logs via l'API Docker (équivalent docker logs)
et on détecte le niveau (INFO/WARN/ERROR/DEBUG) par analyse du contenu.
On ne stocke que les N dernières lignes pour éviter de saturer la base.
"""

import re
import logging
from datetime import datetime, timezone
from typing import Optional
from docker.errors import NotFound, DockerException

logger = logging.getLogger(__name__)

# Patterns de détection du niveau de log
_ERROR_PATTERNS = re.compile(
    r'\b(error|err|fatal|critical|exception|traceback|failed)\b',
    re.IGNORECASE
)
_WARN_PATTERNS = re.compile(
    r'\b(warn|warning|deprecated|caution)\b',
    re.IGNORECASE
)
_DEBUG_PATTERNS = re.compile(
    r'\b(debug|trace|verbose)\b',
    re.IGNORECASE
)


def detect_log_level(message: str) -> str:
    """
    Détecte le niveau de log depuis le contenu du message.

    Ordre de priorité : ERROR > WARN > DEBUG > INFO
    """
    if _ERROR_PATTERNS.search(message):
        return "ERROR"
    if _WARN_PATTERNS.search(message):
        return "WARN"
    if _DEBUG_PATTERNS.search(message):
        return "DEBUG"
    return "INFO"


def collect_container_logs(container, tail: int = 100) -> list[dict]:
    """
    Récupère les dernières lignes de logs d'un container.

    Paramètres :
        container : objet Container Docker SDK
        tail      : nombre de lignes à récupérer (défaut 100)

    Retourne :
        liste de dicts avec message, level, log_timestamp
    """
    entries = []

    try:
        # timestamps=True ajoute le timestamp Docker à chaque ligne
        raw_logs = container.logs(
            stdout=True,
            stderr=True,
            timestamps=True,
            tail=tail,
            stream=False
        )

        if not raw_logs:
            return entries

        lines = raw_logs.decode("utf-8", errors="replace").splitlines()

        for line in lines:
            if not line.strip():
                continue

            # Format Docker avec timestamp : "2026-04-18T10:00:00Z message..."
            log_timestamp = None
            message = line

            parts = line.split(" ", 1)
            if len(parts) == 2:
                try:
                    # Parse le timestamp ISO Docker
                    ts_str = parts[0].rstrip("Z").split(".")[0]
                    log_timestamp = datetime.fromisoformat(ts_str).replace(
                        tzinfo=timezone.utc
                    )
                    message = parts[1]
                except (ValueError, IndexError):
                    message = line

            entries.append({
                "message": message.strip(),
                "level": detect_log_level(message),
                "log_timestamp": log_timestamp,
            })

    except (NotFound, DockerException) as e:
        logger.warning(f"Erreur lecture logs container {container.name}: {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue lecture logs: {e}")

    return entries
