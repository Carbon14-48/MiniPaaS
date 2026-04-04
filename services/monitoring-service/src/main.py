from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import health, logs, metrics

app = FastAPI(
    title="Cloudoku Monitoring Service",
    description="Collects logs, tracks metrics, and displays data in dashboard",
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
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])


@app.get("/")
async def root():
    return {"service": "monitoring-service", "status": "running"}
