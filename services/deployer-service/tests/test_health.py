import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()


def test_deployments_requires_auth():
    response = client.get("/deployments/")
    assert response.status_code == 422


def test_repos_requires_auth():
    response = client.get("/repos/")
    assert response.status_code == 422
