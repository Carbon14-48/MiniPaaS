from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .db import engine, Base
from .models.deployment import Deployment
from .routes import health, deployments, github

app = FastAPI(
    title="Deployer Service - MiniPaaS",
    description="Manages application deployments",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(deployments.router)
app.include_router(github.router)

@app.on_event("startup")
async def startup_event():
    if settings.ENV == "development":
        Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"service": "deployer-service", "status": "running"}
