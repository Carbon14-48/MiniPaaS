import pytest
from src.scanners.base_image_checker import (
    check_base_image,
    APPROVED_BASE_IMAGES,
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

    def test_approved_ubuntu_latest(self):
        result = check_base_image("ubuntu:latest")
        assert result.approved is True

    def test_scratch(self):
        result = check_base_image("scratch")
        assert result.approved is True

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

    def test_unknown_image_still_approved(self):
        result = check_base_image("custom:latest")
        assert result.approved is True

    def test_no_tag_image_approved(self):
        result = check_base_image("myregistry.io/myimage")
        assert result.approved is True