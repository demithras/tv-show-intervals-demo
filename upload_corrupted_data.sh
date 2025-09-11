#!/bin/bash

# Upload corrupted data to Neon development branch
# This script uploads the corrupted CSV data to create a database with integrity issues

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Uploading corrupted data to Neon development branch...${NC}"

# Check if DATABASE_URL is provided
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ ERROR: DATABASE_URL environment variable is not set${NC}"
    echo "Please set DATABASE_URL to your Neon development branch connection string"
    exit 1
fi

# Check if required files exist
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORRUPTED_CSV="$SCRIPT_DIR/data/corrupted_programs.csv"
VALID_CSV="$SCRIPT_DIR/data/full_day_programs.csv"

if [ ! -f "$CORRUPTED_CSV" ]; then
    echo -e "${RED}❌ ERROR: Corrupted CSV file not found: $CORRUPTED_CSV${NC}"
    exit 1
fi

if [ ! -f "$VALID_CSV" ]; then
    echo -e "${RED}❌ ERROR: Valid CSV file not found: $VALID_CSV${NC}"
    exit 1
fi

# Install psql if not available (for GitHub Actions)
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  psql not found, attempting to install...${NC}"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y postgresql-client
    elif command -v brew &> /dev/null; then
        brew install postgresql
    else
        echo -e "${RED}❌ ERROR: Cannot install psql. Please install PostgreSQL client manually.${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}📊 Database connection: ${DATABASE_URL%%@*}@[REDACTED]${NC}"

# Function to execute SQL with error handling
execute_sql() {
    local sql="$1"
    local description="$2"
    
    echo -e "${YELLOW}🔄 $description...${NC}"
    
    if psql "$DATABASE_URL" -c "$sql"; then
        echo -e "${GREEN}✅ $description completed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ ERROR: $description failed${NC}"
        return 1
    fi
}

# Clear existing data
echo -e "${BLUE}🧹 Clearing existing data...${NC}"
execute_sql "DELETE FROM program_intervals; DELETE FROM programs;" "Clearing tables"

# Upload some valid data first (to create a mixed scenario)
echo -e "${BLUE}📥 Uploading valid data first...${NC}"

# Read and insert valid data (skipping header)
tail -n +2 "$VALID_CSV" | head -20 | while IFS=',' read -r program_name start_time end_time; do
    # Clean the data (remove quotes and trim whitespace)
    program_name=$(echo "$program_name" | sed 's/^"//;s/"$//' | xargs)
    start_time=$(echo "$start_time" | sed 's/^"//;s/"$//' | xargs)
    end_time=$(echo "$end_time" | sed 's/^"//;s/"$//' | xargs)
    
    if [ -n "$program_name" ] && [ -n "$start_time" ] && [ -n "$end_time" ]; then
        echo "Inserting valid program: $program_name ($start_time - $end_time)"
        psql "$DATABASE_URL" -c "INSERT INTO programs (program_name, start_time, end_time) VALUES ('$program_name', '$start_time', '$end_time');" || echo "Failed to insert: $program_name"
    fi
done

echo -e "${GREEN}✅ Valid data uploaded successfully${NC}"

# Now upload corrupted data (this will create integrity issues)
echo -e "${BLUE}💥 Uploading corrupted data to create integrity issues...${NC}"

# Manually insert problematic records that will create specific integrity issues
echo -e "${YELLOW}🔄 Creating referential integrity issues...${NC}"

# Insert orphaned interval record (interval without corresponding program)
execute_sql "INSERT INTO program_intervals (program_name, interval_count) VALUES ('Orphaned Show', 5);" "Creating orphaned interval record"

# Insert overlapping programs
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('Overlap Show 1', '09:00', '10:00');" "Inserting first overlapping program"
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('Overlap Show 2', '09:30', '10:30');" "Inserting second overlapping program"

# Insert duplicate program names
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('Duplicate News', '06:00', '07:00');" "Inserting first duplicate"
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('Duplicate News', '18:00', '19:00');" "Inserting second duplicate"

