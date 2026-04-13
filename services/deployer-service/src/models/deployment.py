import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean
from ..db import Base


class DeploymentStatus(str, enum.Enum):
    PENDING = "pending"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    BLOCKED = "blocked"


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, nullable=False, index=True)
    app_name = Column(String(255), nullable=False)
    repo_url = Column(String(500), nullable=False)
    branch = Column(String(255), default="main")
    
    status = Column(
        Enum(DeploymentStatus),
        default=DeploymentStatus.PENDING,
        nullable=False
    )
    
    build_job_id = Column(String(36), nullable=True)
    image_tag = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    
    container_id = Column(String(255), nullable=True)
    container_port = Column(Integer, nullable=True)
    host_port = Column(Integer, nullable=True)
    container_url = Column(String(500), nullable=True)
    
    build_logs = Column(Text, nullable=True)
    deploy_logs = Column(Text, nullable=True)
    
    error_message = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
