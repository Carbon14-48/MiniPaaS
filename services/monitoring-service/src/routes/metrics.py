from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/{app_id}")
async def get_metrics(app_id: int):
    return {
        "app_id": app_id,
        "cpu_usage": "12.5%",
        "memory_usage": "256MB",
        "response_time": "45ms",
        "requests_per_minute": 120,
        "uptime": "99.9%",
        "last_updated": datetime.utcnow().isoformat(),
    }


@router.get("/")
async def get_all_metrics():
    return {
        "total_apps": 0,
        "total_requests": 0,
        "avg_response_time": "50ms",
    }
