from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/apps")
async def list_apps():
    return {"message": "Proxy to app-management service"}


@router.post("/apps")
async def create_app():
    return {"message": "Proxy to app-management service"}


@router.get("/deployments")
async def list_deployments():
    return {"message": "Proxy to deployment service"}


@router.get("/logs/{app_id}")
async def get_logs(app_id: str):
    return {"message": f"Proxy to monitoring service for app {app_id}"}
