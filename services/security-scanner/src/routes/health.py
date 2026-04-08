from fastapi import APIRouter

from src.models.scan_result import HealthResponse, ToolStatus

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="security-scanner",
        version="2.0.0",
    )
