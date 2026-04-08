"""
config.py
---------
Toute la configuration du registry-service lue depuis .env
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Host du registry local SANS http:// — utilisé pour docker tag/push
    registry_host: str = "registry:5000"

    # URL complète du registry — utilisée pour les health checks HTTP
    registry_url: str = "http://registry:5000"

    # Base de données propre au registry-service
    database_url: str = "postgresql://registryuser:registrypass@registry-db:5432/registrydb"

    # Environnement
    env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
