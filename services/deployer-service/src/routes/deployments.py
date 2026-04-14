from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from ..db import get_db
from ..models.deployment import Deployment, DeploymentStatus
from ..services.auth_client import verify_token
from ..services.build_client import trigger_build, get_build_status
from ..services.docker_runner import docker_runner

router = APIRouter(prefix="/deployments", tags=["deployments"])


class DeploymentCreate(BaseModel):
    repo_url: str
    branch: str = "main"
    app_name: str


class DeploymentResponse(BaseModel):
    id: str
    user_id: int
    app_name: str
    repo_url: str
    branch: str
    status: str
    build_job_id: Optional[str] = None
    image_tag: Optional[str] = None
    image_url: Optional[str] = None
    container_id: Optional[str] = None
    container_url: Optional[str] = None
    host_port: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeploymentListResponse(BaseModel):
    deployments: list[DeploymentResponse]
    total: int


async def get_current_user_id(token: str) -> int:
    return await verify_token(token)


def get_token_from_header(authorization: str) -> str:
    if not authorization:
        raise ValueError("Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Invalid Authorization header format")
    return parts[1]


@router.post("/", response_model=DeploymentResponse, status_code=201)
async def create_deployment(
    deployment_req: DeploymentCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    token = get_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    
    deployment = Deployment(
        user_id=user_id,
        app_name=deployment_req.app_name,
        repo_url=deployment_req.repo_url,
        branch=deployment_req.branch,
        status=DeploymentStatus.BUILDING
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    
    try:
        build_result = await trigger_build(
            token=token,
            repo_url=deployment_req.repo_url,
            branch=deployment_req.branch,
            app_name=deployment_req.app_name
        )
        
        deployment.build_job_id = build_result.get("job_id")
        deployment.image_tag = build_result.get("image_tag")
        deployment.image_url = build_result.get("image_url")
        deployment.build_logs = build_result.get("build_logs")
        
        build_status = build_result.get("status")
        
        if build_status == "blocked":
            deployment.status = DeploymentStatus.BLOCKED
            deployment.error_message = build_result.get("reason", "Security scan blocked this build")
            db.commit()
            return deployment
        
        if build_status == "failed":
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = "Build failed"
            db.commit()
            return deployment
        
        if deployment.image_tag:
            try:
                container_info = docker_runner.run_container(
                    image_tag=deployment.image_tag,
                    app_name=deployment.app_name,
                    user_id=user_id
                )
                
                deployment.container_id = container_info["container_id"]
                deployment.host_port = container_info["host_port"]
                deployment.container_url = container_info["container_url"]
                deployment.status = DeploymentStatus.RUNNING
                deployment.started_at = datetime.utcnow()
            except Exception as e:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = f"Container start failed: {str(e)}"
        
        db.commit()
        return deployment
        
    except Exception as e:
        deployment.status = DeploymentStatus.FAILED
        deployment.error_message = str(e)
        db.commit()
        return deployment


@router.get("/", response_model=DeploymentListResponse)
async def list_deployments(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    token = get_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    
    deployments = db.query(Deployment).filter(
        Deployment.user_id == user_id,
        Deployment.is_active == True
    ).order_by(Deployment.created_at.desc()).all()
    
    return DeploymentListResponse(
        deployments=deployments,
        total=len(deployments)
    )


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    token = get_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.user_id == user_id
    ).first()
    
    if not deployment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    if deployment.container_id and deployment.status == DeploymentStatus.RUNNING:
        status = docker_runner.get_container_status(deployment.container_id)
        if status.get("status") == "not_found":
            deployment.status = DeploymentStatus.STOPPED
            deployment.stopped_at = datetime.utcnow()
            db.commit()
        elif status.get("status") == "running":
            deployment.status = DeploymentStatus.RUNNING
        elif status.get("status") == "exited":
            deployment.status = DeploymentStatus.STOPPED
            deployment.stopped_at = datetime.utcnow()
            db.commit()
    
    return deployment


@router.delete("/{deployment_id}", response_model=DeploymentResponse)
async def delete_deployment(
    deployment_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    token = get_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.user_id == user_id
    ).first()
    
    if not deployment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    if deployment.container_id:
        try:
            docker_runner.remove_container(deployment.container_id)
        except Exception:
            pass
    
    deployment.status = DeploymentStatus.STOPPED
    deployment.container_id = None
    deployment.stopped_at = datetime.utcnow()
    deployment.is_active = False
    
    db.commit()
    return deployment


@router.post("/{deployment_id}/stop", response_model=DeploymentResponse)
async def stop_deployment(
    deployment_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    token = get_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.user_id == user_id
    ).first()
    
    if not deployment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    if deployment.container_id:
        try:
            docker_runner.stop_container(deployment.container_id)
        except Exception:
            pass
    
    deployment.status = DeploymentStatus.STOPPED
    deployment.stopped_at = datetime.utcnow()
    
    db.commit()
    return deployment


@router.post("/{deployment_id}/start", response_model=DeploymentResponse)
async def start_deployment(
    deployment_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    token = get_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.user_id == user_id
    ).first()
    
    if not deployment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    if not deployment.image_tag:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No image available for this deployment")
    
    if deployment.status == DeploymentStatus.RUNNING and deployment.container_id:
        return deployment
    
    try:
        container_info = docker_runner.run_container(
            image_tag=deployment.image_tag,
            app_name=deployment.app_name,
            user_id=user_id
        )
        
        deployment.container_id = container_info["container_id"]
        deployment.host_port = container_info["host_port"]
        deployment.container_url = container_info["container_url"]
        deployment.status = DeploymentStatus.RUNNING
        deployment.started_at = datetime.utcnow()
        
        db.commit()
        return deployment
        
    except Exception as e:
        deployment.status = DeploymentStatus.FAILED
        deployment.error_message = str(e)
        db.commit()
        raise


@router.get("/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: str,
    authorization: str = Header(None),
    tail: int = 100,
    db: Session = Depends(get_db)
):
    token = get_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.user_id == user_id
    ).first()
    
    if not deployment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    if deployment.build_logs:
        return {"logs": deployment.build_logs, "source": "build"}
    
    if deployment.container_id:
        logs = docker_runner.get_container_logs(deployment.container_id, tail=tail)
        return {"logs": logs, "source": "container"}
    
    return {"logs": "No logs available", "source": "none"}


@router.post("/{deployment_id}/restart", response_model=DeploymentResponse)
async def restart_deployment(
    deployment_id: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    token = get_token_from_header(authorization)
    user_id = await get_current_user_id(token)
    
    deployment = db.query(Deployment).filter(
        Deployment.id == deployment_id,
        Deployment.user_id == user_id
    ).first()
    
    if not deployment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    if deployment.container_id:
        try:
            docker_runner.remove_container(deployment.container_id)
        except Exception:
            pass
    
    if not deployment.image_tag:
        if deployment.build_job_id:
            build_status = await get_build_status(token, deployment.build_job_id)
            deployment.image_tag = build_status.get("image_tag")
            deployment.image_url = build_status.get("image_url")
    
    if not deployment.image_tag:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No image available for redeployment")
    
    try:
        container_info = docker_runner.run_container(
            image_tag=deployment.image_tag,
            app_name=deployment.app_name,
            user_id=user_id
        )
        
        deployment.container_id = container_info["container_id"]
        deployment.host_port = container_info["host_port"]
        deployment.container_url = container_info["container_url"]
        deployment.status = DeploymentStatus.RUNNING
        deployment.started_at = datetime.utcnow()
        
        db.commit()
        return deployment
        
    except Exception as e:
        deployment.status = DeploymentStatus.FAILED
        deployment.error_message = str(e)
        db.commit()
        raise
