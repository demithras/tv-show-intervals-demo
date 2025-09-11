# TV Show Intervals Demo - AI Coding Assistant Instructions

## Project Overview
This is a PostgreSQL demonstration project that automatically calculates 15-minute intervals for TV programs using database triggers and comprehensive BDD testing. The system handles complex edge cases like overnight programs and zero-duration shows.

## Architecture & Core Components

### Database Layer (`schema.sql`)
- **Main Tables**: `programs` (source data) and `program_intervals` (auto-calculated results)
- **Core Function**: `count_15min_intervals(start_time, end_time)` handles midnight-crossing logic
- **Trigger System**: Automatically maintains data consistency on INSERT/UPDATE/DELETE operations
- **Key Pattern**: Duration calculation logic handles overnight programs by splitting into pre/post-midnight segments

### Testing Framework (BDD with pytest-bdd)
- **Feature Files**: `features/tv_intervals.feature` contains Gherkin scenarios
- **Step Definitions**: `test_tv_intervals.py` implements the step functions
- **Test Fixtures**: `conftest.py` provides database connection management with proper isolation
- **Pattern**: Each test scenario runs with a clean database state using PostgreSQL transaction rollback

## Essential Development Workflows

### Local Development Setup
```bash
./setup.sh  # Automated: starts Docker, creates venv, installs deps, runs tests
```

### Manual Testing Commands
```bash
pytest -v                    # Verbose test output
pytest -k "overnight"        # Run specific scenarios
pytest --alluredir=results   # Generate Allure reports
```

### Database Access
```bash
docker-compose exec postgres psql -U demo -d demo
```

## Project-Specific Conventions

### Test Data Patterns
- Time formats use `"HH:MM"` strings (e.g., `"23:30"`, `"00:15"`)
- Program names are descriptive and test-case specific
- Overnight programs are tested extensively due to complex duration logic

### Database Helper Functions (`conftest.py`)
- `insert_program(cursor, name, start, end)` - Standard insertion pattern
- `get_program_intervals(cursor, program_name=None)` - Query intervals with optional filtering
- Always use parameterized queries to prevent SQL injection

### BDD Step Implementation
- Use `@given/@when/@then` decorators with `parsers.parse()` for dynamic values
- Store test context in `test_context` fixture between steps
- Attach verification data to Allure reports for debugging

## Integration Points

### CI/CD with Neon Database Branches
- **GitHub Action**: `.github/workflows/pr-tests.yml` creates isolated database branches per PR
- **Environment Variables**: Uses `DATABASE_URL` for Neon, falls back to individual DB vars for local Docker
- **Cleanup**: Automatically deletes database branches when PRs close

### Docker Environment
- **Local Testing**: `docker-compose.yml` provides PostgreSQL 15 with auto-schema initialization
- **Health Checks**: Database readiness is verified before test execution
- **Volume Persistence**: `postgres_data` volume maintains data between container restarts

## Critical Edge Cases & Business Rules

### Interval Calculation Logic
- Programs with `start_time == end_time` → 0 intervals
- Duration < 15 minutes → 0 intervals  
- Overnight programs: Calculate as `(24:00 - start) + (end - 00:00)`
- Integer division: `duration_minutes / 15` determines interval count

### Trigger Behavior Patterns
- **INSERT**: Creates new interval record automatically
- **UPDATE**: Recalculates intervals for modified programs
- **DELETE**: Removes corresponding interval records
- **Name Changes**: Properly handles program renaming by deleting old and inserting new records

## Development Guidelines

### When Adding New Test Scenarios
1. Add Gherkin scenario to `features/tv_intervals.feature`
2. Implement step definitions in `test_tv_intervals.py` if new steps needed
3. Use existing helper functions from `conftest.py` for database operations
4. Include edge cases in data tables for comprehensive boundary testing

### When Modifying Database Schema
1. Update `schema.sql` with proper DROP IF EXISTS statements for clean setup
2. Test both local Docker and Neon environments
3. Verify trigger behavior with manual database operations
4. Add corresponding test scenarios for new functionality

### Debugging Database Issues
- Check trigger execution: `\d+ programs` in psql
- Test interval function directly: `SELECT count_15min_intervals('23:30'::time, '00:15'::time);`
- Examine auto-generated data: `SELECT * FROM program_intervals;`

## Key Files for AI Context
- `schema.sql` - Complete database structure and business logic
- `conftest.py` - Database connection patterns and helper functions  
- `features/tv_intervals.feature` - Comprehensive business requirements and edge cases
- `test_tv_intervals.py` - BDD implementation patterns and Allure integration