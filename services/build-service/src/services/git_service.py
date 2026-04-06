"""
services/git_service.py
-----------------------
FICHIER PYTHON INTERNE AU BUILD-SERVICE — pas un microservice.

Son unique rôle : cloner le repo Git d'un utilisateur dans un dossier temporaire.

Flux :
  build-service reçoit { "repo_url": "https://github.com/user42/myapp.git", "branch": "main" }
      ↓
  clone_repo("https://github.com/user42/myapp.git", "job_a3f9c1", "main") appelé ici
      ↓
  git clone https://github.com/user42/myapp.git /tmp/builds/job_a3f9c1/
      ↓
  Retourne le chemin "/tmp/builds/job_a3f9c1/" au service appelant

Le dossier /tmp/builds/job_a3f9c1/ contiendra alors :
  ├── main.py
  ├── requirements.txt
  ├── README.md
  └── ... (tout le code de l'utilisateur)
"""

import os
import shutil
from git import Repo, GitCommandError
from fastapi import HTTPException, status
from src.config import settings


def clone_repo(repo_url: str, job_id: str, branch: str = "main") -> str:
    """
    Clone un repo Git dans /tmp/builds/<job_id>/.

    Paramètres :
        repo_url : URL publique du repo (ex: https://github.com/user/app.git)
        job_id   : identifiant unique du build (sert de nom de dossier)
        branch   : branche à cloner (défaut: main)

    Retourne :
        chemin absolu du dossier cloné (ex: "/tmp/builds/job_a3f9c1")

    Lève :
        HTTPException 400 : si le repo n'existe pas ou est inaccessible
        HTTPException 500 : erreur Git inattendue
    """
    # Construit le chemin de destination
    # Ex: /tmp/builds/job_a3f9c1
    clone_path = os.path.join(settings.build_workdir, job_id)

    # Crée le dossier parent /tmp/builds/ s'il n'existe pas
    os.makedirs(settings.build_workdir, exist_ok=True)

    # Si le dossier existe déjà (retry), on le supprime d'abord
    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)

    try:
        # Clone le repo sur la branche demandée
        # depth=1 = ne prend que le dernier commit (plus rapide, moins lourd)
        Repo.clone_from(
            repo_url,
            clone_path,
            branch=branch,
            depth=1
        )
    except GitCommandError as e:
        # Repo introuvable, URL incorrecte, repo privé sans accès, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de cloner le repo : {str(e)}"
        )

    return clone_path


def cleanup_repo(job_id: str) -> None:
    """
    Supprime le dossier temporaire après le build (libère l'espace disque).
    Appelé après le push vers le registry, qu'il y ait succès ou échec.

    Paramètre :
        job_id : identifiant du build dont on veut supprimer le dossier
    """
    clone_path = os.path.join(settings.build_workdir, job_id)
    if os.path.exists(clone_path):
        shutil.rmtree(clone_path)
