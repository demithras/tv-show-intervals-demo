# TV Show Intervals Demo

This repoository showcase several approaches to test a PostgreSQL Data base.

It contains 5 PRs that each implement a different way to test database changes using GitHub Actions.

## Testing Options

### 1. Functional tests with pytest-bdd using Neon Database
PR: https://github.com/demithras/tv-show-intervals-demo/pull/2

The tests are written in BDD style using pytest-bdd and run against a Neon database branch created for each PR.
The tests are using clean database state for each scenario using transactions and rollbacks.
The tests are run automatically on each PR and the results are posted as a comment and an Allure report is generated and published to GitHub Pages.

Example of allure report with history: https://demithras.github.io/tv-show-intervals-demo/pr-2

### 2. Functional tests with pytest-bdd using ephemeral PostgreSQL
PR: https://github.com/demithras/tv-show-intervals-demo/pull/3

The same approach but the tests are run against a PostgreSQL database running in an ephemeral database created for each test run in GitHub Actions.
The database is created using the official PostgreSQL Docker image and is destroyed after the tests are run. The tests are running much faster than with Neon as there is no network latency.

Report: https://demithras.github.io/tv-show-intervals-demo/pr-3

### 3. Data integrity tests with python-bdd
PR: https://github.com/demithras/tv-show-intervals-demo/pull/6

The tests are running agains a Neon database populated with data. The goal is to test that data in all tables is consistent and valid.

Report: https://demithras.github.io/tv-show-intervals-demo/pr-6

### 4. Data integrity tests with pgTAP
PR: https://github.com/demithras/tv-show-intervals-demo/pull/7

The tests are written in SQL using the pgTAP extension and run against a Neon database prepopulated with data. The goal is to test that data in all tables is consistent and valid. Reports are converted to JUnit XML format so that they can be displayed in Allure format.

Report: https://demithras.github.io/tv-show-intervals-demo/pr-7

### 6. Performance tests with python-bdd
PR: https://github.com/demithras/tv-show-intervals-demo/pull/8

The tests are designed to measure the performance of the database prepopulated with big amounts of synthetic data. The goal is to ensure that the database can handle large amounts of data and that the performance is acceptable. The tests are run against a Neon database branch created for each PR.

Report: https://demithras.github.io/tv-show-intervals-demo/performance/run-6/

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

## Data Loading

### Loading Test Data

Before running tests, load the test data using the provided script:

```bash
./load_data.sh
```

This script will:
1. Clean the database (remove existing data)
2. Load programs from `full_day_programs.csv`
3. Automatically calculate intervals via database triggers
4. Verify the data was loaded correctly

### Custom CSV File

You can load a different CSV file:

```bash
./load_data.sh my_custom_programs.csv
```

### Data Verification

To see the loaded data during the loading process:

```bash
VERIFY_DATA=true ./load_data.sh
```

### Environment Variables

The script supports the same database connection options as the tests:

- **DATABASE_URL**: Full connection string (for Neon, Docker, etc.)
- **DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD**: Individual parameters

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

## GitHub Actions CI/CD

This project includes a GitHub Action that automatically tests database changes on pull requests using Neon database branches.

### Setup with Neon GitHub App (Recommended)

Since you have the Neon GitHub App installed, setup is simplified:

1. **Configure the GitHub App**:
   - Click "Configure" on your Neon GitHub App
   - Select your repository and grant necessary permissions
   - The app will automatically provide the required credentials

2. **Add Repository Variables**:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add these **Repository Variables**:
     - `NEON_PROJECT_ID`: Your Neon project ID
   - Add this **Repository Secret**:
     - `NEON_API_KEY`: Your Neon API key (if not auto-configured by the app)

### Alternative Manual Setup

If you prefer manual setup or don't use the GitHub App:

1. **Neon Account**: Create a Neon account and project at [neon.tech](https://neon.tech)
2. **GitHub Repository Variables**: Add `NEON_PROJECT_ID`
3. **GitHub Repository Secrets**: Add `NEON_API_KEY`

Run `./github-setup.sh` for detailed manual setup instructions.

### How It Works

The GitHub Action (`.github/workflows/pr-tests.yml`) automatically:

1. **On PR Open/Update**:
   - Creates a new Neon database branch for the PR
   - Applies the schema to the new branch
   - Runs all BDD tests against the isolated database
   - Posts test results as PR comments

2. **On PR Close**:
   - Automatically deletes the Neon database branch

### Benefits

- ✅ **Isolated Testing**: Each PR gets its own database branch
- ✅ **Automatic Setup**: GitHub App handles most configuration
- ✅ **Rich Test Reports**: Beautiful Allure reports with detailed analytics
- ✅ **Interactive Reports**: Published to GitHub Pages for easy access
- ✅ **Test History**: Track test trends over time
- ✅ **Cost Effective**: Branches are automatically cleaned up
- ✅ **No Local DB Required**: Tests run entirely in the cloud

### Allure Reports with History

The workflow generates comprehensive Allure reports that include:

- 📊 **Test Overview**: Pass/fail rates, execution times, test trends
- 🎯 **BDD Scenarios**: Gherkin steps with detailed execution logs
- 📋 **Test Steps**: Granular step-by-step execution details
- 📎 **Attachments**: Database queries, program data, and debug info
- 🏷️ **Categories**: Organized by features, stories, and test types
- 📈 **History & Trends**: Cross-run analysis and performance tracking

#### 🔄 **History Management:**

**Per-PR History:**
- Each PR maintains its own test execution history
- Multiple runs on the same PR show trends over time
- History preserved between synchronize events (new commits)

**Global History:**
- Browse reports from all PRs at the main GitHub Pages URL
- Compare test performance across different branches
- Track overall project test health

**Trend Analytics:**
- ⏱️ **Duration Trends**: Test execution time changes
- 🔄 **Retry Trends**: Flaky test detection over time  
- 📊 **History Trends**: Pass/fail rates across runs
- 📈 **Categories Trends**: Failure pattern analysis

**Accessing Reports:**
- **Latest PR Report**: `https://your-username.github.io/repo-name/pr-{number}`
- **Global History Index**: `https://your-username.github.io/repo-name/` - Shows all PR reports with proper timestamps
- **Artifacts**: Available in GitHub Actions run page for 30 days

**Recent Improvements:**
- ✅ Fixed global index to show all PR reports (not just the latest one)
- ✅ Fixed timestamp display issues (was showing raw shell commands)
- ✅ Enhanced styling and metadata display for better navigation
- ✅ Automatic discovery of existing PR reports with proper branch/run information

### Manual Testing

You can still run tests locally using Docker:

```bash
./setup.sh
```

This uses the local PostgreSQL container defined in `docker-compose.yml`.

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