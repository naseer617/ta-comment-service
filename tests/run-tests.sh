#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_ROOT="$(dirname "$SCRIPT_DIR")"
WORKSPACE_ROOT="$(dirname "$SERVICE_ROOT")"

# Activate virtual environment
if [ -d "$SERVICE_ROOT/.venv" ]; then
    echo "🐍 Activating virtual environment..."
    source "$SERVICE_ROOT/.venv/bin/activate"
fi

echo "🔄 Starting test DB..."
docker-compose -f "$SCRIPT_DIR/test-config/docker-compose.test.yml" up -d --wait

echo "⏳ Waiting for DB to be ready..."
sleep 3

# Change to service root first
cd "$SERVICE_ROOT"
echo "📁 Running from: $(pwd)"

echo "🚀 Running pytest..."
# Set PYTHONPATH to include both service root and workspace root
PYTHONPATH="$WORKSPACE_ROOT:$SERVICE_ROOT" pytest --rootdir=. --confcutdir=. -c "$SCRIPT_DIR/test-config/pytest.ini" -v

echo "🧹 Tearing down test DB..."
docker-compose -f "$SCRIPT_DIR/test-config/docker-compose.test.yml" down

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi
