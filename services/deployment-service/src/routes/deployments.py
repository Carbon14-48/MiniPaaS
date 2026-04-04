from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter()


class DeployRequest(BaseModel):
    app_id: int
    image_tag: str
    replicas: int = 1
    env_vars: dict = {}


class DeployResponse(BaseModel):
    id: int
    app_id: int
    status: str
    replicas: int
    public_url: str
    deployed_at: datetime


class ScaleRequest(BaseModel):
    replicas: int


@router.post("/", response_model=DeployResponse)
async def deploy(request: DeployRequest):
    return {
        "id": 1,
        "app_id": request.app_id,
        "status": "deploying",
        "replicas": request.replicas,
        "public_url": f"https://app-{request.app_id}.cloudoku.app",
        "deployed_at": datetime.utcnow(),
    }


@router.get("/", response_model=list[DeployResponse])
async def list_deployments():
    return []


@router.get("/{deployment_id}", response_model=DeployResponse)
async def get_deployment(deployment_id: int):
    return {
        "id": deployment_id,
        "app_id": 1,
        "status": "running",
        "replicas": 1,
        "public_url": "https://app-1.cloudoku.app",
        "deployed_at": datetime.utcnow(),
    }


@router.post("/{deployment_id}/scale")
async def scale_deployment(deployment_id: int, request: ScaleRequest):
    return {
        "id": deployment_id,
        "replicas": request.replicas,
        "status": "scaled",
    }
