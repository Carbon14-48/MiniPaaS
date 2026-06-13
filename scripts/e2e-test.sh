#!/usr/bin/env bash
set -e

echo "========================================="
echo "  MiniPaaS End-to-End Functional Test"
echo "========================================="
echo ""

# 1. Setup .env
if [ ! -f .env ]; then
    echo "[1/7] Creating .env from .env.example..."
    cp .env.example .env
else
    echo "[1/7] .env already exists"
fi

# 2. Start services
echo "[2/7] Building and starting all services..."
docker compose up -d --build

echo "Waiting for services to be ready..."
for i in $(seq 1 30); do
    if curl -sf localhost:8000/health >/dev/null 2>&1; then
        echo "  Gateway ready after ${i}s"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  ERROR: Gateway not ready after 30s"
        exit 1
    fi
    sleep 1
done

# 3. Register user
echo "[3/7] Registering test user..."
REG=$(curl -sf -X POST localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e@test.com","password":"TestPass123","name":"e2etester"}') || true

# 4. Login
echo "[4/7] Logging in..."
LOGIN=$(curl -sf -X POST localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e@test.com","password":"TestPass123"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])" 2>/dev/null) || {
    echo "ERROR: Login failed. Response: $LOGIN"
    exit 1
}
echo "  Token obtained: ${TOKEN:0:20}..."

# 5. Deploy BAD app
echo "[5/7] Deploying BAD app (expect BLOCKED)..."
BAD=$(curl -s -X POST localhost:8000/deployments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "repo_url": "https://github.com/Carbon14-48/bad-deployable-test",
    "branch": "main",
    "app_name": "bad-app"
  }')
BAD_STATUS=$(echo "$BAD" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "parse_error")
echo "  Bad app status: $BAD_STATUS"
echo "  Response: $BAD" | head -5

# 6. Deploy GOOD app
echo "[6/7] Deploying GOOD app (expect running)..."
GOOD=$(curl -s -X POST localhost:8000/deployments/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "repo_url": "https://github.com/Carbon14-48/good-deployable-test",
    "branch": "main",
    "app_name": "good-app"
  }')
GOOD_ID=$(echo "$GOOD" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id','unknown'))" 2>/dev/null || echo "unknown")
GOOD_STATUS=$(echo "$GOOD" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
GOOD_PORT=$(echo "$GOOD" | python3 -c "import sys,json;print(json.load(sys.stdin).get('host_port','unknown'))" 2>/dev/null || echo "unknown")
echo "  Good app id: $GOOD_ID"
echo "  Status: $GOOD_STATUS"
echo "  Host port: $GOOD_PORT"

# Check build progress for good app
if [ "$GOOD_STATUS" = "building" ]; then
    echo "  Waiting for build to complete..."
    sleep 30
    # Check deployment again
    GOOD2=$(curl -sf localhost:8000/deployments/$GOOD_ID \
      -H "Authorization: Bearer $TOKEN")
    GOOD_STATUS2=$(echo "$GOOD2" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','unknown'))")
    GOOD_PORT2=$(echo "$GOOD2" | python3 -c "import sys,json;print(json.load(sys.stdin).get('host_port','unknown'))")
    echo "  Updated status: $GOOD_STATUS2"
    echo "  URL: http://localhost:$GOOD_PORT2"
fi

# 7. Check monitoring
echo "[7/7] Checking monitoring..."
# Health
HEALTH=$(curl -sf localhost:8000/monitoring/health \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null || echo "unavailable")
echo "  Monitoring health: $HEALTH" | head -3

# Metrics summary
SUMMARY=$(curl -sf localhost:8000/monitoring/metrics/summary \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null || echo "unavailable")
echo "  Metrics summary: $SUMMARY" | head -3

echo ""
echo "========================================="
echo "  URLs to check:"
echo "  Frontend:  http://localhost:5173"
echo "  API Docs:  http://localhost:8000/docs"
echo "========================================="
echo ""
echo "Quick checks:"
echo "  curl localhost:8000/health"
echo "  curl localhost:8000/auth/me -H \"Authorization: Bearer \$TOKEN\""
echo "  curl localhost:8000/deployments/ -H \"Authorization: Bearer \$TOKEN\""
