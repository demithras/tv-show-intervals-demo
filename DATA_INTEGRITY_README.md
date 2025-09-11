# Data Integrity Testing

This directory contains comprehensive data integrity validation for the TV show intervals project. Unlike functional tests that load data during execution, these tests validate existing corrupted data in the database.

## Overview

The data integrity testing approach follows these principles:

1. **Pre-populate Database**: Upload corrupted data to create known integrity issues
2. **Static Validation**: Run validation tests against existing data state
3. **Comprehensive Reporting**: Generate detailed reports of all integrity issues found

## Files and Components

### Data Files
- `data/full_day_programs.csv` - Valid TV program data for a full day
- `data/corrupted_programs.csv` - CSV with various data issues (unused in current approach)

### Core Components
- `upload_corrupted_data.sh` - Script to upload corrupted data to Neon database
- `data_integrity.py` - Validation functions for checking data integrity
- `data_loader.py` - Utility for loading and validating CSV data (legacy)

### Test Files
- `features/data_integrity_validation.feature` - BDD scenarios for integrity validation
- `test_data_integrity_validation.py` - Step definitions for validation tests

### Utility Scripts
- `test_integrity_locally.sh` - Local testing script using Docker

## Data Corruption Types

The test data includes these integrity issues:

1. **Referential Integrity**:
   - Orphaned interval records (intervals without programs)
   - Missing interval records (programs without intervals)

2. **Time Constraints**:
   - Overlapping program schedules
   - Invalid time formats
   - Negative duration programs

3. **Data Quality**:
   - Duplicate program names
   - Empty/null program names
   - Excessively long program names
   - Zero duration programs

4. **Business Rules**:
   - Programs longer than 24 hours
   - Suspicious program names (SQL injection patterns)
   - Non-standard broadcast time slots

5. **Calculation Errors**:
   - Incorrect interval calculations
   - Manual data corruption

## Usage

### CI/CD Integration (Neon Database)

The GitHub Actions workflow automatically:

1. Creates a Neon database branch for the PR
2. Applies the schema
3. Uploads corrupted data using `upload_corrupted_data.sh`
4. Runs BDD validation tests
5. Generates Allure reports with detailed findings

### Local Testing

```bash
# Test the complete workflow locally
./test_integrity_locally.sh

# Manual upload to local database
export DATABASE_URL="postgresql://demo:demo@localhost:5432/demo"
./upload_corrupted_data.sh

# Run validation tests
pytest test_data_integrity_validation.py -v
```

### Manual Validation

```python
from data_integrity import DataIntegrityValidator
from conftest import db_connection

# Get database connection
with db_connection() as conn:
    with conn.cursor() as cursor:
        validator = DataIntegrityValidator(cursor)
        
        # Run comprehensive validation
        results = validator.run_comprehensive_validation()
        
        # Generate formatted report
        from data_integrity import format_validation_report
        report = format_validation_report(results)
        print(report)
```

## Test Scenarios

The BDD tests validate:

- **Detection of Known Issues**: Each type of corruption is properly detected
- **Comprehensive Reporting**: All validation categories are covered
- **Performance**: Validation completes within reasonable time
- **Read-Only Operations**: Database state remains unchanged during validation
- **Error Categorization**: Issues are properly categorized by severity
- **Detailed Reporting**: Specific problematic records are identified

## Expected Test Results

With the corrupted data, tests should show:

- ❌ **Overall Status**: FAIL (as expected)
- 🔍 **Errors Found**: 5+ different types of integrity issues
- ⚠️ **Warnings Generated**: 2+ types of suspicious patterns
- 📊 **Specific Issues**:
  - 1+ orphaned interval records
  - 1+ missing interval records
  - 1+ overlapping program pairs
  - 1+ duplicate program names
  - 1+ incorrect interval calculations

## Integration with Existing Tests

This data integrity testing complements the existing functional tests:

- **Functional Tests** (`test_tv_intervals.py`): Test program logic with clean data
- **Integrity Tests** (`test_data_integrity_validation.py`): Validate corrupted data detection

Both test suites run together in CI/CD to ensure:
1. Core functionality works correctly
2. Data quality issues are properly detected

## Development Workflow

1. **Make Changes**: Modify validation logic or add new corruption types
2. **Test Locally**: Run `./test_integrity_locally.sh`
3. **Commit & Push**: Changes trigger CI/CD with Neon database
4. **Review Reports**: Check Allure reports for validation results
5. **Verify Detection**: Ensure all expected issues are detected

## Benefits

- **Realistic Testing**: Tests against actual corrupted data scenarios
- **Production-Ready**: Validates data quality checks for production use
- **Comprehensive Coverage**: Tests all aspects of data integrity
- **Automated Reporting**: Generates detailed reports for stakeholders
- **CI/CD Integration**: Runs automatically on every PR