from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter()


class ScanRequest(BaseModel):
    app_id: int
    image_tag: Optional[str] = None
    repo_url: Optional[str] = None


class Vulnerability(BaseModel):
    id: str
    severity: str
    package: str
    description: str


class ScanResponse(BaseModel):
    id: int
    app_id: int
    status: str
    vulnerabilities: list[Vulnerability]
    scanned_at: datetime


@router.post("/image", response_model=ScanResponse)
async def scan_image(request: ScanRequest):
    return {
        "id": 1,
        "app_id": request.app_id,
        "status": "completed",
        "vulnerabilities": [],
        "scanned_at": datetime.utcnow(),
    }


@router.post("/code", response_model=ScanResponse)
async def scan_code(request: ScanRequest):
    return {
        "id": 1,
        "app_id": request.app_id,
        "status": "completed",
        "vulnerabilities": [],
        "scanned_at": datetime.utcnow(),
    }


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: int):
    return {
        "id": scan_id,
        "app_id": 1,
        "status": "completed",
        "vulnerabilities": [],
        "scanned_at": datetime.utcnow(),
    }
