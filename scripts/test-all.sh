#!/usr/bin/env bash
set -e

echo "🧪 Running tests for all services..."

failed=0

for service in services/*/; do
    if [ -d "${service}tests" ]; then
        echo ""
        echo "Testing $(basename $service)..."
        cd "$service"
        if pytest tests/ -v; then
            echo "✅ $(basename $service) passed"
        else
            echo "❌ $(basename $service) failed"
            failed=$((failed + 1))
        fi
        cd ../..
    fi
done

echo ""
if [ $failed -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ $failed service(s) failed"
    exit 1
fi
