#!/bin/bash#!/bin/bash\n\n# TV Show Intervals Demo Setup Script - pgTAP Version\n# This script sets up the environment and runs the pgTAP tests\n\nset -e  # Exit on any error\n\necho \"🚀 TV Show Intervals Demo Setup (pgTAP)\"\necho \"=======================================\"\n\n# Check if Docker is running\nif ! docker info > /dev/null 2>&1; then\n    echo \"❌ Docker is not running. Please start Docker and try again.\"\n    exit 1\nfi\n\n# Check if Docker Compose is available\nif ! command -v docker-compose > /dev/null 2>&1; then\n    echo \"❌ docker-compose is not installed. Please install it and try again.\"\n    exit 1\nfi\n\necho \"📦 Starting PostgreSQL database with pgTAP...\"\ndocker-compose up -d\n\necho \"⏳ Waiting for database to be ready...\"\n# Wait for database to be healthy\ntimeout=60\ncounter=0\nwhile ! docker-compose exec -T postgres pg_isready -U demo -d demo > /dev/null 2>&1; do\n    if [ $counter -ge $timeout ]; then\n        echo \"❌ Database failed to start within $timeout seconds\"\n        docker-compose logs postgres\n        exit 1\n    fi\n    sleep 2\n    counter=$((counter + 2))\n    echo -n \".\"\ndone\necho \"\"\n\necho \"✅ Database is ready!\"\n\n# Verify pgTAP installation\necho \"🔍 Verifying pgTAP installation...\"\nif docker-compose exec -T postgres psql -U demo -d demo -c \"SELECT extversion FROM pg_extension WHERE extname = 'pgtap';\" > /dev/null 2>&1; then\n    echo \"✅ pgTAP extension is installed and ready\"\nelse\n    echo \"❌ pgTAP extension not found. Check Docker logs for installation issues.\"\n    docker-compose logs postgres\n    exit 1\nfi\n\n# Load test data\necho \"📊 Loading test data...\"\nif [ -f \"load_data.sh\" ]; then\n    ./load_data.sh\nelse\n    echo \"ℹ️ No load_data.sh script found, skipping test data loading\"\nfi\n\necho \"🧪 Running pgTAP data integrity tests...\"\n\n# Run pgTAP tests directly in the database\necho \"📋 Executing pgTAP test suite...\"\ndocker-compose exec -T postgres psql -U demo -d demo -f /app/tests/test_runner.sql > tap_output.txt 2>&1\n\necho \"📊 Test Results:\"\necho \"===============\"\ncat tap_output.txt\necho \"===============\"\n\n# Check if we have Python available for Allure conversion\nif command -v python3 > /dev/null 2>&1; then\n    # Check if Python virtual environment exists\n    if [ ! -d \"venv\" ]; then\n        echo \"🐍 Creating Python virtual environment for Allure reporting...\"\n        python3 -m venv venv\n    fi\n\n    echo \"📚 Installing minimal Python dependencies for Allure...\"\n    source venv/bin/activate\n    pip install -r requirements.txt > /dev/null 2>&1\n\n    # Convert TAP output to Allure format\n    echo \"📊 Converting test results to Allure format...\"\n    python tests/tap_to_allure.py tap_output.txt --output-dir allure-results\n    \n    echo \"📋 Allure results generated in allure-results/ directory\"\nelse\n    echo \"ℹ️ Python not available - skipping Allure report generation\"\nfi\n\necho \"\"\necho \"✅ Setup complete! pgTAP tests executed.\"\necho \"\"\necho \"📋 Available commands:\"\necho \"  - Run pgTAP tests: docker-compose exec postgres psql -U demo -d demo -f /app/tests/test_runner.sql\"\necho \"  - Connect to database: psql -h localhost -U demo -d demo\"\necho \"  - Stop database: docker-compose down\"\necho \"  - View database logs: docker-compose logs postgres\"\necho \"  - Generate Allure report: allure serve allure-results (requires Allure CLI)\"

# TV Show Intervals Demo Setup Script - pgTAP Version
# This script sets up the environment and runs the pgTAP tests

set -e  # Exit on any error

echo "🚀 TV Show Intervals Demo Setup (pgTAP)"
echo "======================================="

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

echo "📦 Starting PostgreSQL database with pgTAP..."
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

# Verify pgTAP installation
echo "🔍 Verifying pgTAP installation..."
if docker-compose exec -T postgres psql -U demo -d demo -c "SELECT extversion FROM pg_extension WHERE extname = 'pgtap';" > /dev/null 2>&1; then
    echo "✅ pgTAP extension is installed and ready"
else
    echo "❌ pgTAP extension not found. Check Docker logs for installation issues."
    docker-compose logs postgres
    exit 1
fi

# Load test data
echo "📊 Loading test data..."
if [ -f "load_data.sh" ]; then
    ./load_data.sh
else
    echo "ℹ️ No load_data.sh script found, skipping test data loading"
fi

echo "🧪 Running pgTAP data integrity tests..."

# Run pgTAP tests directly in the database
echo "📋 Executing pgTAP test suite..."
docker-compose exec -T postgres psql -U demo -d demo -f /app/tests/test_runner.sql > tap_output.txt 2>&1

echo "📊 Test Results:"
echo "==============="
cat tap_output.txt
echo "==============="

# Check if we have Python available for Allure conversion
if command -v python3 > /dev/null 2>&1; then
    # Check if Python virtual environment exists
    if [ ! -d "venv" ]; then
        echo "🐍 Creating Python virtual environment for Allure reporting..."
        python3 -m venv venv
    fi

    echo "📚 Installing minimal Python dependencies for Allure..."
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1

    # Convert TAP output to Allure format
    echo "📊 Converting test results to Allure format..."
    python tests/tap_to_allure.py tap_output.txt --output-dir allure-results
    
    echo "📋 Allure results generated in allure-results/ directory"
else
    echo "ℹ️ Python not available - skipping Allure report generation"
fi

echo ""
echo "✅ Setup complete! pgTAP tests executed."
echo ""
echo "📋 Available commands:"
echo "  - Run pgTAP tests: docker-compose exec postgres psql -U demo -d demo -f /app/tests/test_runner.sql"
echo "  - Connect to database: psql -h localhost -U demo -d demo"
echo "  - Stop database: docker-compose down"
echo "  - View database logs: docker-compose logs postgres"
echo "  - Generate Allure report: allure serve allure-results (requires Allure CLI)"