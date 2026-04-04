.PHONY: help setup dev stop test lint build clean

help:
	@echo "Cloudoku - Available commands:"
	@echo ""
	@echo "  make setup    - Initial project setup"
	@echo "  make dev      - Start all services locally"
	@echo "  make stop     - Stop all services"
	@echo "  make test     - Run all tests"
	@echo "  make lint     - Lint all services"
	@echo "  make build    - Build all Docker images"
	@echo "  make clean    - Clean up build artifacts"

setup:
	@./scripts/setup.sh

dev:
	@./scripts/dev.sh

stop:
	docker compose down

test:
	@./scripts/test-all.sh

lint:
	@./scripts/lint-all.sh

build:
	docker compose build

clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
