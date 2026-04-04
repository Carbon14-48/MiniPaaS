#!/usr/bin/env bash
set -e

echo "🚀 Starting Cloudoku services..."
docker compose up -d

echo ""
echo "✅ Services started!"
echo ""
echo "Service URLs:"
echo "  API Gateway:        http://localhost:8000"
echo "  Auth Service:       http://localhost:8001"
echo "  App Management:     http://localhost:8002"
echo "  Build Service:      http://localhost:8003"
echo "  Deployment Service: http://localhost:8004"
echo "  Monitoring Service: http://localhost:8005"
echo "  Security Scanner:   http://localhost:8006"
echo ""
echo "API Docs: http://localhost:8000/docs"
