from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import health, builds

app = FastAPI(
    title="Cloudoku Build Service",
    description="Pulls source code, builds Docker images, stores in registry",
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
app.include_router(builds.router, prefix="/builds", tags=["builds"])


@app.get("/")
async def root():
    return {"service": "build-service", "status": "running"}
