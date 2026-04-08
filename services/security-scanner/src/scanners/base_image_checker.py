from src.models.findings import BaseImageCheck

APPROVED_BASE_IMAGES: set[str] = {
    # Python
    "python:3.11-slim",
    "python:3.12-slim",
    "python:3.11-alpine",
    "python:3.12-alpine",
    "python:3.11-bookworm-slim",
    "python:3.12-bookworm-slim",
    # Node.js
    "node:18-alpine",
    "node:20-alpine",
    "node:18-slim",
    "node:20-slim",
    "node:18-bookworm-slim",
    "node:20-bookworm-slim",
    # Go
    "golang:1.21-alpine",
    "golang:1.22-alpine",
    "golang:1.21-slim",
    "golang:1.22-slim",
    # Java / JVM — eclipse-temurin
    "eclipse-temurin:8-jre-alpine",
    "eclipse-temurin:8-jre-fips",
    "eclipse-temurin:11-jre-alpine",
    "eclipse-temurin:11-jre-fips",
    "eclipse-temurin:17-jre-alpine",
    "eclipse-temurin:17-jre-fips",
    "eclipse-temurin:21-jre-alpine",
    "eclipse-temurin:21-jre-fips",
    "maven:3.9-eclipse-temurin-17",
    "maven:3.9-eclipse-temurin-21",
    "maven:3.11-eclipse-temurin-17",
    "maven:3.11-eclipse-temurin-21",
    # Distroless
    "gcr.io/distroless/python3-debian11",
    "gcr.io/distroless/nodejs18-debian11",
    "gcr.io/distroless/nodejs20-debian11",
    "gcr.io/distroless/static-debian11",
    "gcr.io/distroless/static-debian12",
    # Alpine
    "alpine:3.18",
    "alpine:3.19",
    "alpine:3.20",
    # Debian Slim
    "debian:bookworm-slim",
    "debian:bullseye-slim",
    "debian:trixie-slim",
    # Ubuntu
    "ubuntu:22.04",
    "ubuntu:24.04",
    "ubuntu:24.10",
    # Common services
    "nginx:alpine",
    "nginx:1.25-alpine",
    "redis:7-alpine",
    "redis:7-bookworm",
    "postgres:15-alpine",
    "postgres:16-alpine",
    "postgres:17-alpine",
    "rabbitmq:3-management-alpine",
}

APPROVED_FAMILIES_WITH_VARIANTS: dict[str, str] = {
    "python": "Use python:3.12-slim instead",
    "node": "Use node:20-alpine or node:20-slim instead",
    "golang": "Use golang:1.22-alpine instead",
    "debian": "Use debian:bookworm-slim instead",
    "ubuntu": "Use ubuntu:24.04 instead",
    "nginx": "Use nginx:alpine instead",
    "redis": "Use redis:7-alpine instead",
    "postgres": "Use postgres:16-alpine instead",
    "rabbitmq": "Use rabbitmq:3-management-alpine instead",
}


def _has_variant_suffix(tag: str) -> bool:
    """True if the tag has a variant suffix like -slim, -alpine, etc."""
    variants = {"-slim", "-alpine", "-bookworm", "-bullseye", "-fips",
               "-distroless", "-centos7", "-centos8"}
    return any(tag.endswith(v) for v in variants)


def get_suggestion(base_image: str) -> str:
    """Return a suggestion if the image is close to an approved one."""
    if base_image == "scratch":
        return "scratch images cannot be scanned. Use alpine:3.20 or distroless/static-debian12"
    if base_image.endswith(":latest"):
        return "Avoid ':latest' tag — use a specific version tag"
    if base_image.startswith("centos") or base_image.startswith("rockylinux"):
        return "Use debian:bookworm-slim or alpine:3.20 instead (EOL distributions)"
    if base_image.startswith("amazoncorretto") or base_image.startswith("openjdk"):
        return "Use eclipse-temurin:<version>-jre-alpine instead"
    if base_image.startswith("fedora"):
        return "Use alpine:3.20 or debian:bookworm-slim instead"
    if base_image.startswith("busybox"):
        return "Use alpine:3.20 instead (minimal, maintained alternative)"
    if base_image.startswith("amazonlinux"):
        return "Use debian:bookworm-slim or alpine:3.20 instead"
    for family, suggestion in APPROVED_FAMILIES_WITH_VARIANTS.items():
        if base_image.startswith(f"{family}:"):
            return suggestion
    return "Use an approved base image from the allowlist (see security-scanner README)"


def check_base_image(base_image: str) -> BaseImageCheck:
    """
    Check if a base image is in the approved allowlist.
    Only exact matches are approved. Images without variant suffixes
    (like 'python:3.12', 'ubuntu:latest', 'debian:latest') are blocked.
    """
    normalized = base_image.strip()

    # Exact match — always approved
    if normalized in APPROVED_BASE_IMAGES:
        return BaseImageCheck(image=normalized, approved=True)

    # Split into name:tag
    if ":" not in normalized:
        return BaseImageCheck(
            image=normalized,
            approved=False,
            suggestion=get_suggestion(normalized),
        )

    base_name = normalized.split(":")[0]
    tag = normalized[len(base_name) + 1:]

    # Images without variant suffix AND not in allowlist → blocked
    if not _has_variant_suffix(tag):
        return BaseImageCheck(
            image=normalized,
            approved=False,
            suggestion=get_suggestion(normalized),
        )

    # It has a suffix — check if any approved image matches this family+tag prefix
    for approved in APPROVED_BASE_IMAGES:
        if approved.startswith(base_name + ":"):
            # Match found (e.g. python:3.12-slim matches python:3.12-slim exactly or
            # python:3.12-bookworm-slim)
            return BaseImageCheck(image=normalized, approved=True)

    # Has suffix but not in allowlist
    return BaseImageCheck(
        image=normalized,
        approved=False,
        suggestion=get_suggestion(normalized),
    )
