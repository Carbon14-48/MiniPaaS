"""
tests/test_docker_collector.py
--------------------------------
Tests de la logique de collecte Docker (sans vrai daemon).
"""
import pytest
from unittest.mock import MagicMock, patch
from src.services.docker_collector import (
    _calculate_cpu_percent,
    _extract_network_stats,
    parse_container_identity,
)
from src.services.log_collector import detect_log_level


# ── CPU calculation ───────────────────────────────────────────────────────────

def test_calculate_cpu_percent_normal():
    stats = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 2000000},
            "system_cpu_usage": 10000000,
            "online_cpus": 2,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 1000000},
            "system_cpu_usage": 9000000,
        },
    }
    result = _calculate_cpu_percent(stats)
    assert result is not None
    assert 0.0 <= result <= 200.0  # 2 CPUs max 200%


def test_calculate_cpu_percent_zero_delta():
    """Pas de delta → 0% CPU."""
    stats = {
        "cpu_stats": {
            "cpu_usage": {"total_usage": 1000},
            "system_cpu_usage": 5000,
            "online_cpus": 1,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 1000},
            "system_cpu_usage": 4000,
        },
    }
    result = _calculate_cpu_percent(stats)
    assert result == 0.0


def test_calculate_cpu_percent_malformed():
    """Stats malformées → None sans crash."""
    result = _calculate_cpu_percent({})
    assert result is None


# ── Network extraction ────────────────────────────────────────────────────────

def test_extract_network_stats_normal():
    stats = {
        "networks": {
            "eth0": {"rx_bytes": 1024, "tx_bytes": 512},
            "eth1": {"rx_bytes": 2048, "tx_bytes": 1024},
        }
    }
    rx, tx = _extract_network_stats(stats)
    assert rx == 3072
    assert tx == 1536


def test_extract_network_stats_empty():
    rx, tx = _extract_network_stats({})
    assert rx is None
    assert tx is None


# ── Container identity parsing ────────────────────────────────────────────────

def test_parse_identity_from_labels():
    """Labels Docker ont priorité sur le nom."""
    container = MagicMock()
    container.labels = {
        "minipaas.app_id": "myapp",
        "minipaas.user_id": "42",
    }
    container.name = "some_random_container_name"
    result = parse_container_identity(container)
    assert result["app_id"] == "myapp"
    assert result["user_id"] == 42


def test_parse_identity_from_name():
    """Sans labels, parse depuis le nom minipaas_{user_id}_{app_name}."""
    container = MagicMock()
    container.labels = {}
    container.name = "minipaas_42_myapp"
    result = parse_container_identity(container)
    assert result["app_id"] == "myapp"
    assert result["user_id"] == 42


def test_parse_identity_fallback():
    """Nom non conforme → app_id = nom complet, user_id = 0."""
    container = MagicMock()
    container.labels = {}
    container.name = "random_container"
    result = parse_container_identity(container)
    assert result["app_id"] == "random_container"
    assert result["user_id"] == 0


# ── Log level detection ───────────────────────────────────────────────────────

def test_detect_error_level():
    assert detect_log_level("ERROR: connection refused") == "ERROR"
    assert detect_log_level("Fatal exception occurred") == "ERROR"
    assert detect_log_level("Traceback (most recent call last)") == "ERROR"


def test_detect_warn_level():
    assert detect_log_level("WARNING: deprecated function") == "WARN"
    assert detect_log_level("warn: disk space low") == "WARN"


def test_detect_debug_level():
    assert detect_log_level("debug mode enabled") == "DEBUG"


def test_detect_info_level():
    """Messages normaux → INFO par défaut."""
    assert detect_log_level("Server started on port 8000") == "INFO"
    assert detect_log_level("Request processed successfully") == "INFO"
