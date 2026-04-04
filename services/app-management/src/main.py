from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import health, apps

app = FastAPI(
    title="Cloudoku App Management Service",
    description="Manage application metadata and configurations",
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
app.include_router(apps.router, prefix="/apps", tags=["apps"])


@app.get("/")
async def root():
    return {"service": "app-management", "status": "running"}
