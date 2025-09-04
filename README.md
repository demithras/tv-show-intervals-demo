# TV Show Intervals Demo

A PostgreSQL demonstration project showing automatic interval calculation for TV programs using database triggers and BDD testing with pytest-bdd.

## Overview

This project demonstrates how to:
- Create database triggers that automatically calculate 15-minute intervals for TV programs
- Handle edge cases like overnight programs and zero-duration shows
- Write comprehensive BDD tests using pytest-bdd with proper test isolation
- Use Docker for consistent database environments

## Problem Statement

Given a table of TV programs with start/end times, automatically maintain a second table with the number of 15-minute intervals each program spans. The calculation must handle:

- **Zero intervals**: Programs with same start/end time or duration < 15 minutes
- **Multiple intervals**: Programs spanning multiple 15-minute blocks  
- **Overnight programs**: Shows crossing midnight (e.g., 23:30 → 00:15)
- **Automatic updates**: Triggers maintain consistency when programs change

## Database Schema

### Tables

- **`programs`**: Stores program name, start_time, end_time
- **`program_intervals`**: Auto-populated with program name and interval count

### Key Components

- **`count_15min_intervals(start, end)`**: SQL function handling overnight logic
- **Trigger system**: Automatically updates intervals on INSERT/UPDATE/DELETE
- **Proper indexing**: For performance on program lookups

## Project Structure

```
tv-show-intervals-demo/
├── README.md                   # This file
├── docker-compose.yml          # PostgreSQL container setup
├── schema.sql                  # Database schema with triggers
├── requirements.txt            # Python dependencies
├── conftest.py                 # Pytest fixtures and helpers
├── setup.sh                    # Automated setup script
├── features/
│   └── tv_intervals.feature    # BDD scenarios in Gherkin
└── test_tv_intervals.py        # Step definitions for BDD tests
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Git

### Automated Setup

Run the setup script to start everything:

```bash
./setup.sh
```

This will:
1. Start PostgreSQL in Docker
2. Create Python virtual environment
3. Install dependencies
4. Run all BDD tests

### Manual Setup

If you prefer manual setup:

1. **Start the database:**
   ```bash
   docker-compose up -d
   ```

2. **Wait for database to be ready:**
   ```bash
   # Check if database is ready
   docker-compose exec postgres pg_isready -U demo -d demo
   ```

3. **Set up Python environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run the tests:**
   ```bash
   pytest -v
   ```

## Test Scenarios

The BDD tests cover all edge cases:

### Basic Cases
- ✅ Same start/end time → 0 intervals
- ✅ Duration < 15 minutes → 0 intervals  
- ✅ Exactly 15 minutes → 1 interval
- ✅ Exactly 30 minutes → 2 intervals

### Complex Cases
- ✅ Partial intervals (40 minutes → 2 intervals)
- ✅ Overnight programs (23:30→00:15 → 3 intervals)
- ✅ Long overnight programs (23:00→01:30 → 10 intervals)

### Boundary Value Tests
- ✅ 14 minutes → 0 intervals (just under threshold)
- ✅ 16 minutes → 1 interval (just over threshold)
- ✅ 29 minutes → 1 interval (just under 2 intervals)
- ✅ 31 minutes → 2 intervals (just over 2 intervals)
- ✅ Midnight crossing edge cases (23:59→00:01)
- ✅ Very long programs (almost 24 hours)
- ✅ Full day programs (00:00→00:00)
- ✅ Multiple boundary scenarios in one test

### Database Operations
- ✅ Multiple programs with different intervals
- ✅ Empty database state
- ✅ Program updates recalculate intervals
- ✅ Program deletion removes intervals
- ✅ Program renaming updates intervals table

### Test Isolation

Each test scenario runs with a clean database state using:
- PostgreSQL transaction rollback
- Explicit cleanup fixtures
- Isolated test data

## Running Tests

### All tests with verbose output:
```bash
pytest -v
```

### Quiet mode:
```bash
pytest -q
```

### Specific scenario:
```bash
pytest -k "overnight"
```

### With coverage:
```bash
pytest --cov=. --cov-report=html
```

## Database Access

Connect to the database for manual inspection:

```bash
# Using psql
psql -h localhost -U demo -d demo

# Using Docker
docker-compose exec postgres psql -U demo -d demo
```

### Useful queries:
```sql
-- View all programs
SELECT * FROM programs;

-- View calculated intervals
SELECT * FROM program_intervals;

-- Test the interval function directly
SELECT count_15min_intervals('23:30'::time, '00:15'::time);

-- View trigger information
\d+ programs
```

## Example Usage

Insert a program and see automatic interval calculation:

```sql
-- Insert a program
INSERT INTO programs (program_name, start_time, end_time) 
VALUES ('Morning Show', '09:00', '10:30');

-- Check the automatically calculated intervals
SELECT * FROM program_intervals WHERE program_name = 'Morning Show';
-- Result: interval_count = 6 (90 minutes / 15 = 6)
```

## Edge Case Examples

### Overnight Program
```sql
INSERT INTO programs (program_name, start_time, end_time) 
VALUES ('Late Night Talk', '23:30', '00:15');
-- Result: 45 minutes (30 min + 15 min) = 3 intervals
```

### Short Program
```sql
INSERT INTO programs (program_name, start_time, end_time) 
VALUES ('News Brief', '12:00', '12:10');
-- Result: 10 minutes < 15 minutes = 0 intervals
```

## Cleanup

Stop and remove the database:

```bash
docker-compose down -v
```

Remove Python virtual environment:

```bash
deactivate  # If virtual environment is active
rm -rf venv
```

## Technical Details

### Interval Calculation Logic

The `count_15min_intervals()` function implements these rules:

1. **Same time**: `start == end` → 0 intervals
2. **Short duration**: `< 15 minutes` → 0 intervals
3. **Normal case**: `duration / 15` (integer division)
4. **Overnight**: Calculate as `(24:00 - start) + (end - 00:00)`

### Trigger Behavior

The trigger fires on:
- **INSERT**: Creates new interval record
- **UPDATE**: Updates existing interval record
- **DELETE**: Removes interval record
- **Name change**: Handles program renaming correctly

### Test Architecture

- **pytest-bdd**: Enables behavior-driven development
- **Database fixtures**: Ensure test isolation
- **Helper functions**: Simplify database operations
- **Error handling**: Robust connection management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is for demonstration purposes.