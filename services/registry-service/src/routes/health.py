"""
routes/health.py
----------------
Santé du service.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "registry-service"}
