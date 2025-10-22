Feature: Data Integrity Between Programs and Program Intervals Tables
  As a TV scheduling system administrator
  I want to ensure that all programs in the programs table have corresponding entries in the program_intervals table
  So that I can maintain data consistency and completeness across the system

# background is for demo purposes only, in real life real data would be used
# Note: Data loading is now handled by the load_data.sh script before running tests
  Background:
    Given the database is clean with test data loaded

  Scenario: All programs from the programs table should exist in the program_intervals table
    When I query both programs and program_intervals tables
    Then every program in the programs table should have a corresponding entry in the program_intervals table
    And the program count in both tables should be equal

  Scenario: Program intervals table should not contain orphaned entries
    When I query both programs and program_intervals tables
    Then every entry in the program_intervals table should have a corresponding program in the programs table
    And there should be no orphaned intervals

  Scenario: Verify no gaps in the schedule coverage
    When I analyze the schedule coverage
    Then the schedule should cover the full 24-hour period without gaps
    And the schedule should have no overlapping programs

  Scenario: Program names should not be empty or null
    When I query both programs and program_intervals tables
    Then all program names in the programs table should not be empty
    And all program names in the program_intervals table should not be empty