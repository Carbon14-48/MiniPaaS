"""
config.py
---------
Lit les variables d'environnement depuis .env ou l'environnement système.
Toute la configuration du service est centralisée ici.
Importer Settings() dans les autres fichiers pour accéder aux valeurs.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # URLs des autres microservices
    auth_service_url: str = "http://auth-service:8001"
    scanner_service_url: str = "http://security-scanner:8003"
    registry_service_url: str = "http://registry-service:8005"

    # Base de données
    database_url: str = "postgresql://builduser:buildpass@build-db:5432/builddb"

    # Dossier temporaire pour les clones Git
    build_workdir: str = "/tmp/builds"

    # Timeout du docker build en secondes
    max_build_timeout: int = 300

    # Environnement
    env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instance unique réutilisée partout dans le service
settings = Settings()
