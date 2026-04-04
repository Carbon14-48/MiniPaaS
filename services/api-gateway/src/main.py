from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import health, proxy

app = FastAPI(
    title="Cloudoku API Gateway",
    description="Entry point for all Cloudoku client requests",
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
app.include_router(proxy.router, prefix="/api", tags=["api"])


@app.get("/")
async def root():
    return {"service": "api-gateway", "status": "running"}
