#!/bin/bash
set -e

# Activate virtual environment if it exists (for local testing), 
# otherwise assume environment is set up (Docker)
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Starting up..."

# Create migrations for 'db' app
# In production, we usually don't run makemigrations, but keeping it per existing workflow
echo "Running migrate (alembic upgrade head)..."
alembic -c pyproject.toml upgrade head

echo "Starting Bot..."
exec pyweastcoastbot
