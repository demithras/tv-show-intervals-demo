Feature: Data Integrity Validation Against Pre-populated Database
  As a data quality engineer
  I want to validate the integrity of existing TV program data in the database
  So that I can identify and report data quality issues in production-like scenarios

  Background:
    Given the database contains pre-populated data with known integrity issues
    And the data integrity validator is initialized

  Scenario: Detect orphaned interval records
    When I run referential integrity validation
    Then the validation should fail
    And it should detect orphaned interval records
    And the orphaned interval "Orphaned Show" should be reported
    And the error should mention "orphaned interval records"

  Scenario: Detect missing interval records
    When I run referential integrity validation
    Then the validation should fail
    And it should detect missing interval records
    And the program "Missing Interval Show" should be reported as missing intervals
    And the error should mention "programs without interval records"

  Scenario: Detect overlapping program schedules
    When I run time constraint validation
    Then the validation should fail
    And it should detect overlapping programs
    And the overlapping programs should include "Overlap Show 1" and "Overlap Show 2"
    And the error should mention "overlapping program pairs"

  Scenario: Detect duplicate program names
    When I run data quality validation
    Then the validation should fail
    And it should detect duplicate program names
    And "Duplicate News" should be reported as a duplicate
    And the error should mention "duplicate program names"

  Scenario: Detect incorrect interval calculations
    When I run interval calculation validation
    Then the validation should fail
    And it should detect incorrect calculations
    And "Incorrect Calculation Show" should be reported with wrong calculation
    And the stored count should be 10 but calculated count should be 4

  Scenario: Detect suspicious program names
    When I run business rules validation
    Then the validation should generate warnings
    And it should detect suspicious program names
    And programs with SQL injection patterns should be flagged
    And the warning should mention "suspicious names"

  Scenario: Detect programs with zero duration
    When I run data quality validation
    Then it should detect zero duration programs
    And "Zero Duration Show" should be listed as zero duration
    And the program should have start time equal to end time

  Scenario: Detect non-standard broadcast time slots
    When I run business rules validation
    Then the validation should generate warnings
    And it should detect non-standard time slots
    And "Non-Standard Time Show" should be flagged for timing
    And the warning should mention "non-standard time slots"

  Scenario: Validate programs with excessively long names
    When I run data quality validation
    Then the validation should fail
    And it should detect programs with long names
    And programs exceeding 255 characters should be reported
    And the error should mention "names exceeding 255 characters"

  Scenario: Comprehensive integrity validation reports all issues
    When I run comprehensive validation
    Then the overall validation should fail
    And the validation report should include all categories:
      | validation_category    |
      | referential_integrity  |
      | time_constraints       |
      | interval_calculations  |
      | data_quality          |
      | business_rules        |
    And the report should show multiple errors and warnings
    And the summary should show total error count greater than 5
    And the summary should show total warning count greater than 2

  Scenario: Validation identifies specific data quality metrics
    When I run comprehensive validation
    Then the validation results should include:
      | metric_type            | expected_count |
      | orphaned_intervals     | 1              |
      | missing_intervals      | 1              |
      | overlapping_programs   | 1              |
      | duplicate_names        | 1              |
      | incorrect_calculations | 1              |
      | zero_duration_programs | 1              |
    And each metric should have detailed information about the problematic records

  Scenario: Generate formatted validation report
    When I run comprehensive validation
    And I generate a formatted validation report
    Then the report should be well-structured
    And it should include an overall status of "FAIL"
    And it should contain detailed error descriptions
    And it should list specific problematic records
    And it should provide actionable recommendations

  Scenario: Validate that some data is still good
    When I run comprehensive validation
    Then some programs should still be valid
    And valid programs should have correct interval calculations
    And valid programs should not appear in any error lists
    And the validation should distinguish between good and bad data

  Scenario: Performance validation with large corrupted dataset
    When I run comprehensive validation
    Then the validation should complete within reasonable time
    And all validation checks should execute successfully
    And the database connection should remain stable throughout
    And memory usage should remain within acceptable limits

  Scenario: Error categorization and prioritization
    When I run comprehensive validation
    Then errors should be categorized by severity
    And critical errors should be clearly identified
    And warnings should be separated from errors
    And each issue should have a clear description
    And the report should suggest remediation steps

  Scenario: Validation detects edge cases in corrupted data
    When I run business rules validation
    Then it should detect programs that appear longer than 24 hours
    And "Invalid Long Show" should be flagged as suspicious
    And the validation should handle edge cases gracefully
    And no validation should crash due to data corruption

  Scenario: Database state verification after validation
    When I run comprehensive validation
    Then the database state should remain unchanged
    And no data should be modified during validation
    And all original corruption should still exist
    And the validation should be read-only