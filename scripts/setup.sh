#!/usr/bin/env bash
set -e

echo "🚀 Setting up Cloudoku..."

# Copy env example if .env doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file"
fi

# Create Python virtual environments for each service
for service in services/*/; do
    if [ -f "${service}requirements.txt" ]; then
        echo "📦 Installing dependencies for $(basename $service)..."
        cd "$service"
        pip install -r requirements.txt --quiet
        cd ../..
    fi
done

echo "✅ Setup complete!"
echo "Run './scripts/dev.sh' to start all services."
