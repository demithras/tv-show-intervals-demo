#!/bin/bash

# TV Show Intervals Demo Setup Script
# This script sets up the environment and runs the tests

set -e  # Exit on any error

echo "🚀 TV Show Intervals Demo Setup"
echo "================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

echo "📦 Starting PostgreSQL database..."
docker-compose up -d

echo "⏳ Waiting for database to be ready..."
# Wait for database to be healthy
timeout=60
counter=0
while ! docker-compose exec -T postgres pg_isready -U demo -d demo > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Database failed to start within $timeout seconds"
        docker-compose logs postgres
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done
echo ""

echo "✅ Database is ready!"

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "📚 Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "🧪 Running BDD tests..."
pytest -v --tb=short

echo ""
echo "✅ Setup complete! All tests passed."
echo ""
echo "📋 Available commands:"
echo "  - Run tests: pytest -v"
echo "  - Run tests quietly: pytest -q"
echo "  - Stop database: docker-compose down"
echo "  - View database logs: docker-compose logs postgres"
echo "  - Connect to database: psql -h localhost -U demo -d demo"