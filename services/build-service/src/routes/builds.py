from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class BuildRequest(BaseModel):
    app_id: int
    repo_url: str
    branch: str = "main"


class BuildResponse(BaseModel):
    id: int
    app_id: int
    status: str
    image_tag: str
    started_at: datetime
    completed_at: datetime | None = None


@router.post("/", response_model=BuildResponse)
async def trigger_build(request: BuildRequest):
    return {
        "id": 1,
        "app_id": request.app_id,
        "status": "building",
        "image_tag": f"{request.app_id}:latest",
        "started_at": datetime.utcnow(),
    }


@router.get("/{build_id}", response_model=BuildResponse)
async def get_build(build_id: int):
    return {
        "id": build_id,
        "app_id": 1,
        "status": "completed",
        "image_tag": "1:latest",
        "started_at": datetime.utcnow(),
        "completed_at": datetime.utcnow(),
    }


@router.get("/", response_model=list[BuildResponse])
async def list_builds():
    return []
