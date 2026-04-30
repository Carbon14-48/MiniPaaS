"""
services/docker_collector.py
-----------------------------
Collecte les métriques des containers Docker via le Docker SDK Python.

Ce fichier est le coeur du monitoring-service.
Il communique UNIQUEMENT avec le daemon Docker local via le socket.
Il n'appelle AUCUN autre microservice MiniPaaS.

Comment ça marche :
  Le deployer-service crée des containers avec des labels Docker.
  On filtre les containers par le label "minipaas=true" pour ne
  monitorer que les apps utilisateurs, pas les services internes.

  Si le deployer-service ne met pas encore de labels, on filtre
  par convention de nommage (containers dont le nom commence par
  "minipaas_") — les deux stratégies coexistent sans conflit.
"""

import docker
from docker.errors import DockerException, NotFound
from datetime import datetime, timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_docker_client():
    """
    Retourne un client Docker.
    Retourne None si le daemon est injoignable (ne lève pas d'exception)
    pour que le scheduler continue de tourner même si Docker redémarre.
    """
    try:
        client = docker.from_env()
        client.ping()
        return client
    except DockerException as e:
        logger.warning(f"Docker daemon injoignable : {e}")
        return None


def _calculate_cpu_percent(stats: dict) -> Optional[float]:
    """
    Calcule le pourcentage CPU depuis les stats Docker brutes.

    Docker retourne des compteurs cumulatifs — il faut calculer
    le delta entre deux mesures pour obtenir un pourcentage.
    L'API stats avec stream=False fait deux snapshots automatiquement.
    """
    try:
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = (
            stats["cpu_stats"]["system_cpu_usage"]
            - stats["precpu_stats"]["system_cpu_usage"]
        )
        num_cpus = stats["cpu_stats"].get("online_cpus") or len(
            stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [1])
        )
        if system_delta > 0 and cpu_delta >= 0:
            return round((cpu_delta / system_delta) * num_cpus * 100.0, 2)
    except (KeyError, ZeroDivisionError, TypeError):
        pass
    return None


def _extract_network_stats(stats: dict) -> tuple[Optional[int], Optional[int]]:
    """
    Extrait les bytes réseau reçus et envoyés.
    Retourne (rx_bytes, tx_bytes).
    """
    try:
        networks = stats.get("networks", {})
        if networks:
            rx = sum(v.get("rx_bytes", 0) for v in networks.values())
            tx = sum(v.get("tx_bytes", 0) for v in networks.values())
            return rx, tx
    except (KeyError, TypeError, AttributeError):
        pass
    return None, None


def collect_container_stats(container) -> Optional[dict]:
    """
    Collecte les métriques d'un container Docker spécifique.

    Paramètre :
        container : objet Container du Docker SDK

    Retourne :
        dict avec cpu_percent, memory_usage_bytes, memory_limit_bytes,
        memory_percent, network_rx_bytes, network_tx_bytes, status
        ou None si la collecte échoue
    """
    try:
        # stream=False retourne un seul snapshot avec pre/cpu_stats
        stats = container.stats(stream=False)
        status = container.status

        # CPU
        cpu_percent = _calculate_cpu_percent(stats)

        # Mémoire
        mem_stats = stats.get("memory_stats", {})
        mem_usage = mem_stats.get("usage")
        mem_limit = mem_stats.get("limit")
        mem_percent = None
        if mem_usage and mem_limit and mem_limit > 0:
            mem_percent = round((mem_usage / mem_limit) * 100.0, 2)

        # Réseau
        rx_bytes, tx_bytes = _extract_network_stats(stats)

        return {
            "cpu_percent": cpu_percent,
            "memory_usage_bytes": mem_usage,
            "memory_limit_bytes": mem_limit,
            "memory_percent": mem_percent,
            "network_rx_bytes": rx_bytes,
            "network_tx_bytes": tx_bytes,
            "status": status,
        }

    except (NotFound, DockerException) as e:
        logger.warning(f"Erreur collecte stats container {container.name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue collecte stats: {e}")
        return None


def get_monitored_containers(client) -> list:
    """
    Retourne la liste des containers à monitorer.

    Stratégie double (pour compatibilité avec deployer-service actuel et futur) :
      1. Containers avec label "minipaas=true" (stratégie propre)
      2. Containers dont le nom commence par "minipaas_" (convention nommage)

    Les containers des services internes MiniPaaS (build-service, auth-service,
    registry-service, etc.) ne sont PAS inclus — on monitore uniquement
    les apps déployées par les utilisateurs.
    """
    monitored = {}

    # Stratégie 1 : label minipaas=true
    try:
        labeled = client.containers.list(
            filters={"label": "minipaas=true", "status": "running"}
        )
        for c in labeled:
            monitored[c.id] = c
    except DockerException:
        pass

    # Stratégie 2 : convention de nommage minipaas_
    try:
        all_running = client.containers.list(filters={"status": "running"})
        for c in all_running:
            name = c.name.lstrip("/")
            if name.startswith("minipaas_") and c.id not in monitored:
                monitored[c.id] = c
    except DockerException:
        pass

    return list(monitored.values())


def parse_container_identity(container) -> dict:
    """
    Extrait app_id et user_id depuis un container.

    Priorité :
      1. Labels Docker (si deployer-service les met)
         Labels attendus : minipaas.app_id, minipaas.user_id
      2. Convention de nommage : minipaas_{user_id}_{app_name}
         Ex: minipaas_42_myapp → user_id=42, app_id=myapp

    Retourne dict avec app_id, user_id et container_id
    """
    labels = container.labels or {}
    name = container.name.lstrip("/")
    container_id = container.short_id

    # Priorité 1 : labels
    app_id = labels.get("minipaas.app_id")
    user_id_str = labels.get("minipaas.user_id", "0")

    if app_id:
        return {"app_id": app_id, "user_id": int(user_id_str), "container_id": container_id}

    # Priorité 2 : convention minipaas_{user_id}_{app_name} ou minipaas-{user_id}-{app_name}
    if name.startswith("minipaas-"):
        parts = name.split("-", 2)
        if len(parts) >= 3:
            try:
                return {"app_id": "-".join(parts[2:]), "user_id": int(parts[1]), "container_id": container_id}
            except ValueError:
                pass
    elif name.startswith("minipaas_"):
        parts = name.split("_", 2)
        if len(parts) >= 3:
            try:
                return {"app_id": parts[2], "user_id": int(parts[1]), "container_id": container_id}
            except ValueError:
                pass
        elif len(parts) == 2:
            return {"app_id": parts[1], "user_id": 0, "container_id": container_id}

    # Fallback : nom complet comme app_id
    return {"app_id": name, "user_id": 0, "container_id": container_id}
