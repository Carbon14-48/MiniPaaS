"""
tests/test_registry_route.py
-----------------------------
Tests des endpoints du registry-service.
On mocke les appels Docker — pas besoin d'un vrai daemon pendant les tests.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db import Base, get_db
from src.models.image import RegistryImage

# Base SQLite en mémoire pour les tests
SQLALCHEMY_TEST_URL = "sqlite:///./test_registry.db"
engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine_test)
client = TestClient(app)


# ─── Test 1 : health ─────────────────────────────────────────────────────────

def test_health():
    with patch("src.routes.registry.httpx") as mock_httpx:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_httpx.get.return_value = mock_resp
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ("ok", "degraded")


# ─── Test 2 : push image non existante localement ────────────────────────────

def test_push_image_not_found_locally():
    """Image absente du daemon Docker → 404."""
    with patch("src.routes.registry.push_to_registry") as mock_push:
        from fastapi import HTTPException
        mock_push.side_effect = HTTPException(
            status_code=404,
            detail="Image introuvable localement"
        )
        response = client.post("/push", json={
            "image_tag": "user42/ghost:v1",
            "user_id": 42,
            "app_name": "ghost"
        })
    assert response.status_code == 404


# ─── Test 3 : push réussi ────────────────────────────────────────────────────

def test_push_success():
    """Push réussi → 200 avec url + digest."""
    with patch("src.routes.registry.push_to_registry") as mock_push:
        mock_push.return_value = {
            "registry_url": "registry:5000/user42/myapp:v1",
            "digest": "sha256:abc123",
            "size_bytes": 45000000
        }
        response = client.post("/push", json={
            "image_tag": "user42/myapp:v1",
            "user_id": 42,
            "app_name": "myapp"
        })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Vérifie le contrat avec build-service : le champ doit s'appeler "url"
    assert "url" in data
    assert data["url"] == "registry:5000/user42/myapp:v1"
    assert data["digest"] == "sha256:abc123"


# ─── Test 4 : idempotence — push deux fois la même image ─────────────────────

def test_push_idempotent():
    """Pusher deux fois la même image → retourne already_exists."""
    with patch("src.routes.registry.push_to_registry") as mock_push:
        mock_push.return_value = {
            "registry_url": "registry:5000/user42/dupapp:v1",
            "digest": "sha256:dup123",
            "size_bytes": 10000
        }
        # Premier push
        client.post("/push", json={
            "image_tag": "user42/dupapp:v1",
            "user_id": 42,
            "app_name": "dupapp"
        })
        # Deuxième push — même image
        response = client.post("/push", json={
            "image_tag": "user42/dupapp:v1",
            "user_id": 42,
            "app_name": "dupapp"
        })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "already_exists"
    assert "url" in data  # le contrat est respecté même pour already_exists


# ─── Test 5 : liste images utilisateur vide ──────────────────────────────────

def test_get_user_images_empty():
    """Utilisateur sans images → liste vide."""
    response = client.get("/images/9999")
    assert response.status_code == 200
    assert response.json() == []


# ─── Test 6 : liste images utilisateur ───────────────────────────────────────

def test_get_user_images():
    """Après un push, l'image apparaît dans la liste."""
    with patch("src.routes.registry.push_to_registry") as mock_push:
        mock_push.return_value = {
            "registry_url": "registry:5000/user77/api:v1",
            "digest": "sha256:xyz",
            "size_bytes": 20000
        }
        client.post("/push", json={
            "image_tag": "user77/api:v1",
            "user_id": 77,
            "app_name": "api"
        })

    response = client.get("/images/77")
    assert response.status_code == 200
    images = response.json()
    assert len(images) >= 1
    assert images[0]["image_tag"] == "user77/api:v1"
    assert images[0]["registry_url"] == "registry:5000/user77/api:v1"


# ─── Test 7 : image par tag — introuvable ────────────────────────────────────

def test_get_image_by_tag_not_found():
    response = client.get("/images/tag/user42/inexistant:v99")
    assert response.status_code == 404


# ─── Test 8 : delete image ───────────────────────────────────────────────────

def test_delete_image():
    """Delete → soft delete, image n'apparaît plus dans la liste."""
    with patch("src.routes.registry.push_to_registry") as mock_push, \
         patch("src.routes.registry.delete_from_registry", return_value=True):

        mock_push.return_value = {
            "registry_url": "registry:5000/user55/todelete:v1",
            "digest": "sha256:del",
            "size_bytes": 5000
        }
        client.post("/push", json={
            "image_tag": "user55/todelete:v1",
            "user_id": 55,
            "app_name": "todelete"
        })

        response = client.delete("/images/user55/todelete:v1")

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    # L'image ne doit plus apparaître dans la liste
    list_resp = client.get("/images/55")
    tags = [img["image_tag"] for img in list_resp.json()]
    assert "user55/todelete:v1" not in tags


# ─── Test 9 : delete image inexistante ───────────────────────────────────────

def test_delete_image_not_found():
    response = client.delete("/images/user42/ghost:v99")
    assert response.status_code == 404


# ─── Test 10 : contrat champ "url" toujours présent ─────────────────────────

def test_push_response_always_has_url_field():
    """
    Le champ 'url' DOIT toujours être présent dans la réponse de /push.
    C'est le contrat avec build-service (registry_client.py fait .get('url')).
    """
    with patch("src.routes.registry.push_to_registry") as mock_push:
        mock_push.return_value = {
            "registry_url": "registry:5000/user99/contract:v1",
            "digest": "sha256:contract",
            "size_bytes": 1000
        }
        response = client.post("/push", json={
            "image_tag": "user99/contract:v1",
            "user_id": 99,
            "app_name": "contract"
        })

    assert "url" in response.json()
    assert "registry_url" not in response.json()  # pas ce nom — c'est "url"
