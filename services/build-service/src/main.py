"""
main.py
-------
Point d'entrée du build-service.

Crée l'application FastAPI, enregistre les routes, et au démarrage
crée automatiquement les tables en base si elles n'existent pas.

Ce fichier est lancé par la commande :
  uvicorn src.main:app --host 0.0.0.0 --port 8002
"""

from fastapi import FastAPI
from src.db import engine, Base
from src.routes.build import router

# Importer les modèles pour qu'Alembic/SQLAlchemy les connaisse
from src.models import job  # noqa: F401

app = FastAPI(
    title="Build Service — MiniPaaS",
    description="Transforme du code source en image Docker prête à déployer.",
    version="1.0.0"
)


@app.on_event("startup")
def create_tables():
    """
    Crée toutes les tables en base au démarrage si elles n'existent pas.
    En production, utiliser Alembic (alembic upgrade head) à la place.
    """
    Base.metadata.create_all(bind=engine)


# Enregistre les routes du build
# Tous les endpoints seront accessibles sous /
# Ex: POST /build, GET /build/{job_id}
app.include_router(router)


@app.get("/health")
def health():
    """
    Endpoint de santé — appelé par Docker Compose pour savoir si le service
    est prêt à recevoir des requêtes.
    Retourne toujours 200 si le service tourne.
    """
    return {"status": "ok", "service": "build-service"}
