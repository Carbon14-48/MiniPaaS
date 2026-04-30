from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.routes import health, proxy

app = FastAPI(
    title="MiniPaaS API Gateway",
    description="Unified entry point for all MiniPaaS services",
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
app.include_router(proxy.router, prefix="/api", tags=["proxy"])


@app.get("/")
async def root():
    return {"service": "api-gateway", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}