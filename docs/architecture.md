# Architecture

## Overview

Cloudoku is a microservices-based PaaS platform with 7 backend services and a React frontend dashboard.

## Service Communication

- **Synchronous**: HTTP/REST between services via API Gateway
- **Asynchronous**: RabbitMQ for event-driven communication (build triggers, deployment events)

## Data Flow

1. User creates app via frontend → API Gateway → App Management Service
2. App Management triggers build → Build Service (via RabbitMQ)
3. Build Service clones repo, builds Docker image, pushes to registry
4. Security Scanner scans the image
5. Deployment Service deploys to Kubernetes
6. Monitoring Service collects logs and metrics

## Technology Decisions

- **FastAPI**: Modern async Python framework with auto-generated OpenAPI docs
- **PostgreSQL**: Relational database for structured data
- **RabbitMQ**: Message broker for async communication
- **Kubernetes**: Container orchestration for production deployments
- **Docker**: Containerization for all services
