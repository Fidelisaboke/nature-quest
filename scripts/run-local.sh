#!/bin/bash
set -e

echo "🚀 Starting Nature Quest Development Server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup first..."
    ./scripts/setup-db.sh
    exit 0
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Check if database is accessible
if ! python -c "import psycopg2; psycopg2.connect(host='${POSTGRES_HOST:-localhost}', port='${POSTGRES_PORT:-5432}', dbname='${POSTGRES_DB:-nature_quest}', user='${POSTGRES_USER:-nature_quest_user}', password='${POSTGRES_PASSWORD}')" 2>/dev/null; then
    echo "Database not accessible. Running database setup..."
    ./scripts/setup-db.sh
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Start development server
echo "Starting Django development server..."
echo "Health endpoint: http://localhost:8000/api/v1/health/"
echo "Admin panel: http://localhost:8000/admin/"
echo ""
python manage.py runserver 0.0.0.0:8000
