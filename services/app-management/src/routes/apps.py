from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class AppCreate(BaseModel):
    name: str
    repo_url: str
    branch: str = "main"
    env_vars: dict = {}


class AppResponse(BaseModel):
    id: int
    name: str
    repo_url: str
    branch: str
    status: str
    public_url: Optional[str] = None
    created_at: datetime


@router.get("/", response_model=list[AppResponse])
async def list_apps():
    return []


@router.post("/", response_model=AppResponse)
async def create_app(app: AppCreate):
    return {
        "id": 1,
        "name": app.name,
        "repo_url": app.repo_url,
        "branch": app.branch,
        "status": "created",
        "created_at": datetime.utcnow(),
    }


@router.get("/{app_id}", response_model=AppResponse)
async def get_app(app_id: int):
    return {
        "id": app_id,
        "name": "sample-app",
        "repo_url": "https://github.com/user/sample-app",
        "branch": "main",
        "status": "running",
        "public_url": "https://sample-app.cloudoku.app",
        "created_at": datetime.utcnow(),
    }


@router.delete("/{app_id}")
async def delete_app(app_id: int):
    return {"message": f"App {app_id} deleted"}
