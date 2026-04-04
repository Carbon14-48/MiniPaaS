from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import health, scans

app = FastAPI(
    title="Cloudoku Security Scanner",
    description="Scans code and Docker images for vulnerabilities",
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
app.include_router(scans.router, prefix="/scans", tags=["scans"])


@app.get("/")
async def root():
    return {"service": "security-scanner", "status": "running"}
