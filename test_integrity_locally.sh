#!/bin/bash

# Test data integrity validation locally
# This script tests the new data integrity approach using local Docker database

set -e

echo "🧪 Testing Data Integrity Validation Locally"
echo "============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start the database
echo "🐳 Starting PostgreSQL database..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Check database readiness
for i in {1..30}; do
    if docker-compose exec postgres pg_isready -U demo -d demo > /dev/null 2>&1; then
        echo "✅ Database is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Database failed to start after 30 attempts"
        exit 1
    fi
    echo "⏳ Still waiting... (attempt $i/30)"
    sleep 2
done

# Apply schema
echo "📋 Applying database schema..."
docker-compose exec -T postgres psql -U demo -d demo < schema.sql

# Upload corrupted data
echo "💥 Uploading corrupted data..."
export DATABASE_URL="postgresql://demo:demo@localhost:5432/demo"
./upload_corrupted_data.sh

# Run a quick validation test
echo "🔍 Running quick validation test..."
python3 -c "
import sys
import os
sys.path.append('.')
from conftest import db_connection
from data_integrity import DataIntegrityValidator

# Create connection
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'demo'
os.environ['DB_USER'] = 'demo'
os.environ['DB_PASSWORD'] = 'demo'

print('🔗 Connecting to database...')

# Use the same connection setup as in conftest.py
import psycopg2
from psycopg2.extras import RealDictCursor

connection = psycopg2.connect(
    host='localhost',
    database='demo',
    user='demo',
    password='demo',
    port=5432,
    cursor_factory=RealDictCursor
)
connection.autocommit = True

with connection.cursor() as cursor:
    print('✅ Database connection established')
    
    # Quick data check
    cursor.execute('SELECT COUNT(*) FROM programs')
    program_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) FROM program_intervals')
    interval_count = cursor.fetchone()['count']
    
    print(f'📊 Database contains: {program_count} programs, {interval_count} intervals')
    
    # Run comprehensive validation
    print('🔍 Running comprehensive validation...')
    validator = DataIntegrityValidator(cursor)
    results = validator.run_comprehensive_validation()
    
    # Print summary
    summary = results.get('summary', {})
    overall_valid = results.get('overall_valid', True)
    
    print(f'📋 Validation Results:')
    print(f'   Overall Valid: {overall_valid}')
    print(f'   Checks Performed: {summary.get(\"checks_performed\", 0)}')
    print(f'   Total Errors: {summary.get(\"total_errors\", 0)}')
    print(f'   Total Warnings: {summary.get(\"total_warnings\", 0)}')
    
    if not overall_valid:
        print('✅ SUCCESS: Validation correctly detected data integrity issues!')
    else:
        print('❌ UNEXPECTED: Validation did not detect expected integrity issues')
        sys.exit(1)

connection.close()
print('✅ Local validation test completed successfully!')
"

# Clean up
echo "🧹 Cleaning up..."
docker-compose down

echo ""
echo "🎉 Local data integrity validation test completed successfully!"
echo "The corrupted data approach is working correctly."
echo ""
echo "Next steps:"
echo "1. Commit and push the changes"
echo "2. Create a PR to test with Neon database"
echo "3. The CI/CD will upload corrupted data and run validation tests"