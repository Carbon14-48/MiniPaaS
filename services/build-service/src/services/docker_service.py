"""
services/docker_service.py
--------------------------
FICHIER PYTHON INTERNE AU BUILD-SERVICE — pas un microservice.

Responsabilités :
  1. Chercher un Dockerfile dans le repo cloné
  2. Si absent : détecter le langage et générer un Dockerfile adapté
  3. Lancer docker build et capturer les logs
  4. Retourner le tag de l'image et les logs

Flux concret :
  Après git clone → dossier /tmp/builds/job_a3f9c1/ contient le code
      ↓
  detect_and_prepare_dockerfile("/tmp/builds/job_a3f9c1/") appelé
      → cherche Dockerfile à la racine du dossier
      → si absent, analyse les fichiers présents et écrit un Dockerfile
      ↓
  build_image("/tmp/builds/job_a3f9c1/", "user42/myapp", 1) appelé
      → docker build -t user42/myapp:v1 /tmp/builds/job_a3f9c1/
      → capture et retourne les logs ligne par ligne
"""

import os
import docker
from docker.errors import BuildError, DockerException
from fastapi import HTTPException, status


# Dockerfiles pré-écrits par langage détecté
# Utilisés si l'utilisateur n'a pas fourni son propre Dockerfile

DOCKERFILE_PYTHON = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

DOCKERFILE_NODE = """FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production || npm install
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "node index.js || node server.js || node app.js || npx serve -s . -l 8000"]
"""

DOCKERFILE_JAVA = """FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
"""


def detect_and_prepare_dockerfile(repo_path: str) -> str:
    """
    Cherche un Dockerfile dans le repo cloné.
    S'il n'existe pas, détecte le langage et en génère un automatiquement.

    Paramètre :
        repo_path : chemin absolu du repo cloné (ex: "/tmp/builds/job_a3f9c1")

    Retourne :
        le langage détecté ("python", "node", "java", "custom")

    Lève :
        HTTPException 400 : si aucun langage détectable et pas de Dockerfile
    """
    dockerfile_path = os.path.join(repo_path, "Dockerfile")

    # Cas 1 : l'utilisateur a fourni son propre Dockerfile → on l'utilise tel quel
    if os.path.exists(dockerfile_path):
        return "custom"

    # Cas 2 : pas de Dockerfile → détection du langage par les fichiers présents
    files = os.listdir(repo_path)

    if "requirements.txt" in files or any(f.endswith(".py") for f in files):
        # Repo Python détecté
        _write_dockerfile(dockerfile_path, DOCKERFILE_PYTHON)
        return "python"

    if "package.json" in files:
        # Repo Node.js détecté
        _write_dockerfile(dockerfile_path, DOCKERFILE_NODE)
        return "node"

    if "pom.xml" in files:
        # Repo Java/Maven détecté
        _write_dockerfile(dockerfile_path, DOCKERFILE_JAVA)
        return "java"

    # Aucun langage détecté et pas de Dockerfile → on ne peut pas builder
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Impossible de détecter le langage du projet. "
            "Ajoute un Dockerfile à la racine de ton repo, "
            "ou assure-toi d'avoir requirements.txt (Python), "
            "package.json (Node.js) ou pom.xml (Java)."
        )
    )


def _write_dockerfile(path: str, content: str) -> None:
    """Écrit le Dockerfile généré dans le dossier du repo."""
    with open(path, "w") as f:
        f.write(content)


def build_image(repo_path: str, app_name: str, user_id: int, build_number: int) -> tuple[str, str]:
    """
    Lance docker build sur le dossier du repo et retourne le tag + les logs.

    Le tag de l'image suit le format : user{user_id}/{app_name}:v{build_number}
    Exemple : user42/myapp:v1

    Paramètres :
        repo_path    : chemin du dossier contenant le Dockerfile
        app_name     : nom de l'app fourni par l'utilisateur
        user_id      : ID de l'utilisateur (pour le tag)
        build_number : numéro de version (1, 2, 3...)

    Retourne :
        tuple (image_tag, build_logs)
        - image_tag  : ex "user42/myapp:v1"
        - build_logs : tous les logs du docker build en une seule string

    Lève :
        HTTPException 500 : si docker build échoue
    """
    image_tag = f"user{user_id}/{app_name}:v{build_number}"

    try:
        client = docker.from_env()

        # docker build retourne (image, generator_de_logs)
        image, log_generator = client.images.build(
            path=repo_path,
            tag=image_tag,
            rm=True,        # supprime les containers intermédiaires après build
            forcerm=True,   # supprime même si le build échoue
        )

        # Capture tous les logs ligne par ligne
        logs_lines = []
        for log in log_generator:
            if "stream" in log:
                line = log["stream"].strip()
                if line:
                    logs_lines.append(line)

        build_logs = "\n".join(logs_lines)
        return image_tag, build_logs

    except BuildError as e:
        # docker build a échoué (erreur dans le Dockerfile, dépendance manquante, etc.)
        error_logs = "\n".join(
            log.get("stream", "").strip()
            for log in e.build_log
            if log.get("stream", "").strip()
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docker build échoué :\n{error_logs}"
        )

    except DockerException as e:
        # Docker daemon injoignable ou autre erreur Docker
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur Docker : {str(e)}"
        )
