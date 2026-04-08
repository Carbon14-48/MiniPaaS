"""
tests/test_docker_registry.py
------------------------------
Tests de la logique Docker interne (docker_registry.py).
On mocke le client Docker — pas de vrai daemon pendant les tests.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.services.docker_registry import (
    image_exists_locally,
    push_to_registry,
)


# ─── Test 1 : image existe localement ────────────────────────────────────────

def test_image_exists_locally_true():
    with patch("src.services.docker_registry.docker") as mock_docker:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()

        result = image_exists_locally("user42/myapp:v1")
        assert result is True


# ─── Test 2 : image absente localement ───────────────────────────────────────

def test_image_exists_locally_false():
    from docker.errors import ImageNotFound

    with patch("src.services.docker_registry.docker") as mock_docker:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.images.get.side_effect = ImageNotFound("not found")

        result = image_exists_locally("user42/ghost:v1")
        assert result is False


# ─── Test 3 : push image absente → 404 ───────────────────────────────────────

def test_push_raises_404_when_image_missing():
    """push_to_registry doit lever 404 si l'image n'existe pas localement."""
    from docker.errors import ImageNotFound

    with patch("src.services.docker_registry.docker") as mock_docker:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.images.get.side_effect = ImageNotFound("not found")

        with pytest.raises(HTTPException) as exc:
            push_to_registry("user42/ghost:v1")

        assert exc.value.status_code == 404


# ─── Test 4 : push réussi — retourne registry_url + digest ──────────────────

def test_push_returns_registry_url_and_digest():
    """Push réussi → retourne dict avec registry_url, digest, size_bytes."""
    with patch("src.services.docker_registry.docker") as mock_docker:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.ping.return_value = True

        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image

        # Simule les logs de docker push avec digest
        mock_client.images.push.return_value = iter([
            {"status": "Pushing"},
            {"aux": {"Digest": "sha256:abc123", "Size": 45000000}},
            {"status": "Pushed"},
        ])

        result = push_to_registry("user42/myapp:v1")

        assert "registry_url" in result
        assert result["registry_url"] == "registry:5000/user42/myapp:v1"
        assert result["digest"] == "sha256:abc123"
        assert result["size_bytes"] == 45000000


# ─── Test 5 : erreur push → 503 si registry injoignable ─────────────────────

def test_push_raises_503_when_registry_unreachable():
    """Push vers registry injoignable → HTTPException 503."""
    with patch("src.services.docker_registry.docker") as mock_docker:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.ping.return_value = True

        mock_image = MagicMock()
        mock_client.images.get.return_value = mock_image

        # Simule une erreur "connection refused" dans les logs de push
        mock_client.images.push.return_value = iter([
            {"error": "connection refused to registry:5000"}
        ])

        with pytest.raises(HTTPException) as exc:
            push_to_registry("user42/myapp:v1")

        assert exc.value.status_code == 503


# ─── Test 6 : nettoyage toujours exécuté ─────────────────────────────────────

def test_cleanup_always_called_after_push():
    """Les images locales doivent être supprimées même après un push réussi."""
    with patch("src.services.docker_registry.docker") as mock_docker:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.images.get.return_value = MagicMock()
        mock_client.images.push.return_value = iter([
            {"aux": {"Digest": "sha256:clean", "Size": 1000}},
        ])

        push_to_registry("user42/myapp:v1")

        # docker rmi doit avoir été appelé (nettoyage)
        assert mock_client.images.remove.called
