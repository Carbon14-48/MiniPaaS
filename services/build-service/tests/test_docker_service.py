"""
tests/test_docker_service.py
-----------------------------
Tests de la détection de langage et génération de Dockerfile.
On teste la logique Python pure — pas le vrai Docker daemon.

Lancer avec : pytest tests/test_docker_service.py -v
"""

import os
import pytest
import tempfile
from fastapi import HTTPException

from src.services.docker_service import detect_and_prepare_dockerfile


def test_detects_existing_dockerfile():
    """Si un Dockerfile existe déjà, on le garde tel quel (retourne 'custom')."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crée un Dockerfile dans le dossier temporaire
        dockerfile_path = os.path.join(tmpdir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write("FROM ubuntu:22.04\n")

        result = detect_and_prepare_dockerfile(tmpdir)
        assert result == "custom"

        # Vérifie que le contenu n'a pas été modifié
        with open(dockerfile_path) as f:
            content = f.read()
        assert "FROM ubuntu:22.04" in content


def test_detects_python_by_requirements():
    """requirements.txt trouvé → génère un Dockerfile Python."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crée un requirements.txt (repo Python sans Dockerfile)
        with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
            f.write("fastapi==0.111.0\nuvicorn==0.29.0\n")

        result = detect_and_prepare_dockerfile(tmpdir)
        assert result == "python"

        # Le Dockerfile doit avoir été créé
        dockerfile_path = os.path.join(tmpdir, "Dockerfile")
        assert os.path.exists(dockerfile_path)

        with open(dockerfile_path) as f:
            content = f.read()
        assert "FROM python" in content
        assert "requirements.txt" in content


def test_detects_node_by_package_json():
    """package.json trouvé → génère un Dockerfile Node.js."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"name": "myapp", "version": "1.0.0"}')

        result = detect_and_prepare_dockerfile(tmpdir)
        assert result == "node"

        with open(os.path.join(tmpdir, "Dockerfile")) as f:
            content = f.read()
        assert "FROM node" in content
        assert "npm install" in content


def test_detects_java_by_pom_xml():
    """pom.xml trouvé → génère un Dockerfile Java/Maven."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "pom.xml"), "w") as f:
            f.write("<project></project>")

        result = detect_and_prepare_dockerfile(tmpdir)
        assert result == "java"

        with open(os.path.join(tmpdir, "Dockerfile")) as f:
            content = f.read()
        assert "FROM maven" in content


def test_raises_error_when_no_language_detected():
    """Aucun fichier reconnu et pas de Dockerfile → HTTPException 400."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Dossier vide — aucun fichier reconnaissable
        with open(os.path.join(tmpdir, "random.txt"), "w") as f:
            f.write("contenu quelconque")

        with pytest.raises(HTTPException) as exc_info:
            detect_and_prepare_dockerfile(tmpdir)

        assert exc_info.value.status_code == 400
        assert "Dockerfile" in exc_info.value.detail


def test_python_detected_by_py_extension():
    """Un fichier .py trouvé (sans requirements.txt) → détecte Python."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("print('hello')")

        result = detect_and_prepare_dockerfile(tmpdir)
        assert result == "python"
