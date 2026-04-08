"""
main.py
-------
Point d'entrée du registry-service.
Lance FastAPI, branche les routes, crée les tables en dev.
"""
from fastapi import FastAPI
from src.db import engine, Base
from src.routes.registry import router
from src.config import settings
from src.models import image  # noqa: F401 — nécessaire pour SQLAlchemy

app = FastAPI(
    title="Registry Service — MiniPaaS",
    description="Stocke et gère les images Docker des utilisateurs.",
    version="1.0.0"
)


@app.on_event("startup")
def on_startup():
    """
    En développement : crée les tables automatiquement.
    En production : utiliser alembic upgrade head.
    """
    if settings.env == "development":
        Base.metadata.create_all(bind=engine)


app.include_router(router)
