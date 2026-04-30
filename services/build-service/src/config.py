"""
config.py
---------
Lit les variables d'environnement depuis .env ou l'environnement système.
Toute la configuration du service est centralisée ici.
Importer Settings() dans les autres fichiers pour accéder aux valeurs.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    auth_service_url: str = "http://auth-service:8000"
    scanner_service_url: str = "http://security-scanner:8000"
    registry_service_url: str = "http://registry-service:8005"
    
    # Override registry host - use Docker Hub for testing
    registry_push_url: str = ""  # If empty, push to local registry

    database_url: str = "postgresql://minipaas:minipaas@postgres:5432/minipaas"

    build_workdir: str = "/tmp/builds"

    max_build_timeout: int = 300

    env: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Instance unique réutilisée partout dans le service
settings = Settings()
