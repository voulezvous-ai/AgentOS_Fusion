#!/bin/bash

set -e

# Activate the virtual environment
source .venv/bin/activate

# Run migrations or setup tasks (if applicable)
# echo "Running database setup/migrations..."
# python -m app.db_setup

# Start Uvicorn server
echo "Starting Uvicorn server..."
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
LOG_LEVEL=${LOG_LEVEL:-info}
WORKERS_PER_CORE=${WORKERS_PER_CORE:-1}
CORES=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || echo 1)
DEFAULT_WORKERS=$((CORES * WORKERS_PER_CORE))
WORKERS=${WORKERS:-$DEFAULT_WORKERS}

exec uvicorn \
    app.main:app \
    --host ${HOST} \
    --port ${PORT} \
    --workers ${WORKERS} \
    --log-level ${LOG_LEVEL} \
    --forwarded-allow-ips='*' \
    --proxy-headers