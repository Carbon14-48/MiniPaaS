"""
models/job.py
-------------
Définit la table build_jobs dans PostgreSQL.

Chaque ligne dans cette table = un build demandé par un utilisateur.
C'est ce qu'on appelle un "job" : l'enregistrement complet d'une demande de build.

Exemple d'une ligne :
  job_id     = "a3f9c1b2-..."
  user_id    = 42
  repo_url   = "https://github.com/user42/myapp.git"
  app_name   = "myapp"
  branch     = "main"
  status     = "success"
  image_tag  = "user42/myapp:v1"
  image_url  = "registry:5000/user42/myapp:v1"
  build_logs = "Step 1/5 : FROM python:3.11-slim\n..."
  scan_result= {"critical": false, "vulnerabilities": [...]}
  created_at = 2026-04-05 18:00:00
  finished_at= 2026-04-05 18:02:34
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Enum as SAEnum
from src.db import Base
import enum


class BuildStatus(str, enum.Enum):
    """
    États possibles d'un build :
    - pending  : reçu, pas encore commencé
    - running  : en cours (clone + docker build)
    - success  : image buildée et poussée au registry
    - failed   : erreur pendant le clone ou le docker build
    - blocked  : CVE critique détectée par le scanner, push annulé
    """
    pending = "pending"
    running = "running"
    success = "success"
    failed  = "failed"
    blocked = "blocked"


class BuildJob(Base):
    """
    Table build_jobs : une ligne par demande de build.
    Alembic crée cette table dans PostgreSQL au premier lancement.
    """
    __tablename__ = "build_jobs"

    # Identifiant unique du build (UUID auto-généré)
    job_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # ID de l'utilisateur — récupéré depuis la réponse de l'auth-service
    user_id = Column(Integer, nullable=False, index=True)

    # URL du repo Git fournie par l'utilisateur
    repo_url = Column(String, nullable=False)

    # Nom de l'application (ex: "myapp")
    app_name = Column(String, nullable=False)

    # Branche Git à cloner (ex: "main")
    branch = Column(String, nullable=False, default="main")

    # Statut actuel du build
    status = Column(SAEnum(BuildStatus), nullable=False, default=BuildStatus.pending)

    # Tag Docker de l'image créée (ex: "user42/myapp:v1")
    # Null tant que le build n'est pas terminé
    image_tag = Column(String, nullable=True)

    # URL complète de l'image dans le registry (ex: "registry:5000/user42/myapp:v1")
    image_url = Column(String, nullable=True)

    # Logs complets du docker build — pour que l'utilisateur voie ce qui s'est passé
    build_logs = Column(Text, nullable=True)

    # Réponse JSON du scanner (vulnerabilities trouvées, critique ou non)
    scan_result = Column(JSON, nullable=True)

    # Date de création du job
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Date de fin du build (null tant que pas terminé)
    finished_at = Column(DateTime, nullable=True)
