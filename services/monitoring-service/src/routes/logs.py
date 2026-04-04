from fastapi import APIRouter, Query
from datetime import datetime
from typing import Optional

router = APIRouter()


@router.get("/{app_id}")
async def get_logs(
    app_id: int,
    lines: int = Query(default=100, le=1000),
    start: Optional[str] = None,
    end: Optional[str] = None,
):
    return {
        "app_id": app_id,
        "logs": [
            {"timestamp": datetime.utcnow().isoformat(), "level": "INFO", "message": "Application started"},
            {"timestamp": datetime.utcnow().isoformat(), "level": "INFO", "message": "Listening on port 8000"},
        ],
    }


@router.get("/{app_id}/stream")
async def stream_logs(app_id: int):
    return {"message": "WebSocket stream endpoint", "app_id": app_id}
