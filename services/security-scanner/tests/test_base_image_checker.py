import pytest
from unittest.mock import patch, MagicMock
from src.scanners.base_image_checker import (
    check_base_image,
    APPROVED_BASE_IMAGES,
    get_suggestion,
)


class TestBaseImageChecker:
    def test_approved_python_slim(self):
        result = check_base_image("python:3.12-slim")
        assert result.approved is True
        assert result.image == "python:3.12-slim"

    def test_approved_alpine(self):
        result = check_base_image("alpine:3.20")
        assert result.approved is True

    def test_approved_distroless(self):
        result = check_base_image("gcr.io/distroless/static-debian12")
        assert result.approved is True

    def test_approved_nginx_alpine(self):
        result = check_base_image("nginx:alpine")
        assert result.approved is True

    def test_blocked_ubuntu_latest(self):
        result = check_base_image("ubuntu:latest")
        assert result.approved is False
        assert result.suggestion is not None

    def test_blocked_scratch(self):
        result = check_base_image("scratch")
        assert result.approved is False
        assert "scanned" in result.suggestion.lower()

    def test_blocked_debian_full(self):
        result = check_base_image("debian:latest")
        assert result.approved is False

    def test_blocked_centos(self):
        result = check_base_image("centos:7")
        assert result.approved is False

    def test_blocked_python_no_suffix(self):
        result = check_base_image("python:3.12")
        assert result.approved is False

    def test_blocked_amazoncorretto(self):
        result = check_base_image("amazoncorretto:17")
        assert result.approved is False

    def test_suggestion_for_python(self):
        result = check_base_image("python:3.12")
        assert result.suggestion == "Use python:3.12-slim instead"

    def test_suggestion_for_ubuntu_latest_tag(self):
        result = check_base_image("ubuntu:latest")
        assert "latest" in result.suggestion.lower()

    def test_suggestion_for_scratch(self):
        result = check_base_image("scratch")
        assert result.suggestion is not None

    def test_approved_ubuntu_versioned(self):
        result = check_base_image("ubuntu:24.04")
        assert result.approved is True

    def test_approved_java_temurin(self):
        result = check_base_image("eclipse-temurin:17-jre-alpine")
        assert result.approved is True

    def test_approved_maven_temurin(self):
        result = check_base_image("maven:3.9-eclipse-temurin-17")
        assert result.approved is True

    def test_approved_postgres_alpine(self):
        result = check_base_image("postgres:16-alpine")
        assert result.approved is True

    def test_approved_redis(self):
        result = check_base_image("redis:7-alpine")
        assert result.approved is True

    def test_normalizes_whitespace(self):
        result = check_base_image("  python:3.12-slim  ")
        assert result.approved is True

    def test_approved_base_images_count(self):
        assert len(APPROVED_BASE_IMAGES) > 20
