#!/bin/sh
set -e
echo "running database migrations..."
python scripts/migrate.py
echo "starting api server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${API_PORT:-8000}"