# Insert program with zero duration
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('Zero Duration Show', '15:00', '15:00');" "Inserting zero duration program"

# Insert program with suspicious name (simulating SQL injection attempt)
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('Suspicious''; DROP TABLE programs; --', '20:00', '21:00');" "Inserting program with suspicious name"

# Insert program with very long name
LONG_NAME="Very Long Program Name That Exceeds Normal Database Limits And Should Cause Issues With Storage And Display In Most User Interfaces And Reports Making It A Good Test Case For Data Validation"
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('$LONG_NAME', '21:00', '22:00');" "Inserting program with very long name"

# Create incorrect interval calculation by manually updating
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('Incorrect Calculation Show', '10:00', '11:00');" "Inserting program for incorrect calculation test"
execute_sql "UPDATE program_intervals SET interval_count = 10 WHERE program_name = 'Incorrect Calculation Show';" "Creating incorrect interval calculation"

# Insert program without intervals (by deleting the interval after insertion)
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('Missing Interval Show', '12:00', '13:00');" "Inserting program that will miss intervals"
execute_sql "DELETE FROM program_intervals WHERE program_name = 'Missing Interval Show';" "Creating missing interval issue"

# Insert programs with non-standard time slots
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('Non-Standard Time Show', '10:17', '10:42');" "Inserting non-standard time program"

# Create a program that appears longer than 24 hours (edge case)
execute_sql "INSERT INTO programs (program_name, start_time, end_time) VALUES ('Invalid Long Show', '23:00', '22:00');" "Inserting apparently long program"

echo -e "${GREEN}✅ Corrupted data uploaded successfully${NC}"

# Verify the corruption
echo -e "${BLUE}🔍 Verifying data corruption...${NC}"

# Count total programs and intervals
PROGRAM_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM programs;" | xargs)
INTERVAL_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM program_intervals;" | xargs)

echo -e "${BLUE}📊 Database state after corruption:${NC}"
echo -e "  Programs: $PROGRAM_COUNT"
echo -e "  Intervals: $INTERVAL_COUNT"

# Quick integrity check
ORPHANED_INTERVALS=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM program_intervals pi LEFT JOIN programs p ON pi.program_name = p.program_name WHERE p.program_name IS NULL;" | xargs)
MISSING_INTERVALS=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM programs p LEFT JOIN program_intervals pi ON p.program_name = pi.program_name WHERE pi.program_name IS NULL;" | xargs)
OVERLAPPING_PROGRAMS=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM programs p1 JOIN programs p2 ON p1.id < p2.id WHERE p1.start_time < p2.end_time AND p1.end_time > p2.start_time AND NOT (p1.start_time > p1.end_time OR p2.start_time > p2.end_time);" | xargs)
DUPLICATE_NAMES=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM (SELECT program_name FROM programs GROUP BY program_name HAVING COUNT(*) > 1) AS dups;" | xargs)

echo -e "${YELLOW}🚨 Integrity issues detected:${NC}"
echo -e "  Orphaned intervals: $ORPHANED_INTERVALS"
echo -e "  Missing intervals: $MISSING_INTERVALS"
echo -e "  Overlapping programs: $OVERLAPPING_PROGRAMS"
echo -e "  Duplicate names: $DUPLICATE_NAMES"

if [ "$ORPHANED_INTERVALS" -gt 0 ] || [ "$MISSING_INTERVALS" -gt 0 ] || [ "$OVERLAPPING_PROGRAMS" -gt 0 ] || [ "$DUPLICATE_NAMES" -gt 0 ]; then
    echo -e "${GREEN}✅ Data corruption successfully created! The database now contains integrity issues for testing.${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Some corruption may not have been created as expected.${NC}"
fi

echo -e "${BLUE}🎯 Database is ready for data integrity testing!${NC}"
echo -e "${GREEN}✅ Upload completed successfully${NC}"