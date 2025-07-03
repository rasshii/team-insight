#!/bin/bash
# Startup script for backend service

echo "🚀 Starting Team Insight Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "✅ Database is ready"

# Run migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

# Initialize admin users from environment variable
echo "👤 Initializing admin users..."
python scripts/init_admin.py

# Start the application
echo "🌟 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug