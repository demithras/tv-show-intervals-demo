#!/bin/bash

# TV Show Intervals Demo - Data Loading Script
# This script cleans the database and loads test data from CSV file
# Supports both DATABASE_URL and individual DB environment variables

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if psql is available
if ! command_exists psql; then
    print_error "psql command not found. Please install PostgreSQL client tools."
    exit 1
fi

# Set default CSV file if not provided
CSV_FILE=${1:-"full_day_programs.csv"}

# Check if CSV file exists
if [ ! -f "$CSV_FILE" ]; then
    print_error "CSV file '$CSV_FILE' not found."
    print_info "Usage: $0 [csv_file]"
    print_info "Default CSV file: full_day_programs.csv"
    exit 1
fi

print_info "Loading data from CSV file: $CSV_FILE"

# Parse database connection parameters
if [ -n "$DATABASE_URL" ]; then
    print_info "Using DATABASE_URL for connection"
    PSQL_CMD="psql $DATABASE_URL"
else
    # Use individual environment variables or defaults
    DB_HOST=${DB_HOST:-"localhost"}
    DB_PORT=${DB_PORT:-"5432"}
    DB_NAME=${DB_NAME:-"demo"}
    DB_USER=${DB_USER:-"demo"}
    DB_PASSWORD=${DB_PASSWORD:-"demo"}
    
    print_info "Using individual DB environment variables"
    print_info "Connecting to: $DB_HOST:$DB_PORT/$DB_NAME as $DB_USER"
    
    # Set PGPASSWORD for psql
    export PGPASSWORD="$DB_PASSWORD"
    PSQL_CMD="psql -h $DB_HOST -p $DB_PORT -d $DB_NAME -U $DB_USER"
fi

# Test database connection
print_info "Testing database connection..."
if ! $PSQL_CMD -c "SELECT 1;" >/dev/null 2>&1; then
    print_error "Failed to connect to database. Please check your connection parameters."
    exit 1
fi
print_info "Database connection successful."

# Clean existing data
print_info "Cleaning existing data..."
$PSQL_CMD -c "
BEGIN;
DELETE FROM program_intervals;
DELETE FROM programs;
COMMIT;
" || {
    print_error "Failed to clean database"
    exit 1
}
print_info "Database cleaned successfully."

# Load data from CSV
print_info "Loading data from CSV..."
LOAD_RESULT=$($PSQL_CMD << EOF
BEGIN;
\copy programs (program_name, start_time, end_time) FROM '$CSV_FILE' WITH (FORMAT csv, DELIMITER ',', HEADER true);
SELECT COUNT(*) FROM programs;
COMMIT;
EOF
)

# Extract the count from the result
LOAD_COUNT=$(echo "$LOAD_RESULT" | grep -E '^[[:space:]]*[0-9]+[[:space:]]*$' | tr -d ' ')

if [ -z "$LOAD_COUNT" ]; then
    print_error "Failed to load data from CSV"
    print_error "Database output: $LOAD_RESULT"
    exit 1
fi

print_info "Successfully loaded $LOAD_COUNT programs from CSV."

# Verify program_intervals table was populated by triggers
INTERVAL_COUNT=$($PSQL_CMD -t -c "SELECT COUNT(*) FROM program_intervals;" | tr -d ' ')

print_info "Program intervals automatically calculated: $INTERVAL_COUNT entries."

# Display summary
print_info "Data loading completed successfully!"
print_info "Summary:"
print_info "  - Programs loaded: $LOAD_COUNT"
print_info "  - Program intervals calculated: $INTERVAL_COUNT"

# Optional: Display first few records for verification
if [ "${VERIFY_DATA:-false}" = "true" ]; then
    print_info "Sample data verification:"
    echo "Programs:"
    $PSQL_CMD -c "SELECT program_name, start_time, end_time FROM programs ORDER BY start_time LIMIT 5;"
    echo
    echo "Program intervals:"
    $PSQL_CMD -c "SELECT program_name, interval_count FROM program_intervals ORDER BY program_name LIMIT 5;"
fi