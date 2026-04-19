"""
config.py
---------
Configuration du monitoring-service.
Toutes les variables lues depuis .env ou l'environnement Docker.

Ce service n'appelle AUCUN autre microservice en HTTP.
Il lit uniquement le Docker daemon via le SDK Python.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de données propre au monitoring-service
    database_url: str = "postgresql://monitoruser:monitorpass@monitor-db:5432/monitordb"

    # Intervalle de collecte des métriques en secondes
    # Toutes les 30s on collecte CPU/RAM de tous les containers actifs
    collect_interval_seconds: int = 30

    # Nombre de jours de rétention des métriques en base
    # Au-delà, les anciennes métriques sont supprimées automatiquement
    metrics_retention_days: int = 7

    # Nombre de lignes max retournées pour les logs d'un container
    log_tail_lines: int = 100

    # Environnement
    env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
