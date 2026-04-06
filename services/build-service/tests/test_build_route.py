"""
tests/test_build_route.py
-------------------------
Tests des endpoints HTTP du build-service.

On ne teste PAS les vrais appels Docker ou Git ici.
On simule (mock) les services externes pour tester uniquement la logique des routes.

Lancer avec : pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db import Base, get_db
from src.models.job import BuildJob, BuildStatus

# ── Base de données SQLite en mémoire pour les tests ─────────────────────────
# On ne touche pas à la vraie base PostgreSQL pendant les tests
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine_test = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    """Remplace la vraie base PostgreSQL par SQLite en mémoire pendant les tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Crée les tables dans la base de test
Base.metadata.create_all(bind=engine_test)

client = TestClient(app)


# ── Test 1 : health check ─────────────────────────────────────────────────────

def test_health():
    """Le service doit répondre 200 sur /health."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── Test 2 : build sans header Authorization ──────────────────────────────────

def test_build_missing_auth_header():
    """Sans header Authorization, doit retourner 422 (champ manquant)."""
    response = client.post("/build", json={
        "repo_url": "https://github.com/user42/myapp.git",
        "branch": "main",
        "app_name": "myapp"
    })
    assert response.status_code == 422


# ── Test 3 : build avec token invalide ───────────────────────────────────────

def test_build_invalid_token():
    """Token invalide → auth-service répond valid=false → 401."""
    with patch("src.routes.build.verify_token", new_callable=AsyncMock) as mock_auth:
        from fastapi import HTTPException
        mock_auth.side_effect = HTTPException(status_code=401, detail="Token invalide")

        response = client.post(
            "/build",
            json={"repo_url": "https://github.com/u/app.git", "branch": "main", "app_name": "app"},
            headers={"Authorization": "Bearer token_invalide"}
        )
        assert response.status_code == 401


# ── Test 4 : build complet réussi ────────────────────────────────────────────

def test_build_success():
    """
    Simule un build complet réussi :
    auth OK → clone OK → dockerfile OK → build OK → scan OK → push OK
    """
    with patch("src.routes.build.verify_token", new_callable=AsyncMock) as mock_auth, \
         patch("src.routes.build.clone_repo") as mock_clone, \
         patch("src.routes.build.detect_and_prepare_dockerfile") as mock_dockerfile, \
         patch("src.routes.build.build_image") as mock_build, \
         patch("src.routes.build.scan_image", new_callable=AsyncMock) as mock_scan, \
         patch("src.routes.build.push_image", new_callable=AsyncMock) as mock_push, \
         patch("src.routes.build.cleanup_repo") as mock_cleanup:

        mock_auth.return_value = 42
        mock_clone.return_value = "/tmp/builds/test_job"
        mock_dockerfile.return_value = "python"
        mock_build.return_value = ("user42/myapp:v1", "Step 1/5: FROM python:3.11-slim")
        mock_scan.return_value = {"critical": False, "vulnerabilities": []}
        mock_push.return_value = {
            "url": "registry:5000/user42/myapp:v1",
            "digest": "sha256:abc123"
        }

        response = client.post(
            "/build",
            json={"repo_url": "https://github.com/user42/myapp.git", "branch": "main", "app_name": "myapp"},
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["image_tag"] == "user42/myapp:v1"
        assert data["image_url"] == "registry:5000/user42/myapp:v1"
        assert mock_cleanup.called  # le dossier temp doit toujours être nettoyé


# ── Test 5 : build bloqué par CVE critique ───────────────────────────────────

def test_build_blocked_by_scanner():
    """
    Le scanner détecte une CVE critique → build bloqué, image non pushée.
    """
    with patch("src.routes.build.verify_token", new_callable=AsyncMock) as mock_auth, \
         patch("src.routes.build.clone_repo") as mock_clone, \
         patch("src.routes.build.detect_and_prepare_dockerfile") as mock_dockerfile, \
         patch("src.routes.build.build_image") as mock_build, \
         patch("src.routes.build.scan_image", new_callable=AsyncMock) as mock_scan, \
         patch("src.routes.build.push_image", new_callable=AsyncMock) as mock_push, \
         patch("src.routes.build.cleanup_repo"):

        mock_auth.return_value = 42
        mock_clone.return_value = "/tmp/builds/test_job"
        mock_dockerfile.return_value = "python"
        mock_build.return_value = ("user42/myapp:v1", "Step 1/5...")
        mock_scan.return_value = {
            "critical": True,
            "cve": "CVE-2024-1234",
            "severity": "CRITICAL",
            "package": "libssl 1.0.1"
        }

        response = client.post(
            "/build",
            json={"repo_url": "https://github.com/user42/myapp.git", "branch": "main", "app_name": "myapp"},
            headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blocked"
        assert "CVE-2024-1234" in data["reason"]
        # Le push ne doit JAMAIS être appelé si le scan bloque
        mock_push.assert_not_called()


# ── Test 6 : GET /build/{job_id} introuvable ─────────────────────────────────

def test_get_build_not_found():
    """Un job_id inexistant doit retourner 404."""
    with patch("src.routes.build.verify_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = 1
        response = client.get(
            "/build/job_inexistant",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 404


# ── Test 7 : GET /build/user/{user_id} vide ──────────────────────────────────

def test_get_user_builds_empty():
    """Un utilisateur sans builds doit recevoir une liste vide."""
    with patch("src.routes.build.verify_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = 9999
        response = client.get(
            "/build/me",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200
        assert response.json() == []


def test_get_user_builds_forbidden_when_not_owner():
    with patch("src.routes.build.verify_token", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = 42
        response = client.get(
            "/build/user/9999",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 403
