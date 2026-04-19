"""
tests/test_metrics_route.py
----------------------------
Tests des endpoints métriques.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from src.main import app
from src.db import Base, get_db
from src.models.metric import ContainerMetric

SQLALCHEMY_TEST_URL = "sqlite:///./test_monitoring.db"
engine_test = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine_test)
client = TestClient(app)


def _insert_metric(app_id="myapp", user_id=42, cpu=23.5, mem_pct=45.0):
    """Insère une métrique de test directement en base."""
    db = TestingSessionLocal()
    m = ContainerMetric(
        app_id=app_id,
        user_id=user_id,
        container_name=f"minipaas_{user_id}_{app_id}",
        container_id="abc123",
        cpu_percent=cpu,
        memory_usage_bytes=512 * 1024 * 1024,
        memory_limit_bytes=1024 * 1024 * 1024,
        memory_percent=mem_pct,
        network_rx_bytes=1024000,
        network_tx_bytes=512000,
        status="running",
        collected_at=datetime.now(timezone.utc),
    )
    db.add(m)
    db.commit()
    db.close()


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_get_app_metrics_empty():
    """App sans métriques → liste vide."""
    response = client.get("/metrics/nonexistent_app")
    assert response.status_code == 200
    assert response.json() == []


def test_get_app_metrics_with_data():
    """Après insertion, les métriques apparaissent."""
    _insert_metric(app_id="testapp1", user_id=10, cpu=55.0)
    response = client.get("/metrics/testapp1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["app_id"] == "testapp1"
    assert data[0]["cpu_percent"] == 55.0


def test_get_user_metrics():
    """Les métriques d'un utilisateur incluent toutes ses apps."""
    _insert_metric(app_id="app_a", user_id=99)
    _insert_metric(app_id="app_b", user_id=99)
    response = client.get("/metrics/user/99")
    assert response.status_code == 200
    data = response.json()
    app_ids = [m["app_id"] for m in data]
    assert "app_a" in app_ids
    assert "app_b" in app_ids


def test_prometheus_format():
    """Le endpoint /metrics retourne du texte Prometheus valide."""
    _insert_metric(app_id="promapp", user_id=77, cpu=12.5)
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    # Vérifier les marqueurs Prometheus
    assert "# HELP" in content
    assert "# TYPE" in content
    assert "minipaas_container_cpu_percent" in content


def test_metrics_summary():
    """Le résumé retourne des données agrégées."""
    _insert_metric(app_id="summaryapp", user_id=55)
    response = client.get("/metrics/summary")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_metrics_response_has_all_fields():
    """Chaque métrique contient tous les champs attendus."""
    _insert_metric(app_id="fieldapp", user_id=33)
    response = client.get("/metrics/fieldapp")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    m = data[0]
    required_fields = [
        "id", "app_id", "user_id", "container_name", "container_id",
        "cpu_percent", "memory_usage_bytes", "memory_percent",
        "network_rx_bytes", "network_tx_bytes", "status", "collected_at"
    ]
    for field in required_fields:
        assert field in m, f"Champ manquant : {field}"
