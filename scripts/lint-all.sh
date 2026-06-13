#!/usr/bin/env bash
set -e

echo "🔍 Linting all services..."

for service in services/*/; do
    if [ -f "${service}requirements.txt" ]; then
        echo "Linting $(basename $service)..."
        cd "$service"
        ruff check src/ || true
        cd ../..
    fi
done

echo ""
echo "🔍 Linting frontend..."
if [ -f "frontend/node_modules/.package-lock.json" ]; then
    cd frontend
    echo "  ESLint..."
    npx eslint src/ || true
    echo "  TypeScript..."
    npx tsc --noEmit || true
    cd ..
else
    echo "  Skipping — run 'cd frontend && npm install' first"
fi

echo ""
echo "✅ Linting complete!"
