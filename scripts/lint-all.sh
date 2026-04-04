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

echo "✅ Linting complete!"
