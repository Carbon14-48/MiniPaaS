from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import health, deployments

app = FastAPI(
    title="Cloudoku Deployment Service",
    description="Deploys containers to Kubernetes, manages scaling and public URLs",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(deployments.router, prefix="/deployments", tags=["deployments"])


@app.get("/")
async def root():
    return {"service": "deployment-service", "status": "running"}
