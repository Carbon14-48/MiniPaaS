"""
main.py
-------
Point d'entrée du monitoring-service.

Ce service est ENTIÈREMENT PASSIF vis-à-vis des autres microservices :
  - Il n'appelle AUCUN autre service MiniPaaS (auth, build, registry, scanner)
  - Il ne modifie RIEN dans les autres services
  - Il observe uniquement le Docker daemon en lecture seule
  - Les autres services n'ont PAS besoin de le connaître pour fonctionner

Il peut donc être ajouté ou retiré sans impacter auth/build/registry/scanner.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.db import engine, Base
from src.config import settings
from src.routes import metrics, logs, health
from src.services.scheduler import start_scheduler, stop_scheduler

# Import des modèles pour que SQLAlchemy les connaisse
from src.models import metric, log_entry  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    Démarre le scheduler au lancement, l'arrête proprement à l'extinction.
    """
    # Startup
    if settings.env == "development":
        Base.metadata.create_all(bind=engine)

    start_scheduler()

    yield  # L'application tourne ici

    # Shutdown
    stop_scheduler()


app = FastAPI(
    title="Monitoring Service — MiniPaaS",
    description=(
        "Collecte et expose les métriques et logs des applications déployées. "
        "Expose /metrics au format Prometheus pour intégration Grafana."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Enregistrement des routes
app.include_router(metrics.router)
app.include_router(logs.router)
app.include_router(health.router)
