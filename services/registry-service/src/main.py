"""
src/main.py
-----------
Point d'entrée du registry-service.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes.health import router as health_router
from src.routes.push import router as push_router

logging.basicConfig(level=settings.log_level)

app = FastAPI(title="registry-service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(push_router)
